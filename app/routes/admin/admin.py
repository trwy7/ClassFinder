"""
Basic admin route
"""
from shutil import copyfile
import os
import datetime
from flask import render_template, request, abort
from app import app
from app.utilities.users import require_login, require_role, delete_user, get_all_users
from app.utilities.classes import get_current_period, get_all_courses, remove_class
from app.utilities.responses import success_response
from app.db import Class, User, db
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

@app.route("/admin/newsemester", methods=["POST"])
@require_login
@require_role(["admin"])
def new_semester():
    """
    Start a new semester by deleting all classes.
    """
    app.logger.warning("Starting new semester, requested by " + request.user.username)
    dbfile = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///","")
    newfile = dbfile.replace(".",f"_backup_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.")
    app.logger.info(f"Copying database to {newfile}")
    try:
        copyfile(dbfile, newfile)
    except FileNotFoundError:
        copyfile(f"instance/{dbfile}", f"instance/{newfile}")
    for course in get_all_courses():
        app.logger.info(f"Deleting course: {course.name}")
        remove_class(course)
    for user in get_all_users():
        if user.requires_reverification:
            app.logger.info(f"Deleting user: {user.username}")
            delete_user(user)
    for user in get_all_users():
        user.requires_reverification = True
        db.session.commit()
    return success_response("New semester started."), 200