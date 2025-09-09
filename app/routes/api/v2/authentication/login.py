"""
Login API
"""
from datetime import datetime, timezone
from flask import request
from app import app
from app.addons.limiter import limiter
from app.utilities.users import check_password, create_token
from app.utilities.responses import error_response, success_response

@app.route("/api/v2/login", methods=["POST"])
@limiter.limit("10/minute")
def api_login_post():
    """
    Login via the API
    """
    username = request.json.get("username")
    password = request.json.get("password")
    app.logger.debug(f"Processing api v2 login for {username}")
    ttype = request.json.get("type")
    expiry = request.json.get("expiry", None)
    app.logger.debug(f"Processing api v2 login for {username} with type {type} and expiry {expiry}")
    if expiry:
        expiry = datetime.fromtimestamp(expiry, timezone.utc)
    if ttype not in ["app", "api"]:
        app.logger.debug(f"Invalid token type {type}")
        return error_response("Invalid token type, valid types are api and app"), 400
    if check_password(username, password):
        app.logger.debug(f"Login successful for {username}")
        response = success_response("Login Successful",
                                    {
                                        "token": create_token(username, tokentype=ttype, expiry=expiry).token
                                    } if not request.args.get("notoken") else {})
        return response, 200
    app.logger.debug(f"Invalid credentials for {username}")
    return error_response("Invalid Credentials"), 400
