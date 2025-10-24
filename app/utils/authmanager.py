import bcrypt
import hashlib
import os
import base64
import json
from cryptography.fernet import Fernet, InvalidToken
from app.utils.logger import error_logger, info_logger

# Minimum password length
MIN_PASSWORD_LENGTH = 8

def decrypt_user_data(data: dict, key: str) -> dict:
    """
    Decrypt user data as a full dictionary.
    Returns decrypted data or original data if decryption fails.
    """
    try:
        decrypted = data.copy()
        fields_to_decrypt = ["first_name", "last_name", "email", "phone_number", "address", "date_of_birth"]
        
        for field in fields_to_decrypt:
            if field in decrypted and decrypted[field]:
                decrypted_value = decrypt_data(decrypted[field], key=key)
                if decrypted_value:
                    decrypted[field] = decrypted_value
        
        return decrypted
    except Exception as e:
        error_logger.error(f"Error decrypting user data: {str(e)}")
        return data

def hash_pass(password: str) -> str:
    """
    Hash a password using bcrypt.
    Returns the hashed password as a string.
    Raises ValueError if password is invalid.
    """
    try:
        if not password:
            raise ValueError("Password cannot be empty")
        
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
        
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
        
    except Exception as e:
        error_logger.error(f"Error hashing password: {str(e)}")
        raise ValueError(f"Failed to hash password: {str(e)}")

def compare_pass(password: str, hashed_password: str) -> bool:
    """
    Compare a password with its hash.
    Returns True if they match, False otherwise.
    """
    try:
        if not password or not hashed_password:
            error_logger.error("Invalid password or hash provided for comparison")
            return False
        
        return bcrypt.checkpw(
            password.encode("utf-8"), 
            hashed_password.encode("utf-8")
        )
        
    except Exception as e:
        error_logger.error(f"Error comparing password: {str(e)}")
        return False

def _generate_key(key: str) -> bytes:
    """
    Generate a Fernet key based on the provided key.
    """
    try:
        digest = hashlib.sha256(key.encode()).digest()
        return base64.urlsafe_b64encode(digest)
    except Exception as e:
        error_logger.error(f"Error generating encryption key: {str(e)}")
        raise ValueError(f"Failed to generate encryption key: {str(e)}")

def encrypt_data(data: str | dict | list, key: str) -> str:
    """
    Encrypt given data using a key.
    Returns encrypted data as a string.
    """
    try:
        if not key:
            raise ValueError("Encryption key is required")
        
        # Convert complex data types to JSON string
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
        elif not isinstance(data, str):
            data = str(data)
        
        fernet_key = _generate_key(key)
        fernet = Fernet(fernet_key)
        encrypted = fernet.encrypt(data.encode())
        return encrypted.decode()
        
    except Exception as e:
        error_logger.error(f"Error encrypting data: {str(e)}")
        raise ValueError(f"Failed to encrypt data: {str(e)}")

def decrypt_data(data: str, key: str) -> str | None:
    """
    Decrypt given data using a key.
    Returns decrypted data or None if decryption fails.
    """
    try:
        if not data or not key:
            return None
        
        fernet_key = _generate_key(key)
        fernet = Fernet(fernet_key)
        decrypted = fernet.decrypt(data.encode()).decode()
        return decrypted
        
    except (InvalidToken, base64.binascii.Error, Exception) as e:
        error_logger.warning(f"Failed to decrypt data: {str(e)}")
        return None

def validate_password_strength(password: str) -> dict:
    """
    Validate password strength.
    Returns a dictionary with validation results.
    """
    errors = []
    warnings = []
    
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    
    if not any(c.isupper() for c in password):
        warnings.append("Consider adding uppercase letters")
    
    if not any(c.islower() for c in password):
        warnings.append("Consider adding lowercase letters")
    
    if not any(c.isdigit() for c in password):
        warnings.append("Consider adding numbers")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        warnings.append("Consider adding special characters")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "strength_score": max(0, len(password) - MIN_PASSWORD_LENGTH + len([w for w in warnings if "Consider" not in w]))
    }