from typing import Literal
from . import auth_bp
from flask_jwt_extended import jwt_required, get_jwt

BLACKLIST = set()

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout() -> tuple[dict[str, str], Literal[200]]:
    jti = get_jwt()["jti"]
    BLACKLIST.add(jti)
    return {"message": "Successfully logged out"}, 200
