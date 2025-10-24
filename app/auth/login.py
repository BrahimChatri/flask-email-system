from . import auth_bp
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.models.user_model import UserModel
from app.utils.authmanager import compare_pass
from app.utils.logger import error_logger, info_logger
from app.extensions import limiter
from flask import current_app
from datetime import datetime


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    User login endpoint.
    Accepts username/email and password, returns JWT tokens.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        username = data.get("username")
        password = data.get("password")
        
        # Validate input
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        # Initialize user model
        user_model = UserModel()
        
        # Try to find user by username or email
        user_data = user_model.get_user_by_username(username)
        if not user_data:
            user_data = user_model.get_user_by_email(username)
        
        if not user_data:
            error_logger.warning(f"Login attempt failed: User '{username}' not found")
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Check if user is active
        if not user_data.get('is_active', True):
            error_logger.warning(f"Login attempt failed: Inactive user '{username}'")
            return jsonify({"error": "Account is deactivated"}), 401
        
        # Verify password
        if not compare_pass(password, user_data['password_hash']):
            error_logger.warning(f"Login attempt failed: Invalid password for user '{username}'")
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Update last login time
        user_model.update_last_login(user_data['_id'])
        
        # Create JWT tokens
        access_token = create_access_token(identity=user_data['_id'])
        refresh_token = create_refresh_token(identity=user_data['_id'])
        
        # Log successful login
        info_logger.info(f"User '{username}' logged in successfully")
        
        # Return user data (excluding sensitive information)
        user_response = {
            "user_id": user_data['_id'],
            "username": user_data['username'],
            "email": user_data['email'],
            "first_name": user_data.get('first_name'),
            "last_name": user_data.get('last_name'),
            "is_verified": user_data.get('is_verified', False),
            "created_at": user_data.get('created_at'),
            "last_login": user_data.get('last_login')
        }
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_response
        }), 200
        
    except Exception as e:
        error_logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh JWT access token using refresh token.
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Verify user still exists and is active
        user_model = UserModel()
        user_data = user_model.get_user_by_id(current_user_id)
        
        if not user_data or not user_data.get('is_active', True):
            return jsonify({"error": "User not found or inactive"}), 401
        
        # Create new access token
        new_access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            "access_token": new_access_token
        }), 200
        
    except Exception as e:
        error_logger.error(f"Token refresh error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user information.
    """
    try:
        current_user_id = get_jwt_identity()
        
        user_model = UserModel()
        user_data = user_model.get_user_by_id(current_user_id)
        
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
        # Return user data (excluding sensitive information)
        user_response = {
            "user_id": user_data['_id'],
            "username": user_data['username'],
            "email": user_data['email'],
            "first_name": user_data.get('first_name'),
            "last_name": user_data.get('last_name'),
            "is_verified": user_data.get('is_verified', False),
            "created_at": user_data.get('created_at'),
            "last_login": user_data.get('last_login'),
            "profile": user_data.get('profile', {}),
            "settings": user_data.get('settings', {})
        }
        
        return jsonify({"user": user_response}), 200
        
    except Exception as e:
        error_logger.error(f"Get current user error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
        
    