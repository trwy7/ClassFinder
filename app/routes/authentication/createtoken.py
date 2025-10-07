"""
Allows users to create a token for the API.
"""

from datetime import datetime, timedelta
from flask import request
from app import app
from app.utilities.users import require_login, create_token
from app.utilities.responses import success_response, error_response

@app.route("/createtoken", methods=["POST", "GET"])
@require_login
def createtoken():
    """
    Allows users to create a token for the API.
    """
    user = request.user
    expiry = request.args.get("expiry")
    if expiry:
        try:
            expiry = datetime.utcfromtimestamp(float(expiry))
        except ValueError:
            return error_response("Invalid expiry time"), 400
    else:
        expiry = datetime.now() + timedelta(days=5*30)
    token = create_token(user.username, tokentype=request.args.get("type", "api"), expiry=expiry)
    response = success_response("Token created successfully", {"token": token.token})
    return response
