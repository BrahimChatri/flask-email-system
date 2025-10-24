from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from flask_limiter import RateLimitExceeded
from dotenv import load_dotenv
import os

from app.auth import auth_bp
from app.auth.logout import BLACKLIST
from app.mail import mail_bp
from app.user import user_bp
from app.extensions import limiter

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Ensure upload directory exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    
    # Initialize extensions
    jwt = JWTManager(app)
    mail = Mail(app)
    CORS(app)
    
    # Initialize rate limiter
    limiter.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(mail_bp)
    app.register_blueprint(user_bp)
    
    # JWT token revocation callback
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return jti in BLACKLIST
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({"error": "The page you are looking for was not found"}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({"error": "Internal server error"}), 500
    
    @app.errorhandler(RateLimitExceeded)
    def ratelimit_handler(e):
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy", "message": "Flask Gmail System is running"}), 200
    
    return app
