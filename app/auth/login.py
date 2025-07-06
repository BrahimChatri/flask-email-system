from . import auth_bp
from flask import request, jsonify
from models.user_model import UserModel
from dotenv import load_dotenv
from utils.authmanager import compare_pass, decrypt_data
import os 
from app import limiter

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
KEY = os.getenv("ENCREPTION_KEY")
user = UserModel(MONGO_URI, "users")

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("3 per minute")
def login():
    data = request.get_json()
    pass