from . import mail_bp
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.mail_model import MailModel
from app.utils.logger import error_logger, info_logger
from app.extensions import limiter


@mail_bp.route('/inbox', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def get_inbox():
    """
    Get user's inbox emails with pagination.
    """
    try:
        current_user_id = get_jwt_identity()
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100 emails per request
        folder = request.args.get('folder', 'inbox')
        
        mail_model = MailModel()
        emails = mail_model.get_user_inbox(current_user_id, page=page, limit=limit, folder=folder)
        
        return jsonify({
            "emails": emails,
            "page": page,
            "limit": limit,
            "folder": folder
        }), 200
        
    except Exception as e:
        error_logger.error(f"Get inbox error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/sent', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def get_sent_emails():
    """
    Get user's sent emails with pagination.
    """
    try:
        current_user_id = get_jwt_identity()
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)
        
        mail_model = MailModel()
        emails = mail_model.get_sent_emails(current_user_id, page=page, limit=limit)
        
        return jsonify({
            "emails": emails,
            "page": page,
            "limit": limit
        }), 200
        
    except Exception as e:
        error_logger.error(f"Get sent emails error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/email/<email_id>', methods=['GET'])
@jwt_required()
@limiter.limit("200 per hour")
def get_email(email_id):
    """
    Get a specific email by ID.
    """
    try:
        current_user_id = get_jwt_identity()
        
        mail_model = MailModel()
        email = mail_model.get_email_by_id(email_id)
        
        if not email:
            return jsonify({"error": "Email not found"}), 404
        
        # Mark as read if user is recipient
        if str(email.get('sender_id')) != current_user_id:
            mail_model.mark_as_read(email_id, current_user_id)
        
        return jsonify({"email": email}), 200
        
    except Exception as e:
        error_logger.error(f"Get email error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/email/<email_id>/read', methods=['POST'])
@jwt_required()
@limiter.limit("200 per hour")
def mark_as_read(email_id):
    """
    Mark an email as read.
    """
    try:
        current_user_id = get_jwt_identity()
        
        mail_model = MailModel()
        success = mail_model.mark_as_read(email_id, current_user_id)
        
        if success:
            return jsonify({"message": "Email marked as read"}), 200
        else:
            return jsonify({"error": "Email not found or already read"}), 404
            
    except Exception as e:
        error_logger.error(f"Mark as read error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/email/<email_id>/star', methods=['POST'])
@jwt_required()
@limiter.limit("200 per hour")
def toggle_star(email_id):
    """
    Toggle star status of an email.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}
        starred = data.get('starred', True)
        
        mail_model = MailModel()
        success = mail_model.mark_as_starred(email_id, current_user_id, starred=starred)
        
        if success:
            action = "starred" if starred else "unstarred"
            return jsonify({"message": f"Email {action}"}), 200
        else:
            return jsonify({"error": "Email not found"}), 404
            
    except Exception as e:
        error_logger.error(f"Toggle star error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/email/<email_id>/important', methods=['POST'])
@jwt_required()
@limiter.limit("200 per hour")
def toggle_important(email_id):
    """
    Toggle important status of an email.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}
        important = data.get('important', True)
        
        mail_model = MailModel()
        success = mail_model.mark_as_important(email_id, current_user_id, important=important)
        
        if success:
            action = "marked as important" if important else "unmarked as important"
            return jsonify({"message": f"Email {action}"}), 200
        else:
            return jsonify({"error": "Email not found"}), 404
            
    except Exception as e:
        error_logger.error(f"Toggle important error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/email/<email_id>/move', methods=['POST'])
@jwt_required()
@limiter.limit("100 per hour")
def move_email(email_id):
    """
    Move an email to a different folder.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'folder' not in data:
            return jsonify({"error": "Folder is required"}), 400
        
        folder = data['folder']
        valid_folders = ['inbox', 'archive', 'trash', 'spam']
        
        if folder not in valid_folders:
            return jsonify({"error": f"Invalid folder. Must be one of: {', '.join(valid_folders)}"}), 400
        
        mail_model = MailModel()
        success = mail_model.move_to_folder(email_id, current_user_id, folder)
        
        if success:
            return jsonify({"message": f"Email moved to {folder}"}), 200
        else:
            return jsonify({"error": "Email not found"}), 404
            
    except Exception as e:
        error_logger.error(f"Move email error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/email/<email_id>/delete', methods=['DELETE'])
@jwt_required()
@limiter.limit("50 per hour")
def delete_email(email_id):
    """
    Delete an email (move to trash or permanent delete).
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}
        permanent = data.get('permanent', False)
        
        mail_model = MailModel()
        success = mail_model.delete_email(email_id, current_user_id, permanent=permanent)
        
        if success:
            action = "permanently deleted" if permanent else "moved to trash"
            return jsonify({"message": f"Email {action}"}), 200
        else:
            return jsonify({"error": "Email not found"}), 404
            
    except Exception as e:
        error_logger.error(f"Delete email error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/search', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def search_emails():
    """
    Search user's emails by subject, body, or recipient.
    """
    try:
        current_user_id = get_jwt_identity()
        query = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)
        
        if not query:
            return jsonify({"error": "Search query is required"}), 400
        
        mail_model = MailModel()
        emails = mail_model.search_emails(current_user_id, query, page=page, limit=limit)
        
        return jsonify({
            "emails": emails,
            "query": query,
            "page": page,
            "limit": limit
        }), 200
        
    except Exception as e:
        error_logger.error(f"Search emails error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/stats', methods=['GET'])
@jwt_required()
@limiter.limit("50 per hour")
def get_email_stats():
    """
    Get email statistics for the current user.
    """
    try:
        current_user_id = get_jwt_identity()
        
        mail_model = MailModel()
        stats = mail_model.get_email_stats(current_user_id)
        unread_count = mail_model.get_unread_count(current_user_id)
        
        return jsonify({
            "stats": stats,
            "unread_count": unread_count
        }), 200
        
    except Exception as e:
        error_logger.error(f"Get email stats error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@mail_bp.route('/thread/<thread_id>', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def get_thread_emails(thread_id):
    """
    Get all emails in a conversation thread.
    """
    try:
        mail_model = MailModel()
        emails = mail_model.get_thread_emails(thread_id)
        
        return jsonify({
            "thread_id": thread_id,
            "emails": emails
        }), 200
        
    except Exception as e:
        error_logger.error(f"Get thread emails error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
