from . import auth_bp
from flask import request, jsonify
from models.user_model import UserModel
from dotenv import load_dotenv
from utils.authmanager import hash_pass, decrypt_data
import os 


load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
KEY = os.getenv("ENCREPTION_KEY")
user = UserModel(MONGO_URI, "users")

# route for register only post request is allowed 
@auth_bp.route("/register", methods=["POST"])
def register():
    pass    