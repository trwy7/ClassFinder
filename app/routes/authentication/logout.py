"""
Allows users to log out.
"""
from flask import redirect, url_for, request
from app import app
from app.utilities.users import require_login, get_token, delete_token


@app.route("/logout")
@require_login
def logout():
    """
    Log out the user by deleting the token and redirecting to the account page.
    """
    token = get_token(request.cookies.get("token"))
    delete_token(token)
    response = redirect(url_for("index"))
    response.set_cookie(
        "token", "", httponly=True, samesite="Lax", secure=True, max_age=0
    )
    return response
