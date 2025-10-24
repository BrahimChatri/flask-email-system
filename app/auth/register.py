from . import auth_bp
from flask import request, jsonify, url_for
from app.models.user_model import UserModel
from app.utils.authmanager import hash_pass, encrypt_data, validate_password_strength
from app.utils.logger import error_logger, info_logger
from app.extensions import limiter
from flask import current_app
from datetime import datetime


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """
    User registration endpoint.
    Creates a new user account with encrypted sensitive data.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract and validate required fields
        username = data.get("username", "").strip()
        password = data.get("password", "")
        email = data.get("email", "").strip()
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        phone_number = data.get("phone_number", "").strip()
        address = data.get("address", "").strip()
        date_of_birth = data.get("date_of_birth", "").strip()
        
        # Validate required fields
        if not username:
            return jsonify({"error": "Username is required"}), 400
        
        if not password:
            return jsonify({"error": "Password is required"}), 400
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        # Validate password strength
        password_validation = validate_password_strength(password)
        if not password_validation["is_valid"]:
            return jsonify({
                "error": "Password validation failed",
                "details": password_validation["errors"]
            }), 400
        
        # Initialize user model
        user_model = UserModel()
        
        # Check if username already exists
        if user_model.get_user_by_username(username):
            error_logger.warning(f"Registration failed: Username '{username}' already exists")
            return jsonify({"error": "Username already exists"}), 400
        
        # Check if email already exists
        if user_model.get_user_by_email(email):
            error_logger.warning(f"Registration failed: Email '{email}' already exists")
            return jsonify({"error": "Email already exists"}), 400
        
        # Hash password
        try:
            password_hash = hash_pass(password)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
        # Get encryption key from config
        encryption_key = current_app.config.get('ENCRYPTION_KEY')
        if not encryption_key:
            error_logger.error("Encryption key not configured")
            return jsonify({"error": "Server configuration error"}), 500
        
        # Encrypt sensitive data
        try:
            encrypted_first_name = encrypt_data(first_name, encryption_key) if first_name else None
            encrypted_last_name = encrypt_data(last_name, encryption_key) if last_name else None
            encrypted_email = encrypt_data(email, encryption_key)
            encrypted_phone = encrypt_data(phone_number, encryption_key) if phone_number else None
            encrypted_address = encrypt_data(address, encryption_key) if address else None
            encrypted_dob = encrypt_data(date_of_birth, encryption_key) if date_of_birth else None
        except ValueError as e:
            error_logger.error(f"Encryption error: {str(e)}")
            return jsonify({"error": "Failed to encrypt user data"}), 500
        
        # Create user
        try:
            user_id = user_model.create_user(
                email=encrypted_email,
                username=username,
                password_hash=password_hash,
                first_name=encrypted_first_name,
                last_name=encrypted_last_name
            )
            
            # Log successful registration
            info_logger.info(f"User '{username}' registered successfully")
            
            return jsonify({
                "message": "User registered successfully",
                "user_id": user_id,
                "redirect": url_for("auth.login")
            }), 201
            
        except ValueError as e:
            error_logger.error(f"User creation error: {str(e)}")
            return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        error_logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/check-username/<username>', methods=['GET'])
def check_username(username):
    """
    Check if a username is available.
    """
    try:
        if not username or len(username.strip()) < 3:
            return jsonify({"available": False, "error": "Username must be at least 3 characters"}), 400
        
        user_model = UserModel()
        user_exists = user_model.get_user_by_username(username.strip())
        
        return jsonify({
            "available": not user_exists,
            "username": username.strip()
        }), 200
        
    except Exception as e:
        error_logger.error(f"Username check error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/check-email/<email>', methods=['GET'])
def check_email(email):
    """
    Check if an email is available.
    """
    try:
        if not email or '@' not in email:
            return jsonify({"available": False, "error": "Invalid email format"}), 400
        
        user_model = UserModel()
        user_exists = user_model.get_user_by_email(email.strip().lower())
        
        return jsonify({
            "available": not user_exists,
            "email": email.strip().lower()
        }), 200
        
    except Exception as e:
        error_logger.error(f"Email check error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
