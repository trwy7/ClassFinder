"""
Basic admin route
"""
from shutil import copyfile
import os
from flask import render_template, request, abort
from app import app
from app.utilities.users import require_login, require_role
from app.utilities.classes import get_current_period
from app.utilities.responses import success_response
from app.db import Class, User
from app.utilities.config import devmode

CAN_MIGRATE = False
if devmode and os.path.isfile("data/db.sqlite3") and os.path.isfile("instance/db.sqlite3"):
    CAN_MIGRATE = True

@app.route("/admin")
@require_login
@require_role(["admin"])
def admin():
    """
    Display the admin dashboard.
    """
    user = request.user
    app.logger.debug(f"Admin page requested by {user.username}")
    app.logger.debug(f"Devmode: {devmode}")
    return render_template(
        "admin/admin.html", user=user, classes=Class.query.all(), users=User.query.all(), devmode=devmode, period=get_current_period(), can_migrate=CAN_MIGRATE
    )

@app.route("/admin/copyprod", methods=["POST"])
@require_login
@require_role(["admin"])
def copy_prod_to_dev():
    """
    Copy the production database over the development database.
    """
    if not CAN_MIGRATE:
        return abort(403)
    copyfile("data/db.sqlite3", "instance/db.sqlite3")
    if os.environ.get("BELL_DELAY_PATH"):
        prod_bell_delay_path = os.path.join("data", "bell_delay.txt")
        dev_bell_delay_path = os.environ.get("BELL_DELAY_PATH")
        if os.path.isfile(prod_bell_delay_path) and os.path.isfile(dev_bell_delay_path):
            copyfile(prod_bell_delay_path, dev_bell_delay_path)
            app.logger.info(f"Copied bell delay from {prod_bell_delay_path} to {dev_bell_delay_path}")
    app.logger.info("Production database copied over development database.")
    return success_response("Production database copied over development database.")