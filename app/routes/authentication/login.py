"""
This module handles the login functionality for the application.
"""
from flask import render_template, request, Response
from app import app
from app.utilities.config import devmode
from app.utilities.users import check_password, create_token
from app.addons.limiter import limiter
from app.utilities.responses import error_response, success_response

@app.route("/login")
def login():
    """
    Display the login page.
    """
    return render_template("login.html", devmode=devmode)
    # return redirect("/")

@app.route("/login", methods=["POST"])
@limiter.limit("20/minute")
def login_post():
    """
    Handle the login form submission.
    """
    app.logger.debug(request.form)
    if request.form.get("username") and request.form.get("password"): # legacy clients
        if check_password(request.form.get("username").lower(), request.form.get("password")):
            response = Response(render_template("account/legacy_login.html", username=request.form.get("username").lower()))
            response.set_cookie(
                "token",
                create_token(request.form.get("username").lower(), 'refresh').token,
                samesite="Lax",
                secure=not devmode,
                max_age=604800,
            )
            app.logger.debug(f"User {request.form.get('username')} logged in via legacy client")
            return response, 200
        return render_template("login.html", devmode=devmode, status_message="Invalid Credentials"), 400
    if request.is_json is False:
        return error_response("Invalid Content Type: Expected application/json"), 400
    username = request.json.get("username")
    password = request.json.get("password")
    if check_password(username, password):
        response = success_response("Login Successful", {"redirect_to": "/dashboard" if not request.cookies.get("redirect_to") else request.cookies.get("redirect_to")})
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
