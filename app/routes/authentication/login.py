"""
This module handles the login functionality for the application.
"""
from flask import render_template, request
from app import app
from app.utilities.config import devmode
from app.utilities.users import check_password, create_token
from app.addons.limiter import limiter
from app.utilities.responses import error_response, success_response
from app.utilities.config import status

@app.route("/login")
def login():
    """
    Display the login page.
    """
    return render_template("login.html", status=status, devmode=devmode)

@app.route("/login", methods=["POST"])
@limiter.limit("40/minute")
def login_post():
    """
    Handle the login form submission.
    """
    username = request.json.get("username")
    password = request.json.get("password")
    if check_password(username, password):
        response = success_response("Login Successful")
        response.set_cookie(
            "token",
            create_token(username, 'refresh').token,
            httponly=True,
            samesite="Lax",
            secure=not devmode,
            max_age=604800,
        )
        return response, 200
    return error_response("Invalid Credentials"), 400
