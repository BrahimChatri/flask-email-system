import bcrypt
import utils.logger as logger
from cryptography.fernet import Fernet, InvalidToken
import base64
import hashlib, os

min_: int = 8

# This function is used to decrypt user data as full dict.
def decrypt_user_data(data: dict, key: str) -> dict:
    decrypted = data.copy()
    for field in ["first_name","last_name", "email", "phone_number", "address", "date_of_birth"]:
        decrypted[field] = decrypt_data(data[field], key=key)
    return decrypted

def hash_pass(password: str) -> str:
    try:
        if not password or len(password) < min_  :
            return "password is too short "
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    except UnicodeDecodeError:
        logger.Error_logger.error("Error while trying to decode the psw")

def compare_pass(password: str, hashed_password: str) -> bool:
    """This is for comparing a (psw <-> hash)"""
    try:
        if not hashed_password:
            logger.Error_logger.error("Invalid hash provided for comparison")
            return False
        return bcrypt.checkpw(
            password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    except ValueError:
        logger.Error_logger.error("Invalid hash")
        return False
    
def _generate_key(key: str) -> bytes:
    """Generate a Fernet key based on the provided key"""
    digest = hashlib.sha256(key.encode()).digest()
    return base64.urlsafe_b64encode(digest)

def encrypt_data(data: str | dict | list, key: str) -> str:
    """Encrypt given data using a key"""
    if isinstance(data, (dict, list)):
        import json
        data = json.dumps(data)

    fernet_key = _generate_key(key)
    fernet = Fernet(fernet_key)
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()


def decrypt_data(data: str, key: str):
    """Decrypt given data using a key"""
    try :
        fernet_key = _generate_key(key)
        fernet = Fernet(fernet_key)
        decrypted = fernet.decrypt(data.encode()).decode()
        return decrypted
    except (InvalidToken, base64.binascii.Error):
        # Decryption failed (data was not encrypted properly)
        print("[Warning] Data is not encrypted or key is invalid.")
        return None
