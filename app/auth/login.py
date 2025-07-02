from . import auth_bp
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    