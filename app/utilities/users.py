"""
This file contains functions for user management.
"""

from typing import Literal
from datetime import datetime, timedelta
import os
import functools
import base64
import random
from flask_bcrypt import Bcrypt
from flask import request, redirect, render_template
from app.db import db, User, Token, Class
from app.utilities.responses import error_response
from app import app
from app.utilities.times import clear_user_cache

bcrypt = Bcrypt()
# TODO: Move most of these functions to a function within the user class, but keep the decorators here
readable_scopes = {
    "read-username": "See your username",
    "read-email": "See your email",
    "read-classes": "See your classes",
    "read-misc": "See general data about your account (like when your account was created)",
}

temp_passcodes = {}

def create_user(
    username: str, email: str, password: str, created_by="system", role="user"
):
    """
    Create a user

    Args:
        username (str): The username of the user.
        email (str): The email of the user.
        password (str): The password of the user.
        created_by (str): The user who created the user.
        role (str): The role of the user.

    Returns:
        User: The user that was created.
    """
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    if len(username) > 15:
        raise ValueError("Username must be below 15 characters long")
    user = User(
        username=username,
        email=email,
        password=hashed_password,
        created_by=created_by,
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user

def change_password(user: User, password: str):
    """
    Change a user's password

    Args:
        user (User): The user to change the password for.
        password (str): The new password.

    Returns:
        User: The user with the new password.
    """
    user.password = bcrypt.generate_password_hash(password).decode("utf-8")
    db.session.commit()
    return user

def check_password(username: str, password: str):
    """
    Check if a password is valid for a user

    Args:
        username (str): The username of the user.
        password (str): The password to check.

    Returns:
        bool: Whether the password is valid.
    """
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        return True
    if temp_passcodes.get(username):
        if temp_passcodes[username]['code'] == password:
            if temp_passcodes[username]['expires'] > datetime.now():
                del temp_passcodes[username]
                return True
            del temp_passcodes[username]
            app.logger.debug("Temporary passcode expired for user " + username)
            return False
    app.logger.debug("Password check failed for user " + username)
    return False

def create_token( # pylint: disable=too-many-arguments, too-many-positional-arguments
    username: str,
    tokentype: Literal["api", "refresh", "system", "app", "admin", "ext"],
    expiry: datetime = None,
    scopes: list = None,
    noexpiry: bool = False,
    granted_to: str = None, # This is used for external tokens, like those created through /auth
):
    """
    Create a token for a user

    Args:
        username (str): The username of the user.
        tokentype (Literal["api", "refresh", "system", "app", "admin"]): The type of token to create.
        expiry (datetime): The expiry date of the token.

    Returns:
        Token: The token that was created
    """
    nexpiry = expiry
    if noexpiry:
        app.logger.debug("Creating non-expiring token for user " + username)
        nexpiry = None
    else:
        if nexpiry is None:
            nexpiry = datetime.now()
            if tokentype in ("api", "app"):
                nexpiry += timedelta(days=60)
            elif tokentype == "refresh":
                nexpiry += timedelta(days=31)
            elif tokentype == "system":
                nexpiry += timedelta(days=14)
            elif tokentype == "admin":
                nexpiry += timedelta(hours=1)
            elif tokentype == "ext":
                nexpiry += timedelta(days=90)
            else:
                nexpiry += timedelta(days=1)
    app.logger.debug("Creating " + tokentype + " token for user " + username + " with expiry " + str(nexpiry))
    token = Token(
        token=os.urandom(30).hex(),
        user_id=username,
        type=tokentype,
        expire=nexpiry,
        scopes=" ".join(scopes) if scopes is not None else None,
        granted_to=granted_to
    )
    db.session.add(token)
    db.session.commit()
    return token

def check_token(token: str):
    """
    Check if a token is valid

    Args:
        token (str): The token string to check.

    Returns:
        User: The user that the token belongs to.
    """
    token = Token.query.filter_by(token=token).first()
    if token:
        user = User.query.filter_by(username=token.user_id).first()
        return user
    return None

def get_token(token: str):
    """
    Get a token

    Args:
        token (str): The token string to get.

    Returns:
        Token: The token.
    """
    return Token.query.filter_by(token=token).first()

def delete_token(token: Token):
    """
    Delete a token

    Args:
        token (Token): The token to delete.

    Returns:
        None
    """
    db.session.delete(token)
    db.session.commit()

def check_email(email: str):
    """
    Check if an email has a user

    Args:
        email (str): The email to check.

    Returns:
        User: The user with the email.
    """
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    return False

def get_user_count(blacklist_roles: list = []): # pylint: disable=dangerous-default-value
    """
    Get the number of users in the database

    Args:
        blacklist_roles (list): Roles to exclude from the count.

    Returns:
        int: The number of users.
    """
    return User.query.filter(User.role.notin_(blacklist_roles)).count()

def get_user(username: str):
    """
    Get a user by username

    Args:
        username (str): The username of the user.

    Returns:
        User: The user.
    """
    return User.query.filter_by(username=username).first()

def get_all_users():
    """
    Get all users

    Returns:
        list[User]: A list of all users.
    """
    return User.query.all()

def change_user_role(user: User, role: str):
    """
    Change a user's role

    Args:
        user (User): The user to change the role for.
        role (str): The new role.

    Returns:
        User: The user with the new role.
    """
    user.role = role
    db.session.commit()
    return user

def change_username(user: User, username: str, require_change: bool = None):
    """
    Change a user's username

    Args:
        user (User): The user to change the username for.
        username (str): The new username.

    Returns:
        User: The user with the new username.
    """
    if User.query.filter_by(username=username).first():
        raise ValueError("Username already exists")
    old_username = user.username

    # Update related records in other tables
    related_tokens = Token.query.filter_by(user_id=old_username).all()
    related_classes = Class.query.filter(Class.users.any(username=old_username)).all()
    for course in related_classes:
        course.users.remove(user)
    for token in related_tokens:
        token.user_id = username

    # Update created_by for each class
    created_courses = Class.query.filter_by(created_by=old_username).all()
    for course in created_courses:
        course.created_by = username

    # Update username
    user.username = username

    # Update classes
    for course in related_classes:
        course.users.append(user)

    # Update requires_username_change
    if require_change is True:
        user.requires_username_change = True
    elif require_change is False:
        user.requires_username_change = False

    # Commit
    db.session.commit()

    return user

def get_user_by_email(email: str):
    """
    Get a user by email

    Args:
        email (str): The email of the user.

    Returns:
        User: The user.
    """
    return User.query.filter_by(email=email).first()

def revoke_external_token(user: User, granted_to: str):
    """
    Revoke an external token for a user

    Args:
        user (User): The user to revoke the token for.
        granted_to (str): The identifier of the external service.

    Returns:
        None
    """
    tokens = Token.query.filter_by(user_id=user.username, granted_to=granted_to).all()
    if tokens:
        for token in tokens:
            delete_token(token)
    else:
        raise ValueError("No external tokens found for this user and granted_to value.")

def delete_user(user: User):
    """
    Delete a user

    Args:
        user (User): The user to delete.

    Returns:
        None
    """
    for token in user.tokens:
        delete_token(token)
    clear_user_cache(user)
    db.session.delete(user)
    db.session.commit()

def create_temp_passcode(user: User, length: int=6):
    """
    Create a temporary passcode for a user

    Args:
        user (User): The user to create the passcode for.
        length (int): The length of the passcode.

    Returns:
        str: The temporary passcode.
    """
    temp_passcodes[user.username] = {
        'code': "".join(
            random.choice("0123456789") for _ in range(length)
        ),
        'expires': datetime.now() + timedelta(minutes=5)
    }
    return temp_passcodes[user.username]['code']

def set_color(user: User, color_hue: int):
    """
    Set the user's preferred color.

    Args:
        user (User): The user to set the color for.
        color_hue (int): The hue of the color to set.

    Returns:
        User: The user with the updated color.
    """
    if not 0 <= color_hue <= 360:
        raise ValueError("Color hue must be between 0 and 360")
    user.color_hue = color_hue
    db.session.commit()
    return user

def set_custom_delays(user: User, start_delay: int, end_delay: int):
    """
    Set the user's custom start and end delays.

    Args:
        user (User): The user to set the delays for.
        start_delay (int): The start delay in seconds.
        end_delay (int): The end delay in seconds.

    Returns:
        User: The user with the updated delays.
    """
    if start_delay is not None and not -300 <= start_delay <= 600:
        raise ValueError("Start delay must be between -300 and 600 seconds")
    if end_delay is not None and not -600 <= end_delay <= 300:
        raise ValueError("End delay must be between -600 and 300 seconds")
    user.custom_start_delay = start_delay
    user.custom_end_delay = end_delay
    db.session.commit()
    clear_user_cache(user)
    return user

# Verify user

def get_active_token():
    """
    Check if the request has a token in it, valid or not
    """
    auth = request.headers.get("Authorization")
    # Check cookies, query string and URL parameters for an auth token
    token = (
        request.cookies.get("token")
        or request.args.get("authtoken")
        or (request.view_args.get("authtoken") if getattr(request, "view_args", None) else None)
    )
    if auth:
        if auth.startswith("Bearer "):
            token = auth.split(" ")[1]
        elif auth.startswith("Basic "):
            return None
        else:
            if auth != "":
                token = auth.split(" ")[1]
    app.logger.debug(f"Active token from request: {token[0:4] if token else 'None'}")
    return token

def get_active_pwd():
    """
    Check if the request has basic auth in it, valid or not
    """
    auth = request.headers.get("Authorization")
    if auth:
        if auth.startswith("Basic "):
            try:
                auth = base64.b64decode(auth.split(" ")[1]).decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                return None
            username, password = auth.split(":")
            return (username, password)
    return None

def check_token_validity(token: str):
    """
    Check if a token is valid, and return the user and token if it is

    Args:
        token (str): The token string to check.
    Returns:
        (User, Token): The user and token if valid, else (None, None).
    """
    token = Token.query.filter_by(token=token).first()
    if token:
        app.logger.debug(f"Found token for user {token.user_id}, checking validity")
        if token.expire is not None and token.expire < datetime.now():
            app.logger.debug("Token has expired")
            return (None, None)
        user = User.query.filter_by(username=token.user_id).first()
        if user:
            app.logger.debug(f"Token is valid for user {user.username}")
            return (user, token)
    app.logger.debug("Token is invalid or expired")
    return (None, None)

def check_token_scopes(token: Token, required_scopes: list[list[str]]):
    """
    Check if a token has the required scopes

    Args:
        token (Token): The token to check.
        required_scopes (list[list[str]]): The required scopes.
    Returns:
        bool: Whether the token has the required scopes.
    """
    if token.scopes is None:
        return True
    token_scopes = token.scopes.split(" ")
    for scope_group in required_scopes:
        allow_token = True
        for scope in scope_group:
            if not scope in token_scopes:
                allow_token = False
                break
        if allow_token:
            return True
    return False

def auth_user():
    """
    Authenticate a user based on the current request. Should only be run once per request.
    Returns:
        (User, Token): The authenticated user and token, (User, None) if authenticated with password, else (None, None).
    """
    if request.user is not None:
        return (request.user, request.token)
    request.user = None
    request.token = None
    ctoken = get_active_token()
    if ctoken:
        user, token = check_token_validity(ctoken)
        if user and token:
            request.user = user
            request.token = token
            app.logger.debug(f"Authenticated user {user.username} with token")
            return (user, token)
    cpwd = get_active_pwd()
    if cpwd:
        username, password = cpwd
        if check_password(username, password):
            user = User.query.filter_by(username=username).first()
            if user:
                request.user = user
                app.logger.debug(f"Authenticated user {user.username} with password")
                return (user, None)
    app.logger.debug("No valid authentication found in request")
    return (None, None)

def require_logged_out(f):
    """
    Decorator to require a user to be logged out.
    If the user is logged in, they will be redirected to the home page.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user, _ = auth_user()
        if user is not None:
            return redirect("/dashboard")
        return f(*args, **kwargs)
    return decorated_function

def require_login(_func=None):
    """
    Decorator to require a user to be logged in.
    """
    def _has_required_scopes_marker(func):
        cur = func
        # Walk the __wrapped__ chain to find a marker set by require_scopes
        while cur is not None:
            if getattr(cur, "_required_scopes", None) is not None:
                return True
            cur = getattr(cur, "__wrapped__", None)
        return False

    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            user, token = auth_user()
            if user is None:
                if request.path.startswith("/api/") or request.method != "GET":
                    if request.path.startswith("/api/plain/"):
                        return "Unauthorized", 401
                    if request.path.endswith(".css") or request.path.endswith(".js"):
                        return "", 401
                    return error_response("Unauthorized"), 401
                resp = redirect("/login")
                resp.set_cookie("redirect_to", request.path + ("?" + request.query_string.decode("utf-8") if request.query_string else ""))
                return resp

            # If a token was used for auth and it has scopes, disallow it unless the endpoint requires scopes
            if token is not None and token.scopes is not None and not _has_required_scopes_marker(f):
                if request.path.startswith("/api/") or request.method != "GET":
                    if request.path.startswith("/api/plain/"):
                        return "Forbidden: This token has scopes and cannot be used for this request", 403
                    return error_response("Forbidden: This token has scopes and cannot be used for this request"), 403
                return render_template("templates/error.html", status_code=403, error_message="Forbidden: This token has scopes and cannot be used for this request"), 403

            return f(*args, **kwargs)
        return decorated_function

    # If used without parentheses: @require_login
    if _func is not None:
        return decorator(_func)
    return decorator

def require_scopes(required_scopes: list[list[str]]): # pylint: disable=dangerous-default-value
    """
    Decorator to require a user to have certain scopes.
    If the user does not have the required scopes, they will receive a 403 error.
    """
    def decorator(func):
        func._required_scopes = required_scopes  # Marker attribute to indicate required scopes
        @functools.wraps(func)
        def decorated_function(*args, **kwargs):
            user, token = auth_user()
            if user is None:
                raise RuntimeError("This decorator requires the user to be logged in. Use @require_login before this decorator.")
            if not check_token_scopes(token, required_scopes):
                return error_response("Forbidden: This token does not have the required scopes"), 403
            return func(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(roles: list):
    """
    Decorator factory to require a user to have a certain role.
    Usage:
      @require_role(["admin"]) or @require_role(["admin", "moderator"]) 
    If the user does not have the required role, they will receive a 403 error.
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            user, _ = auth_user()
            if user is None:
                raise RuntimeError("This decorator requires the user to be logged in. Use @require_login before this decorator.")
            if user.role not in roles:
                return render_template("templates/error.html", status_code=403, error_message="Forbidden"), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
