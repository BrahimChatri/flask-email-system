from flask import Flask
from app.auth import auth_bp, BLACKLIST
from app.mail import mail_bp
from app.user import user_bp
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


def create_app():
    app = Flask(__name__)
    
    # Load configs first
    app.config.from_object('config.Config')
    
    # Initialize extensions
    jwt = JWTManager(app)
    mail = Mail(app)
    CORS(app)

    # initialize the limiter
    limiter.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(mail_bp)
    app.register_blueprint(user_bp)
    
    # Token revocation callback
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return jti in BLACKLIST
    
    # # to see the request data for debugging 
    # @app.before_request
    # def log_request():
    #     print(f"➡️ {request.method} {request.path}")
    #     print("Headers:", dict(request.headers))
    #     print("Body:", request.get_data())
    
    # 404 handler
    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({"error": "the page you are looking for was not found"}), 404
    @app.errorhandler(RateLimitExceeded)
    def ratelimit_handler(e):
        return jsonify(error="Rate limit exceeded. Try again later."), 429
    return app
