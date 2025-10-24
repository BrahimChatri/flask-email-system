from . import user_bp
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user_model import UserModel
from app.utils.authmanager import decrypt_user_data
from app.utils.logger import error_logger, info_logger
from app.extensions import limiter
from flask import current_app


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def get_profile():
    """
    Get current user's profile information.
    """
    try:
        current_user_id = get_jwt_identity()
        
        user_model = UserModel()
        user_data = user_model.get_user_by_id(current_user_id)
        
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
        # Decrypt sensitive data if encrypted
        encryption_key = current_app.config.get('ENCRYPTION_KEY')
        if encryption_key:
            try:
                user_data = decrypt_user_data(user_data, encryption_key)
            except Exception as e:
                error_logger.warning(f"Failed to decrypt user data: {str(e)}")
        
        # Return profile data (excluding sensitive information)
        profile_data = {
            "user_id": user_data['_id'],
            "username": user_data['username'],
            "email": user_data['email'],
            "first_name": user_data.get('first_name'),
            "last_name": user_data.get('last_name'),
            "created_at": user_data.get('created_at'),
            "last_login": user_data.get('last_login'),
            "is_verified": user_data.get('is_verified', False),
            "is_active": user_data.get('is_active', True),
            "profile": user_data.get('profile', {}),
            "storage": user_data.get('storage', {})
        }
        
        return jsonify({"profile": profile_data}), 200
        
    except Exception as e:
        error_logger.error(f"Get profile error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_profile():
    """
    Update current user's profile information.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate allowed fields
        allowed_fields = ['first_name', 'last_name', 'profile']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                if field == 'profile':
                    # Validate profile sub-fields
                    profile_data = data[field]
                    if isinstance(profile_data, dict):
                        allowed_profile_fields = ['avatar_url', 'bio', 'phone', 'timezone']
                        for profile_field in allowed_profile_fields:
                            if profile_field in profile_data:
                                update_data[f'profile.{profile_field}'] = profile_data[profile_field]
                else:
                    update_data[field] = data[field]
        
        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400
        
        # Update profile
        user_model = UserModel()
        success = user_model.update_profile(current_user_id, update_data)
        
        if success:
            info_logger.info(f"Profile updated successfully for user {current_user_id}")
            return jsonify({"message": "Profile updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update profile"}), 500
        
    except Exception as e:
        error_logger.error(f"Update profile error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/profile/avatar', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def upload_avatar():
    """
    Upload user avatar image.
    """
    try:
        current_user_id = get_jwt_identity()
        
        if 'avatar' not in request.files:
            return jsonify({"error": "No avatar file provided"}), 400
        
        file = request.files['avatar']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not file.filename.lower().endswith(tuple(f'.{ext}' for ext in allowed_extensions)):
            return jsonify({"error": "Invalid file type. Only PNG, JPG, JPEG, GIF are allowed"}), 400
        
        # Check file size (max 5MB)
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({"error": "File too large. Maximum size is 5MB"}), 400
        
        # Save file
        import os
        from werkzeug.utils import secure_filename
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        avatar_folder = os.path.join(upload_folder, 'avatars')
        os.makedirs(avatar_folder, exist_ok=True)
        
        filename = secure_filename(f"avatar_{current_user_id}_{file.filename}")
        file_path = os.path.join(avatar_folder, filename)
        
        file.save(file_path)
        
        # Update user profile with avatar URL
        avatar_url = f"/uploads/avatars/{filename}"
        user_model = UserModel()
        success = user_model.update_profile(current_user_id, {'profile.avatar_url': avatar_url})
        
        if success:
            info_logger.info(f"Avatar uploaded successfully for user {current_user_id}")
            return jsonify({
                "message": "Avatar uploaded successfully",
                "avatar_url": avatar_url
            }), 200
        else:
            return jsonify({"error": "Failed to update avatar"}), 500
        
    except Exception as e:
        error_logger.error(f"Upload avatar error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/stats', methods=['GET'])
@jwt_required()
@limiter.limit("50 per hour")
def get_user_stats():
    """
    Get user statistics including storage usage and email stats.
    """
    try:
        current_user_id = get_jwt_identity()
        
        user_model = UserModel()
        mail_model = None
        
        try:
            from app.models.mail_model import MailModel
            mail_model = MailModel()
        except ImportError:
            pass
        
        # Get user stats
        user_stats = user_model.get_user_stats(current_user_id)
        
        # Get email stats if mail model is available
        email_stats = None
        if mail_model:
            try:
                email_stats = mail_model.get_email_stats(current_user_id)
                unread_count = mail_model.get_unread_count(current_user_id)
                email_stats['unread_count'] = unread_count
            except Exception as e:
                error_logger.warning(f"Failed to get email stats: {str(e)}")
        
        return jsonify({
            "user_stats": user_stats,
            "email_stats": email_stats
        }), 200
        
    except Exception as e:
        error_logger.error(f"Get user stats error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/search', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def search_users():
    """
    Search for users by username, email, first name, or last name.
    """
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not query:
            return jsonify({"error": "Search query is required"}), 400
        
        if len(query) < 2:
            return jsonify({"error": "Search query must be at least 2 characters"}), 400
        
        user_model = UserModel()
        users = user_model.search_users(query, limit=limit)
        
        # Filter out sensitive information
        filtered_users = []
        for user in users:
            filtered_users.append({
                "user_id": user['_id'],
                "username": user['username'],
                "first_name": user.get('first_name'),
                "last_name": user.get('last_name'),
                "profile": {
                    "avatar_url": user.get('profile', {}).get('avatar_url'),
                    "bio": user.get('profile', {}).get('bio')
                }
            })
        
        return jsonify({
            "users": filtered_users,
            "query": query,
            "count": len(filtered_users)
        }), 200
        
    except Exception as e:
        error_logger.error(f"Search users error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/profile/change-password', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def change_password():
    """
    Change user password.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({"error": "Current password and new password are required"}), 400
        
        # Validate password strength
        from app.utils.authmanager import validate_password_strength
        password_validation = validate_password_strength(new_password)
        if not password_validation["is_valid"]:
            return jsonify({
                "error": "Password validation failed",
                "details": password_validation["errors"]
            }), 400
        
        # Verify current password
        user_model = UserModel()
        if not user_model.verify_password(current_user_id, current_password):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Update password
        success = user_model.update_password(current_user_id, new_password)
        
        if success:
            info_logger.info(f"Password changed successfully for user {current_user_id}")
            return jsonify({"message": "Password changed successfully"}), 200
        else:
            return jsonify({"error": "Failed to change password"}), 500
        
    except Exception as e:
        error_logger.error(f"Change password error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/profile/deactivate', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def deactivate_account():
    """
    Deactivate user account.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        password = data.get('password')
        
        if not password:
            return jsonify({"error": "Password is required to deactivate account"}), 400
        
        # Verify password
        user_model = UserModel()
        if not user_model.verify_password(current_user_id, password):
            return jsonify({"error": "Password is incorrect"}), 401
        
        # Deactivate account
        success = user_model.deactivate_user(current_user_id)
        
        if success:
            info_logger.info(f"Account deactivated for user {current_user_id}")
            return jsonify({"message": "Account deactivated successfully"}), 200
        else:
            return jsonify({"error": "Failed to deactivate account"}), 500
        
    except Exception as e:
        error_logger.error(f"Deactivate account error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
