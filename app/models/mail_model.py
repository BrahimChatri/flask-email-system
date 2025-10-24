"""
MailModel: Handles email data and operations for the Flask Gmail System.

This file defines the MailModel class, which interacts with a MongoDB database to manage emails, inboxes, and related actions.

Dependencies:
- MongoDB (pymongo)
- Flask (for current_app)
- bson (for ObjectId)

Make sure MongoDB is running and the required Python packages are installed.
"""
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
from flask import current_app
import re


class MailModel:
    """
    MailModel provides methods to send, retrieve, search, and manage emails and inbox entries in MongoDB.
    """
    def __init__(self, db=None):
        """
        Initialize the MailModel.
        If no db is provided, connect using Flask's current_app config.
        """
        if db is None:
            client = MongoClient(current_app.config['MONGODB_URI'])
            self.db = client[current_app.config['DATABASE_NAME']]
        else:
            self.db = db
        self.collection = self.db.emails
        
        # Create indexes for better performance and search speed
        self.collection.create_index([("sender_id", 1), ("created_at", -1)])
        self.collection.create_index([("recipients.user_id", 1), ("created_at", -1)])
        self.collection.create_index("thread_id")
        self.collection.create_index("subject")
        self.collection.create_index("created_at")
    
    def send_email(self, sender_id, recipients, subject, body, attachments=None, 
                   thread_id=None, reply_to=None, priority="normal"):
        """
        Send a new email from sender_id to recipients.
        Recipients can be a list of emails or dicts with more info.
        Returns the new email's ID as a string.
        """
        if not recipients:
            raise ValueError("At least one recipient is required")
        
        # Validate recipients format
        validated_recipients = []
        for recipient in recipients:
            if isinstance(recipient, str):
                # If it's just an email string, convert to dict
                validated_recipients.append({
                    "email": recipient.lower(),
                    "user_id": None,  # Will be resolved later
                    "type": "to"
                })
            elif isinstance(recipient, dict):
                validated_recipients.append({
                    "email": recipient.get("email", "").lower(),
                    "user_id": recipient.get("user_id"),
                    "type": recipient.get("type", "to")  # to, cc, bcc
                })
        
        # Process attachments and calculate total size
        processed_attachments = []
        total_size = 0
        if attachments:
            for attachment in attachments:
                file_size = attachment.get("size", 0)
                total_size += file_size
                processed_attachments.append({
                    "filename": attachment["filename"],
                    "content_type": attachment.get("content_type", "application/octet-stream"),
                    "size": file_size,
                    "file_id": attachment.get("file_id"),  # GridFS file ID
                    "inline": attachment.get("inline", False)
                })
        
        email_data = {
            "sender_id": ObjectId(sender_id),
            "recipients": validated_recipients,
            "subject": subject,
            "body": body,
            "attachments": processed_attachments,
            "thread_id": thread_id or str(ObjectId()),
            "reply_to": reply_to,
            "priority": priority,
            "created_at": datetime.utcnow(),
            "size": len(body.encode('utf-8')) + total_size,
            "status": "sent",
            "flags": {
                "read": False,
                "starred": False,
                "important": False,
                "deleted": False,
                "archived": False
            },
            "delivery_status": {
                "delivered": True,
                "delivery_time": datetime.utcnow(),
                "bounce_count": 0,
                "last_bounce": None
            }
        }
        
        result = self.collection.insert_one(email_data)
        
        # Create inbox entries for each recipient
        self._create_inbox_entries(str(result.inserted_id), validated_recipients)
        
        return str(result.inserted_id)
    
    def _create_inbox_entries(self, email_id, recipients):
        """
        Create inbox entries for each recipient so they see the email in their inbox.
        """
        inbox_collection = self.db.inbox
        
        for recipient in recipients:
            if recipient.get("user_id"):
                inbox_entry = {
                    "user_id": ObjectId(recipient["user_id"]),
                    "email_id": ObjectId(email_id),
                    "recipient_type": recipient["type"],
                    "received_at": datetime.utcnow(),
                    "flags": {
                        "read": False,
                        "starred": False,
                        "important": False,
                        "deleted": False,
                        "archived": False
                    },
                    "folder": "inbox"
                }
                inbox_collection.insert_one(inbox_entry)
    
    def get_email_by_id(self, email_id):
        """
        Get an email by its unique ID.
        Returns an email dict or None if not found.
        """
        try:
            email = self.collection.find_one({"_id": ObjectId(email_id)})
            if email:
                email['_id'] = str(email['_id'])
                email['sender_id'] = str(email['sender_id'])
            return email
        except:
            return None
    
    def get_user_inbox(self, user_id, page=1, limit=20, folder="inbox"):
        """
        Get a user's inbox emails with pagination.
        Returns a list of email dicts for the specified folder (default: inbox).
        """
        skip = (page - 1) * limit
        
        # Get inbox entries for the user
        inbox_collection = self.db.inbox
        inbox_entries = list(inbox_collection.find({
            "user_id": ObjectId(user_id),
            "folder": folder,
            "flags.deleted": False
        }).sort("received_at", -1).skip(skip).limit(limit))
        
        # Get corresponding emails
        email_ids = [entry["email_id"] for entry in inbox_entries]
        emails = list(self.collection.find({"_id": {"$in": email_ids}}))
        
        # Combine inbox data with email data
        result = []
        for inbox_entry in inbox_entries:
            email = next((e for e in emails if e["_id"] == inbox_entry["email_id"]), None)
            if email:
                email['_id'] = str(email['_id'])
                email['sender_id'] = str(email['sender_id'])
                email['inbox_flags'] = inbox_entry['flags']  # Add inbox-specific flags
                email['received_at'] = inbox_entry['received_at']
                email['recipient_type'] = inbox_entry['recipient_type']
                result.append(email)
        
        return result
    
    def get_sent_emails(self, user_id, page=1, limit=20):
        """
        Get emails sent by a user, with pagination.
        Returns a list of sent email dicts.
        """
        skip = (page - 1) * limit
        
        emails = list(self.collection.find({
            "sender_id": ObjectId(user_id)
        }).sort("created_at", -1).skip(skip).limit(limit))
        
        for email in emails:
            email['_id'] = str(email['_id'])
            email['sender_id'] = str(email['sender_id'])
        
        return emails
    
    def get_thread_emails(self, thread_id):
        """
        Get all emails in a conversation thread.
        Returns a list of email dicts.
        """
        emails = list(self.collection.find({
            "thread_id": thread_id
        }).sort("created_at", 1))
        
        for email in emails:
            email['_id'] = str(email['_id'])
            email['sender_id'] = str(email['sender_id'])
        
        return emails
    
    def mark_as_read(self, email_id, user_id):
        """
        Mark an email as read for a specific user.
        Returns True if updated.
        """
        inbox_collection = self.db.inbox
        result = inbox_collection.update_one(
            {
                "email_id": ObjectId(email_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": {"flags.read": True}}
        )
        return result.modified_count > 0
    
    def mark_as_starred(self, email_id, user_id, starred=True):
        """
        Mark or unmark an email as starred for a user.
        Returns True if updated.
        """
        inbox_collection = self.db.inbox
        result = inbox_collection.update_one(
            {
                "email_id": ObjectId(email_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": {"flags.starred": starred}}
        )
        return result.modified_count > 0
    
    def mark_as_important(self, email_id, user_id, important=True):
        """
        Mark or unmark an email as important for a user.
        Returns True if updated.
        """
        inbox_collection = self.db.inbox
        result = inbox_collection.update_one(
            {
                "email_id": ObjectId(email_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": {"flags.important": important}}
        )
        return result.modified_count > 0
    
    def move_to_folder(self, email_id, user_id, folder):
        """
        Move an email to a specific folder (e.g., inbox, archive, trash).
        Returns True if updated.
        """
        inbox_collection = self.db.inbox
        result = inbox_collection.update_one(
            {
                "email_id": ObjectId(email_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": {"folder": folder}}
        )
        return result.modified_count > 0
    
    def delete_email(self, email_id, user_id, permanent=False):
        """
        Delete an email for a user. If permanent is True, remove from inbox; otherwise, move to trash.
        Returns True if deleted or updated.
        """
        inbox_collection = self.db.inbox
        
        if permanent:
            # Permanently delete from inbox
            result = inbox_collection.delete_one({
                "email_id": ObjectId(email_id),
                "user_id": ObjectId(user_id)
            })
            return result.deleted_count > 0
        else:
            # Mark as deleted
            result = inbox_collection.update_one(
                {
                    "email_id": ObjectId(email_id),
                    "user_id": ObjectId(user_id)
                },
                {
                    "$set": {
                        "flags.deleted": True,
                        "folder": "trash"
                    }
                }
            )
            return result.modified_count > 0
    
    def search_emails(self, user_id, query, page=1, limit=20):
        """
        Search a user's emails by subject, body, or recipient email.
        Returns a list of matching email dicts.
        """
        skip = (page - 1) * limit
        
        # First, get user's inbox entries
        inbox_collection = self.db.inbox
        inbox_entries = list(inbox_collection.find({
            "user_id": ObjectId(user_id),
            "flags.deleted": False
        }))
        
        email_ids = [entry["email_id"] for entry in inbox_entries]
        
        # Search in emails
        search_filter = {
            "_id": {"$in": email_ids},
            "$or": [
                {"subject": {"$regex": query, "$options": "i"}},
                {"body": {"$regex": query, "$options": "i"}},
                {"recipients.email": {"$regex": query, "$options": "i"}}
            ]
        }
        
        emails = list(self.collection.find(search_filter)
                     .sort("created_at", -1)
                     .skip(skip)
                     .limit(limit))
        
        for email in emails:
            email['_id'] = str(email['_id'])
            email['sender_id'] = str(email['sender_id'])
        
        return emails
    
    def get_email_stats(self, user_id):
        """
        Get statistics about a user's emails (e.g., counts by folder, unread, starred, sent).
        Returns a dict with stats.
        """
        inbox_collection = self.db.inbox
        
        # Count emails by folder
        pipeline = [
            {"$match": {"user_id": ObjectId(user_id)}},
            {"$group": {
                "_id": "$folder",
                "count": {"$sum": 1},
                "unread": {"$sum": {"$cond": [{"$eq": ["$flags.read", False]}, 1, 0]}},
                "starred": {"$sum": {"$cond": [{"$eq": ["$flags.starred", True]}, 1, 0]}}
            }}
        ]
        
        folder_stats = list(inbox_collection.aggregate(pipeline))
        
        # Count sent emails
        sent_count = self.collection.count_documents({"sender_id": ObjectId(user_id)})
        
        return {
            "folder_stats": folder_stats,
            "sent_count": sent_count
        }
    
    def get_unread_count(self, user_id):
        """
        Get the number of unread emails for a user.
        Returns an integer count.
        """
        inbox_collection = self.db.inbox
        return inbox_collection.count_documents({
            "user_id": ObjectId(user_id),
            "flags.read": False,
            "flags.deleted": False
        })
    
    def archive_email(self, email_id, user_id):
        """
        Archive an email (move to archive folder).
        Returns True if updated.
        """
        return self.move_to_folder(email_id, user_id, "archive")
    
    def restore_email(self, email_id, user_id):
        """
        Restore an email from trash back to the inbox.
        Returns True if updated.
        """
        inbox_collection = self.db.inbox
        result = inbox_collection.update_one(
            {
                "email_id": ObjectId(email_id),
                "user_id": ObjectId(user_id)
            },
            {
                "$set": {
                    "flags.deleted": False,
                    "folder": "inbox"
                }
            }
        )
        return result.modified_count > 0
    
    def get_attachment(self, email_id, attachment_filename):
        """
        Get metadata for a specific attachment in an email.
        Returns an attachment dict or None if not found.
        """
        email = self.get_email_by_id(email_id)
        if not email:
            return None
        
        for attachment in email.get('attachments', []):
            if attachment['filename'] == attachment_filename:
                return attachment
        
        return None