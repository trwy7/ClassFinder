"""
Logout Routes
"""
from flask import request
from app import app
from app.utilities.users import require_login, delete_token, get_token
from app.utilities.responses import success_response, error_response

@app.route("/api/v2/logout", methods=["POST"])
def logout_post():
    """
    Logout via the API
    """
    token = request.json.get("token")
    if token is None:
        return error_response("Token Required"), 400
    token = get_token(token)
    if token is None:
        return error_response("Invalid Token"), 400
    delete_token(token)
    return success_response("Logout Successful"), 200

@app.route("/api/v2/logout/all", methods=["GET", "POST"])
@require_login
def logout_all():
    """
    Logout of all devices via the API
    """
    user = request.user
    for token in user.tokens:
        delete_token(token)
    return success_response("Logout of all devices Successful"), 200
