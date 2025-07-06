from flask import Blueprint

mail_bp = Blueprint("mail", __name__, url_prefix="/mail")

from . import (
    inbox,
    send
    )