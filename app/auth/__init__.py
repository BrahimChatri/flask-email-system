from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Import the route files to register them to this blueprint
from . import login, register, logout, password_reset, email_verification
