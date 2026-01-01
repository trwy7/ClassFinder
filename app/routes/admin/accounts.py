"""
Allows the admin to manage user accounts.
"""
from flask import render_template, request, redirect, url_for
from app import app
from app.utilities.users import (
    require_login,
    require_role,
    get_user,
    delete_user,
    create_token,
    create_user,
    get_user_by_email,
    change_password,
    change_username
)
from app.db import db
from app.utilities.validation import validate_username
from app.utilities.responses import error_response, success_response
from app.utilities.config import devmode


@app.route("/admin/account/<username>", methods=["DELETE"])
@require_login
@require_role(["admin"])
def delete_account(username):
    """
    Deletes a user account.
    """
    user = request.user
    app.logger.info(f"Deleting account for {username} by {user.username}.")
    deluser = get_user(username)
    if deluser:
        if deluser == user:
            app.logger.warning(f"{user.username} tried to delete their own account.")
            return error_response("Cannot delete own account."), 403
        app.logger.info(f"{user.username} has deleted {deluser.username}'s account.")
        delete_user(deluser)
        return success_response("User deleted."), 200
    app.logger.warning(f"{user.username} tried to delete non-existent account {username}.")
    return error_response("User not found."), 404


@app.route("/admin/account/<username>/login", methods=["POST", "GET"])
@require_login
@require_role(["admin"])
def login_as(username):
    """
    Logs in as a user.
    """
    loguser = get_user(username)
    if loguser:
        token = create_token(username, tokentype="admin")
        response = (
            success_response("Logged in as user.")
            if request.method == "POST"
            else redirect(url_for("dashboard"))
        )
        response.set_cookie(
            "token",
            token.token,
            httponly=True,
            samesite="Lax",
            secure=not devmode,
            max_age=600,
        )
        response.set_cookie(
            "admin_token",
            request.cookies.get("token"),
            httponly=True,
            samesite="Lax",
            secure=not devmode,
            max_age=604800,
        )
        return response
    return error_response("User not found."), 404


@app.route("/admin/create/account")
@require_login
@require_role(["admin"])
def create_account():
    """"
    Creates a new user account.
    """
    return render_template("account/createaccount.html")


@app.route("/admin/create/account", methods=["POST"])
@require_login
@require_role(["admin"])
def create_account_post():
    """
    Creates a new user account.
    """
    user = request.user
    username = request.json.get("username")
    email = request.json.get("email")
    password = request.json.get("password")
    role = request.json.get("role", "user")
    app.logger.info(
        f"Creating account for {username} with email {email} by {user.username}."
    )
    if not request.json.get("bypass_username_requirements") and not validate_username(username):
        return error_response("Invalid username."), 400
    # if not validate_email(email):
    #     return error_response("Invalid email."), 400
    if not password:
        return error_response("Password is required."), 400
    if get_user(username):
        return error_response("Username already exists."), 400
    if get_user_by_email(email):
        return error_response("Email already exists."), 400
    create_user(username, email, password, role=role, created_by=user.username)
    return success_response("User created."), 200

@app.route("/admin/account/<username>/edit")
@require_login
@require_role(["admin"])
def edit_account(username):
    """"
    Edits a user account.
    """
    edituser = get_user(username)
    if edituser:
        return render_template("account/editaccount.html", user=edituser)
    return error_response("User not found."), 404

@app.route("/admin/account/<username>/edit", methods=["POST"])
@require_login
@require_role(["admin"])
def edit_account_post(username):
    """"
    Edits a user account.
    """
    user = request.user
    edituser = get_user(username)
    if edituser:
        nusername = request.json.get("username")
        email = request.json.get("email")
        role = request.json.get("role")
        password = request.json.get("password")
        if password is not None and password != "":
            app.logger.info(f"{user.username} has changed {edituser.username}'s password.")
            change_password(edituser, password)
        if email and email != edituser.email:
            app.logger.info(f"{user.username} has changed {edituser.username}'s email to {email}.")
            edituser.email = email
        if role and role != edituser.role and role != "":
            app.logger.info(f"{user.username} has changed {edituser.username}'s role to {role}.")
            edituser.role = role
        if nusername != edituser.username and nusername:
            if not request.json.get("bypass_username_requirements") and not validate_username(nusername):
                return error_response("Invalid username."), 400
            if get_user(nusername):
                return error_response("Username already exists."), 400
            app.logger.info(f"{user.username} has changed {edituser.username}'s username to {nusername}.")
            change_username(edituser, nusername)
        if edituser == user:
            app.logger.info(f"{user.username} has changed their own account.")
        if edituser.requires_username_change != request.json.get("requires_username_change", False):
            app.logger.info(f"{user.username} has changed {edituser.username}'s requires_username_change to {request.json.get('requires_username_change', False)}.") #pylint: disable=line-too-long
            edituser.requires_username_change = request.json.get("requires_username_change", False)
        if edituser.requires_reverification != request.json.get("reverify_email", False):
            app.logger.info(f"{user.username} has changed {edituser.username}'s requires_reverification to {request.json.get('reverify_email', False)}.") #pylint: disable=line-too-long
            edituser.requires_reverification = request.json.get("reverify_email", False)
        db.session.commit()
        return success_response("User updated."), 200
    return error_response("User not found."), 404
