"""
Account routes
"""

from flask import render_template, request
from app import app
from app.utilities.users import require_login, delete_user, change_username, revoke_external_token, create_temp_passcode, set_color, readable_scopes
from app.utilities.responses import success_response
from app.utilities.classes import (
    get_today_courses,
    neededperiods,
    get_periods_of_user_classes,
)
from app.utilities.config import canvas_url, allow_leave


@app.route("/account")
@require_login
def account():
    """
    This route displays the user's account information.
    """
    user = request.user
    needcanvaslink = False
    for course in user.classes:
        if course.canvasid is None:
            needcanvaslink = True
            break
    has_external_tokens = False
    for token in user.tokens:
        if token.granted_to is not None:
            has_external_tokens = True
            break
    return render_template(
        "account/account.html",
        user=user,
        currentclasses=get_today_courses(user),
        classestoadd=[
            period
            for period in neededperiods
            if period not in get_periods_of_user_classes(user)
        ],
        authorized_sites=[
            (
                token.granted_to,
                [
                    readable_scopes[scope]
                    for scope in token.scopes.split(" ")
                ]
            )
            for token in user.tokens if token.granted_to is not None and token.type == "ext"
        ],
        neededperiods=neededperiods,
        canvasurl=canvas_url,
        needcanvaslink=needcanvaslink,
        allow_leave=allow_leave,
        has_external_tokens=has_external_tokens,
    )

@app.route("/account/delete", methods=["GET"])
@require_login
def account_delete_get():
    """
    This route displays the account deletion page.
    """
    return render_template("account/account_delete.html")

@app.route("/account/delete", methods=["POST"])
@require_login
def account_delete():
    """
    This route deletes the user's account.
    """
    delete_user(request.user)
    return success_response("User deleted successfully")

@app.route("/account/changeusername")
@require_login
def account_changeusername_get():
    """
    This route displays the username change page.
    """
    if not request.user.requires_username_change:
        return render_template("templates/error.html", status_code=403, error_message="You do not currently need to change your name"), 403
    return render_template("changeusername.html")

@app.route("/account/changeusername", methods=["POST"])
@require_login
def account_changeusername():
    """
    This route changes the user's username.
    """
    if not request.user.requires_username_change:
        return {"error": "Username change not required"}, 400
    newusername = request.json.get("username")
    if not newusername:
        return {"error": "No username provided"}, 400
    change_username(request.user, newusername, require_change=False)
    return success_response("Username changed successfully")

@app.route("/account/revoke_token", methods=["POST"])
@require_login
def account_revoke_token():
    """
    This route revokes an external token granted to the user.
    """
    token_granted_to = request.json.get("granted_to")
    if not token_granted_to:
        return {"error": "No token provided"}, 400
    revoke_external_token(request.user, token_granted_to)
    return success_response("Token revoked successfully")

@app.route("/account/temp_passcode", methods=["GET"])
@require_login
def account_temp_passcode():
    """
    This route generates a temporary passcode for the user.
    """
    passcode = create_temp_passcode(request.user)
    return success_response(f"Temporary passcode created successfully: {passcode}", {"passcode": passcode})

@app.route("/account/set_color", methods=["POST"])
@require_login
def account_set_color():
    """
    This route sets the user's preferred color.
    """
    color_hue = request.json.get("color_hue")
    if color_hue is not None:
        set_color(request.user, int(color_hue))
        return success_response("Color set successfully")
    return {"error": "No color provided"}, 400
