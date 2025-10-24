from . import mail_bp
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.mail_model import MailModel
from app.models.user_model import UserModel
from app.utils.logger import error_logger, info_logger
from app.extensions import limiter
from werkzeug.utils import secure_filename
import os
import re


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@mail_bp.route('/send', methods=['POST'])
@jwt_required()
@limiter.limit("50 per hour")
def send_email():
    """
    Send a new email.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract email data
        recipients = data.get('recipients', [])
        subject = data.get('subject', '').strip()
        body = data.get('body', '').strip()
        thread_id = data.get('thread_id')
        reply_to = data.get('reply_to')
        priority = data.get('priority', 'normal')
        
        # Validate required fields
        if not recipients:
            return jsonify({"error": "At least one recipient is required"}), 400
        
        if not subject:
            return jsonify({"error": "Subject is required"}), 400
        
        if not body:
            return jsonify({"error": "Email body is required"}), 400
        
        # Validate priority
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if priority not in valid_priorities:
            return jsonify({"error": f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"}), 400
        
        # Validate recipients format
        validated_recipients = []
        user_model = UserModel()
        
        for recipient in recipients:
            if isinstance(recipient, str):
                # Check if it's a valid email
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', recipient):
                    return jsonify({"error": f"Invalid email format: {recipient}"}), 400
                
                # Try to find user by email
                user = user_model.get_user_by_email(recipient)
                validated_recipients.append({
                    "email": recipient.lower(),
                    "user_id": user['_id'] if user else None,
                    "type": "to"
                })
            elif isinstance(recipient, dict):
                email = recipient.get('email', '').strip()
                if not email:
                    return jsonify({"error": "Email is required for each recipient"}), 400
                
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                    return jsonify({"error": f"Invalid email format: {email}"}), 400
                
                user = user_model.get_user_by_email(email)
                validated_recipients.append({
                    "email": email.lower(),
                    "user_id": user['_id'] if user else None,
                    "type": recipient.get('type', 'to')
                })
        
        # Initialize mail model and send email
        mail_model = MailModel()
        
        try:
            email_id = mail_model.send_email(
                sender_id=current_user_id,
                recipients=validated_recipients,
                subject=subject,
                body=body,
                thread_id=thread_id,
                reply_to=reply_to,
                priority=priority
            )
            
            info_logger.info(f"Email sent successfully by user {current_user_id} to {len(validated_recipients)} recipients")
            
            return jsonify({
                "message": "Email sent successfully",
                "email_id": email_id
            }), 201
            
        except ValueError as e:
            error_logger.error(f"Email sending failed: {str(e)}")
            return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        error_logger.error(f"Send email error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/send-with-attachments', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def send_email_with_attachments():
    """
    Send an email with file attachments.
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get form data
        recipients = request.form.getlist('recipients[]')
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()
        thread_id = request.form.get('thread_id')
        reply_to = request.form.get('reply_to')
        priority = request.form.get('priority', 'normal')
        
        # Validate required fields
        if not recipients:
            return jsonify({"error": "At least one recipient is required"}), 400
        
        if not subject:
            return jsonify({"error": "Subject is required"}), 400
        
        if not body:
            return jsonify({"error": "Email body is required"}), 400
        
        # Validate priority
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if priority not in valid_priorities:
            return jsonify({"error": f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"}), 400
        
        # Process attachments
        attachments = []
        files = request.files.getlist('attachments')
        
        if files:
            allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
            max_file_size = 25 * 1024 * 1024  # 25MB
            
            for file in files:
                if file.filename:
                    if not allowed_file(file.filename, allowed_extensions):
                        return jsonify({"error": f"File type not allowed: {file.filename}"}), 400
                    
                    # Check file size
                    file.seek(0, 2)  # Seek to end
                    file_size = file.tell()
                    file.seek(0)  # Reset to beginning
                    
                    if file_size > max_file_size:
                        return jsonify({"error": f"File too large: {file.filename}"}), 400
                    
                    # Save file temporarily (in production, use cloud storage)
                    filename = secure_filename(file.filename)
                    file_path = os.path.join('uploads', f"{current_user_id}_{filename}")
                    
                    # Ensure upload directory exists
                    os.makedirs('uploads', exist_ok=True)
                    
                    file.save(file_path)
                    
                    attachments.append({
                        "filename": filename,
                        "content_type": file.content_type or "application/octet-stream",
                        "size": file_size,
                        "file_path": file_path,
                        "inline": False
                    })
        
        # Validate recipients format
        validated_recipients = []
        user_model = UserModel()
        
        for recipient in recipients:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', recipient):
                return jsonify({"error": f"Invalid email format: {recipient}"}), 400
            
            user = user_model.get_user_by_email(recipient)
            validated_recipients.append({
                "email": recipient.lower(),
                "user_id": user['_id'] if user else None,
                "type": "to"
            })
        
        # Initialize mail model and send email
        mail_model = MailModel()
        
        try:
            email_id = mail_model.send_email(
                sender_id=current_user_id,
                recipients=validated_recipients,
                subject=subject,
                body=body,
                attachments=attachments,
                thread_id=thread_id,
                reply_to=reply_to,
                priority=priority
            )
            
            info_logger.info(f"Email with attachments sent successfully by user {current_user_id}")
            
            return jsonify({
                "message": "Email sent successfully",
                "email_id": email_id,
                "attachments_count": len(attachments)
            }), 201
            
        except ValueError as e:
            error_logger.error(f"Email sending failed: {str(e)}")
            return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        error_logger.error(f"Send email with attachments error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/reply/<email_id>', methods=['POST'])
@jwt_required()
@limiter.limit("50 per hour")
def reply_to_email(email_id):
    """
    Reply to an existing email.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        body = data.get('body', '').strip()
        
        if not body:
            return jsonify({"error": "Reply body is required"}), 400
        
        # Get the original email
        mail_model = MailModel()
        original_email = mail_model.get_email_by_id(email_id)
        
        if not original_email:
            return jsonify({"error": "Original email not found"}), 404
        
        # Check if user is a recipient of the original email
        user_is_recipient = False
        for recipient in original_email.get('recipients', []):
            if recipient.get('user_id') == current_user_id:
                user_is_recipient = True
                break
        
        if not user_is_recipient and str(original_email.get('sender_id')) != current_user_id:
            return jsonify({"error": "You can only reply to emails you received or sent"}), 403
        
        # Prepare reply recipients
        reply_recipients = []
        user_model = UserModel()
        
        # If user is recipient, reply to sender
        if user_is_recipient:
            sender_email = original_email.get('sender_email')
            if sender_email:
                user = user_model.get_user_by_email(sender_email)
                reply_recipients.append({
                    "email": sender_email.lower(),
                    "user_id": user['_id'] if user else None,
                    "type": "to"
                })
        
        # If user is sender, reply to all recipients
        else:
            for recipient in original_email.get('recipients', []):
                if recipient.get('email'):
                    user = user_model.get_user_by_email(recipient['email'])
                    reply_recipients.append({
                        "email": recipient['email'].lower(),
                        "user_id": user['_id'] if user else None,
                        "type": recipient.get('type', 'to')
                    })
        
        # Create reply subject
        subject = original_email.get('subject', '')
        if not subject.startswith('Re:'):
            subject = f"Re: {subject}"
        
        # Send reply
        try:
            reply_email_id = mail_model.send_email(
                sender_id=current_user_id,
                recipients=reply_recipients,
                subject=subject,
                body=body,
                thread_id=original_email.get('thread_id'),
                reply_to=email_id,
                priority=original_email.get('priority', 'normal')
            )
            
            info_logger.info(f"Reply sent successfully by user {current_user_id} to email {email_id}")
            
            return jsonify({
                "message": "Reply sent successfully",
                "email_id": reply_email_id
            }), 201
            
        except ValueError as e:
            error_logger.error(f"Reply sending failed: {str(e)}")
            return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        error_logger.error(f"Reply to email error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/forward/<email_id>', methods=['POST'])
@jwt_required()
@limiter.limit("50 per hour")
def forward_email(email_id):
    """
    Forward an email to new recipients.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        recipients = data.get('recipients', [])
        additional_message = data.get('additional_message', '').strip()
        
        if not recipients:
            return jsonify({"error": "At least one recipient is required"}), 400
        
        # Get the original email
        mail_model = MailModel()
        original_email = mail_model.get_email_by_id(email_id)
        
        if not original_email:
            return jsonify({"error": "Original email not found"}), 404
        
        # Check if user is a recipient of the original email
        user_is_recipient = False
        for recipient in original_email.get('recipients', []):
            if recipient.get('user_id') == current_user_id:
                user_is_recipient = True
                break
        
        if not user_is_recipient and str(original_email.get('sender_id')) != current_user_id:
            return jsonify({"error": "You can only forward emails you received or sent"}), 403
        
        # Validate new recipients
        validated_recipients = []
        user_model = UserModel()
        
        for recipient in recipients:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', recipient):
                return jsonify({"error": f"Invalid email format: {recipient}"}), 400
            
            user = user_model.get_user_by_email(recipient)
            validated_recipients.append({
                "email": recipient.lower(),
                "user_id": user['_id'] if user else None,
                "type": "to"
            })
        
        # Create forward subject
        subject = original_email.get('subject', '')
        if not subject.startswith('Fwd:'):
            subject = f"Fwd: {subject}"
        
        # Create forward body
        original_body = original_email.get('body', '')
        forward_body = f"---------- Forwarded message ----------\n"
        forward_body += f"From: {original_email.get('sender_email', 'Unknown')}\n"
        forward_body += f"Date: {original_email.get('created_at', 'Unknown')}\n"
        forward_body += f"Subject: {original_email.get('subject', 'No subject')}\n\n"
        forward_body += original_body
        
        if additional_message:
            forward_body = f"{additional_message}\n\n{forward_body}"
        
        # Send forwarded email
        try:
            forward_email_id = mail_model.send_email(
                sender_id=current_user_id,
                recipients=validated_recipients,
                subject=subject,
                body=forward_body,
                attachments=original_email.get('attachments', []),
                priority=original_email.get('priority', 'normal')
            )
            
            info_logger.info(f"Email forwarded successfully by user {current_user_id}")
            
            return jsonify({
                "message": "Email forwarded successfully",
                "email_id": forward_email_id
            }), 201
            
        except ValueError as e:
            error_logger.error(f"Forward email failed: {str(e)}")
            return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        error_logger.error(f"Forward email error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
