"""
UserModel: Handles user data and operations for the Flask Gmail System.

This file defines the UserModel class, which interacts with a MongoDB database to manage user accounts.

Dependencies:
- MongoDB (pymongo)
- Flask (for current_app)
- bson (for ObjectId)
- utils.authmanager (for password hashing)

Make sure MongoDB is running and the required Python packages are installed.
"""
from datetime import datetime
from app.utils.authmanager import hash_pass, compare_pass
from bson import ObjectId
from pymongo import MongoClient
from flask import current_app
import re


class UserModel:
    """
    UserModel provides methods to create, retrieve, update, and delete user accounts in MongoDB.
    """
    def __init__(self, db=None):
        """
        Initialize the UserModel.
        If no db is provided, connect using Flask's current_app config.
        """
        if db is None:
            try:
                client = MongoClient(current_app.config['MONGODB_URI'])
                self.db = client[current_app.config['DATABASE_NAME']]
            except Exception as e:
                raise ValueError(f"Failed to connect to MongoDB: {str(e)}")
        else:
            self.db = db
        self.collection = self.db.users
        
        # Create indexes for better performance and uniqueness
        try:
            self.collection.create_index("email", unique=True)
            self.collection.create_index("username", unique=True)
            self.collection.create_index("created_at")
        except Exception as e:
            # Index creation might fail if they already exist, which is fine
            pass
    
    def create_user(self, email: str, username: str, password_hash: str, first_name: str = None, last_name: str = None):
        """
        Create a new user account.
        Returns the new user's ID as a string.
        Raises ValueError if email or username is invalid or already exists.
        """
        # Validate email format
        if not self._is_valid_email(email):
            raise ValueError("Invalid email format")
        
        # Check if user already exists
        if self.get_user_by_email(email):
            raise ValueError("User with this email already exists")
        
        if self.get_user_by_username(username):
            raise ValueError("Username already taken")
        
        # Validate username
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        # Validate password hash
        if not password_hash:
            raise ValueError("Password hash is required")
                
        user_data = {
            "email": email.lower(),
            "username": username,
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "is_verified": False,
            "last_login": None,
            "profile": {
                "avatar_url": None,
                "bio": None,
                "phone": None,
                "timezone": "UTC"
            },
            "settings": {
                "notifications": {
                    "email_notifications": True,
                    "desktop_notifications": True,
                    "sound_alerts": True
                },
                "privacy": {
                    "show_online_status": True,
                    "allow_read_receipts": True
                },
                "theme": "light"
            },
            "storage": {
                "used_space": 0,  # in bytes
                "max_space": 1073741824,  # 1GB in bytes
                "attachment_limit": 26214400  # 25MB in bytes
            }
        }
        
        try:
            result = self.collection.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            raise ValueError(f"Failed to create user: {str(e)}")
    
    def get_user_by_id(self, user_id):
        """
        Get a user by their unique ObjectId.
        Returns a user dict or None if not found.
        """
        try:
            if not user_id:
                return None
            user = self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except Exception:
            return None
    
    def get_user_by_email(self, email: str):
        """
        Get a user by their email address.
        Returns a user dict or None if not found.
        """
        try:
            if not email:
                return None
            user = self.collection.find_one({"email": email.lower()})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except Exception:
            return None
    
    def get_user_by_username(self, username: str):
        """
        Get a user by their username.
        Returns a user dict or None if not found.
        """
        try:
            if not username:
                return None
            user = self.collection.find_one({"username": username})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except Exception:
            return None
    
    def verify_password(self, user_id, password):
        """
        Check if the provided password matches the user's stored password hash.
        Returns True if correct, False otherwise.
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        return compare_pass(password, user['password_hash'])
    
    def update_password(self, user_id, new_password):
        """
        Update the user's password to a new value.
        Returns True if the password was updated.
        """
        try:
            password_hash = hash_pass(new_password)
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_hash": password_hash,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def update_last_login(self, user_id):
        """
        Update the user's last login time to now.
        Returns True if updated.
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def update_profile(self, user_id, profile_data):
        """
        Update user profile information (e.g., name, avatar, bio).
        Only allows certain fields to be updated.
        Returns True if updated.
        """
        allowed_fields = ['first_name', 'last_name', 'profile.avatar_url', 
                         'profile.bio', 'profile.phone', 'profile.timezone']
        
        update_data = {}
        for field, value in profile_data.items():
            if field in allowed_fields:
                update_data[field] = value
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            try:
                result = self.collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": update_data}
                )
                return result.modified_count > 0
            except Exception:
                return False
        return False
    
    def update_settings(self, user_id, settings_data):
        """
        Update user settings (e.g., notifications, privacy, theme).
        Returns True if updated.
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "settings": settings_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def update_storage_usage(self, user_id, used_space):
        """
        Update the amount of storage space used by the user.
        Returns True if updated.
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "storage.used_space": used_space,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def deactivate_user(self, user_id):
        """
        Deactivate a user account (set is_active to False).
        Returns True if updated.
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def verify_user_email(self, user_id):
        """
        Mark a user's email as verified.
        Returns True if updated.
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_verified": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def search_users(self, query, limit=10):
        """
        Search for users by email, username, first name, or last name.
        Returns a list of user dicts (excluding password hashes).
        """
        try:
            search_filter = {
                "$or": [
                    {"email": {"$regex": query, "$options": "i"}},
                    {"username": {"$regex": query, "$options": "i"}},
                    {"first_name": {"$regex": query, "$options": "i"}},
                    {"last_name": {"$regex": query, "$options": "i"}}
                ],
                "is_active": True
            }
            
            users = list(self.collection.find(
                search_filter,
                {"password_hash": 0}  # Exclude password hash from results
            ).limit(limit))
            
            for user in users:
                user['_id'] = str(user['_id'])
            
            return users
        except Exception:
            return []
    
    def get_user_stats(self, user_id):
        """
        Get basic statistics for a user (e.g., storage used, verification status).
        Returns a dict or None if user not found.
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # This would typically aggregate data from the mail collection
        # For now, return basic user info
        return {
            "user_id": user_id,
            "email": user['email'],
            "created_at": user['created_at'],
            "last_login": user['last_login'],
            "storage_used": user['storage']['used_space'],
            "storage_limit": user['storage']['max_space'],
            "is_verified": user['is_verified']
        }
    
    def delete_user(self, user_id):
        """
        Delete a user account from the database.
        Use with caution! Returns True if deleted.
        """
        try:
            result = self.collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    def _is_valid_email(self, email):
        """
        Check if the email address is in a valid format.
        Returns True if valid, False otherwise.
        """
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_all_users(self, limit=100):
        """
        Get a list of all users (up to the specified limit).
        Returns a list of user dicts (excluding password hashes).
        """
        try:
            users = list(self.collection.find({}, {"password_hash": 0}).limit(limit))
            for user in users:
                user['_id'] = str(user['_id'])
            return users
        except Exception:
            return []