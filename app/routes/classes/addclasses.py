"""
This file contains the routes for adding classes to a user's account.
"""
import re
from flask import render_template, redirect, request, send_from_directory
from better_profanity import profanity
from app import app
from app.utilities.users import require_login
from app.utilities.classes import (
    add_class,
    add_user_to_class,
    check_if_class_exists,
    get_course,
    get_periods_of_user_classes,
    get_ptech_class,
    neededperiods,
)
from app.db import db
from app.utilities.config import campus_url
from app.utilities.responses import error_response, success_response

@app.route("/addclasses")
@require_login
def addclasses():
    """
    Checks if the user has all of their classes, and if not, renders the addclasses page.
    """
    user = request.user
    if len(get_periods_of_user_classes(user)) == len(neededperiods):
        app.logger.debug(
            f"User already has all of their classes. ({len(get_periods_of_user_classes(user))}/{len(neededperiods)})"
        )
        return redirect("/")
    return render_template(
        "addcourses.html",
        neededperiods=[
            period
            for period in neededperiods
            if period not in get_periods_of_user_classes(user)
        ],
        campus_url=campus_url
    )


@app.route("/addclasses", methods=["POST"])
@require_login
def addclasses_post():
    """
    Adds the classes to the user's account.
    """
    user = request.user
    if len(get_periods_of_user_classes(user)) == len(neededperiods):
        return error_response("You already have all of your classes."), 400
    classes = [
        course.strip() for course in request.json
        if "day: t" not in course.strip().lower()
        and "day: w" not in course.strip().lower()
        and "day: m" not in course.strip().lower()
        and "day: r" not in course.strip().lower()
        and "day: f" not in course.strip().lower()
        and "day: early release- blue" not in course.strip().lower()
        and "day: early release- gold" not in course.strip().lower()
        and course.strip() != ""
        and not course.strip().lower().startswith("start: ")
        and not course.strip().lower().startswith("end: ") # I have not confirmed this is a real value, but just in case
    ]
    app.logger.debug(f"Classes: {classes}")
    classes = re.findall(r"([0-9]|Access)\n *(.*)\n *(?:[0-9]{1,2}:[0-9]{1,2} (?:A|P)M(?: - )?){2}\n *Teacher: (.*), .*\n *Room: ((?:E?[0-9]{3}B?)|MS Cafe|PTECH|PTECH-[0-9]{3}|HS Commons)", "\n".join(classes), re.IGNORECASE)
    if len(classes) == 0:
        return error_response("No valid classes found. If you are on mobile, switch to a desktop browser when copying."), 400
    classes = list(set(classes))
    app.logger.debug(f"Filtered Classes: {classes}")
    had_periods = get_periods_of_user_classes(user)
    needed_periods = [
        period for period in neededperiods if period not in had_periods
    ]
    for class_info in classes:
        processed = process_class(class_info, user, needed_periods)
        if processed in [None, True]:
            continue
        return processed  # If an error response is returned, exit early
    return success_response(
        f"Added {len(classes)} classes to your account. You now have {len(get_periods_of_user_classes(user))} classes.",
    )

def process_class(class_info, user, needed_periods):
    """
    Processes a single class and adds it to the user's account.
    """
    period, course, teacher, room = class_info
    if period not in needed_periods:
        app.logger.debug(f"Skipping class {course} for period {period}, already added.")
        return None
    app.logger.debug(f"Processing class: {period}, {course}, {teacher}, {room}")
    if room.startswith("PTECH"):
        #course = "PTECH"
        room = "PTECH"
        pclass = get_ptech_class(course, period)
        if pclass:
            app.logger.debug(f"Adding existing PTECH class {pclass.name} to user {user.username}")
            add_user_to_class(user, pclass)
            return None
        app.logger.debug(f"Creating new PTECH class {course} for user {user.username}")
    elif check_if_class_exists(room, period):
        app.logger.debug(f"Class already exists for room {room} and period {period}, adding to user {user.username}")
        add_user_to_class(user, get_course(period, room))
        return None
    if profanity.contains_profanity(course):
        app.logger.warning(f"Profanity detected in course name: {course}")
        return error_response("Invalid class name"), 400
    app.logger.debug(f"Creating new class {course} for user {user.username}")
    nclass = add_class(course, period, room, user.id, teacher, course, commit=False)
    add_user_to_class(user, nclass)
    app.logger.debug(f"Added class {course} to user {user.username}")
    db.session.commit()
    return True

@app.route("/addclasses/help.gif")
def addclasses_help():
    """
    Renders the help gif for adding classes.
    """
    return send_from_directory("static", "addclasses.gif")
