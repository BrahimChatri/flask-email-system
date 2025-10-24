from . import user_bp
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user_model import UserModel
from app.utils.logger import error_logger, info_logger
from app.extensions import limiter


@user_bp.route('/settings', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def get_settings():
    """
    Get current user's settings.
    """
    try:
        current_user_id = get_jwt_identity()
        
        user_model = UserModel()
        user_data = user_model.get_user_by_id(current_user_id)
        
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
        settings = user_data.get('settings', {})
        
        return jsonify({"settings": settings}), 200
        
    except Exception as e:
        error_logger.error(f"Get settings error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/settings', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_settings():
    """
    Update current user's settings.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate settings structure
        valid_settings = {
            'notifications': {
                'email_notifications': bool,
                'desktop_notifications': bool,
                'sound_alerts': bool
            },
            'privacy': {
                'show_online_status': bool,
                'allow_read_receipts': bool
            },
            'theme': str
        }
        
        # Validate and clean settings data
        cleaned_settings = {}
        
        for category, fields in valid_settings.items():
            if category in data:
                if isinstance(data[category], dict):
                    cleaned_category = {}
                    for field, field_type in fields.items():
                        if field in data[category]:
                            if field_type == bool:
                                cleaned_category[field] = bool(data[category][field])
                            elif field_type == str:
                                cleaned_category[field] = str(data[category][field])
                    cleaned_settings[category] = cleaned_category
        
        if not cleaned_settings:
            return jsonify({"error": "No valid settings to update"}), 400
        
        # Update settings
        user_model = UserModel()
        success = user_model.update_settings(current_user_id, cleaned_settings)
        
        if success:
            info_logger.info(f"Settings updated successfully for user {current_user_id}")
            return jsonify({"message": "Settings updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update settings"}), 500
        
    except Exception as e:
        error_logger.error(f"Update settings error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/settings/notifications', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_notification_settings():
    """
    Update notification settings specifically.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate notification settings
        valid_notification_fields = ['email_notifications', 'desktop_notifications', 'sound_alerts']
        notification_settings = {}
        
        for field in valid_notification_fields:
            if field in data:
                notification_settings[field] = bool(data[field])
        
        if not notification_settings:
            return jsonify({"error": "No valid notification settings to update"}), 400
        
        # Get current settings and update notifications
        user_model = UserModel()
        user_data = user_model.get_user_by_id(current_user_id)
        
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
        current_settings = user_data.get('settings', {})
        current_notifications = current_settings.get('notifications', {})
        current_notifications.update(notification_settings)
        
        updated_settings = current_settings.copy()
        updated_settings['notifications'] = current_notifications
        
        success = user_model.update_settings(current_user_id, updated_settings)
        
        if success:
            info_logger.info(f"Notification settings updated for user {current_user_id}")
            return jsonify({"message": "Notification settings updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update notification settings"}), 500
        
    except Exception as e:
        error_logger.error(f"Update notification settings error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/settings/privacy', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_privacy_settings():
    """
    Update privacy settings specifically.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate privacy settings
        valid_privacy_fields = ['show_online_status', 'allow_read_receipts']
        privacy_settings = {}
        
        for field in valid_privacy_fields:
            if field in data:
                privacy_settings[field] = bool(data[field])
        
        if not privacy_settings:
            return jsonify({"error": "No valid privacy settings to update"}), 400
        
        # Get current settings and update privacy
        user_model = UserModel()
        user_data = user_model.get_user_by_id(current_user_id)
        
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
        current_settings = user_data.get('settings', {})
        current_privacy = current_settings.get('privacy', {})
        current_privacy.update(privacy_settings)
        
        updated_settings = current_settings.copy()
        updated_settings['privacy'] = current_privacy
        
        success = user_model.update_settings(current_user_id, updated_settings)
        
        if success:
            info_logger.info(f"Privacy settings updated for user {current_user_id}")
            return jsonify({"message": "Privacy settings updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update privacy settings"}), 500
        
    except Exception as e:
        error_logger.error(f"Update privacy settings error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/settings/theme', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_theme():
    """
    Update user theme preference.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        theme = data.get('theme')
        
        if not theme:
            return jsonify({"error": "Theme is required"}), 400
        
        # Validate theme
        valid_themes = ['light', 'dark', 'auto']
        if theme not in valid_themes:
            return jsonify({"error": f"Invalid theme. Must be one of: {', '.join(valid_themes)}"}), 400
        
        # Get current settings and update theme
        user_model = UserModel()
        user_data = user_model.get_user_by_id(current_user_id)
        
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
        current_settings = user_data.get('settings', {})
        current_settings['theme'] = theme
        
        success = user_model.update_settings(current_user_id, current_settings)
        
        if success:
            info_logger.info(f"Theme updated to '{theme}' for user {current_user_id}")
            return jsonify({"message": "Theme updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update theme"}), 500
        
    except Exception as e:
        error_logger.error(f"Update theme error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/settings/reset', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def reset_settings():
    """
    Reset user settings to default values.
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Default settings
        default_settings = {
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
        }
        
        # Update settings
        user_model = UserModel()
        success = user_model.update_settings(current_user_id, default_settings)
        
        if success:
            info_logger.info(f"Settings reset to default for user {current_user_id}")
            return jsonify({
                "message": "Settings reset to default successfully",
                "settings": default_settings
            }), 200
        else:
            return jsonify({"error": "Failed to reset settings"}), 500
        
    except Exception as e:
        error_logger.error(f"Reset settings error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/settings/export', methods=['GET'])
@jwt_required()
@limiter.limit("10 per hour")
def export_settings():
    """
    Export user settings as JSON.
    """
    try:
        current_user_id = get_jwt_identity()
        
        user_model = UserModel()
        user_data = user_model.get_user_by_id(current_user_id)
        
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
        settings = user_data.get('settings', {})
        
        # Add metadata
        export_data = {
            "exported_at": user_data.get('updated_at'),
            "user_id": current_user_id,
            "settings": settings
        }
        
        return jsonify(export_data), 200
        
    except Exception as e:
        error_logger.error(f"Export settings error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route('/settings/import', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def import_settings():
    """
    Import user settings from JSON.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        settings = data.get('settings')
        
        if not settings or not isinstance(settings, dict):
            return jsonify({"error": "Invalid settings format"}), 400
        
        # Validate settings structure
        valid_settings = {
            'notifications': {
                'email_notifications': bool,
                'desktop_notifications': bool,
                'sound_alerts': bool
            },
            'privacy': {
                'show_online_status': bool,
                'allow_read_receipts': bool
            },
            'theme': str
        }
        
        # Validate and clean settings
        cleaned_settings = {}
        
        for category, fields in valid_settings.items():
            if category in settings:
                if isinstance(settings[category], dict):
                    cleaned_category = {}
                    for field, field_type in fields.items():
                        if field in settings[category]:
                            if field_type == bool:
                                cleaned_category[field] = bool(settings[category][field])
                            elif field_type == str:
                                cleaned_category[field] = str(settings[category][field])
                    cleaned_settings[category] = cleaned_category
        
        if not cleaned_settings:
            return jsonify({"error": "No valid settings to import"}), 400
        
        # Update settings
        user_model = UserModel()
        success = user_model.update_settings(current_user_id, cleaned_settings)
        
        if success:
            info_logger.info(f"Settings imported successfully for user {current_user_id}")
            return jsonify({"message": "Settings imported successfully"}), 200
        else:
            return jsonify({"error": "Failed to import settings"}), 500
        
    except Exception as e:
        error_logger.error(f"Import settings error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
