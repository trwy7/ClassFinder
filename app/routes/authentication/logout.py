"""
Allows users to log out.
"""
from flask import redirect, url_for, request
from app import app
from app.utilities.users import require_login, get_token, delete_token
from app.utilities.config import devmode


@app.route("/logout")
@require_login
def logout():
    """
    Log out the user by deleting the token and redirecting to the account page.
    """
    token = get_token(request.cookies.get("token"))
    delete_token(token)
    response = redirect(url_for("index"))
    if request.cookies.get("admin_token"):
        response.set_cookie(
            "token", request.cookies.get("admin_token"), httponly=True, samesite="Lax", secure=not devmode, max_age=604800
        )
        response.set_cookie(
            "admin_token", "", httponly=True, samesite="Lax", secure=not devmode, max_age=0
        )
    else:
        response.set_cookie(
            "token", "", httponly=True, samesite="Lax", secure=not devmode, max_age=0
        )
    return response
