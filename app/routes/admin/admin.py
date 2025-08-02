"""
Basic admin route
"""
from flask import render_template, request
from app import app
from app.utilities.users import verify_user
from app.utilities.classes import get_current_period
from app.db import Class, User
from app.utilities.config import devmode

@app.route("/admin")
@verify_user(allowed_roles=["admin"])
def admin():
    """
    Display the admin dashboard.
    """
    user = request.user
    app.logger.debug(f"Admin page requested by {user.username}")
    app.logger.debug(f"Devmode: {devmode}")
    return render_template(
        "admin.html", user=user, classes=Class.query.all(), users=User.query.all(), devmode=devmode, period=get_current_period()
    )
