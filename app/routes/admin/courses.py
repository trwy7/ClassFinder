"""
Admin routes for managing courses.
"""
import shutil
import datetime
from flask import render_template, abort, request
from app import app
from app.utilities.users import require_login, require_role
from app.utilities.classes import get_course_by_id, remove_class, search_classes
from app.utilities.responses import success_response, error_response
from app.utilities.times import change_bell_delay, reset_bell_delay
from app.db import db

@app.route("/admin/class/<courseid>", methods=["DELETE"])
@require_login
@require_role(["admin"])
def delete_course(courseid):
    """
    Deletes a course.
    """
    course = get_course_by_id(courseid)
    if course:
        remove_class(course)
        return success_response("Course deleted."), 200
    return error_response("Course not found."), 404

@app.route("/admin/class/<courseid>/edit")
@require_login
@require_role(["admin"])
def edit_course(courseid):
    """
    Displays the edit course page.
    """
    course = get_course_by_id(courseid)
    if course:
        return render_template("admin/editcourse.html", course=course)
    app.logger.debug(f"Course not found: {courseid}")
    return abort(404)

@app.route("/admin/class/<courseid>/edit", methods=["POST"])
@require_login
@require_role(["admin"])
def edit_course_post(courseid):
    """
    Handles the edit course form submission.
    """
    course = get_course_by_id(courseid)
    if course:
        response = request.json
        course.name = response["name"]
        course.room = response["room"]
        course.campus_name = response["campusname"]
        course.canvasid = (
            response["canvasid"] if response["canvasid"].isdigit() else None
        )
        course.lunch = (
            response["lunch"] if response["lunch"] != "" else None
        )
        course.verified = True
        db.session.commit()
        return success_response("Course updated."), 200
    app.logger.debug(f"Course not found: {courseid}")
    return error_response("Course not found."), 404


@app.route("/admin/class/<courseid>/verify", methods=["POST"])
@require_login
@require_role(["admin"])
def verify_course(courseid):
    """
    Verifies a course.
    """
    course = get_course_by_id(courseid)
    if course:
        course.verified = True
        db.session.commit()
        app.logger.info(f"Course verified: {courseid}")
        return success_response("Course verified."), 200
    app.logger.debug(f"Course not found: {courseid}")
    return error_response("Course not found."), 404

@app.route("/admin/class/search")
@require_login
@require_role(["admin"])
def search_courses():
    """
    Searches for courses.
    """
    if not request.is_json:
        return render_template("searchcourses.html")
    query = request.json
    results = []
    for course in search_classes(**query):
        serialized = course.serialize()
        serialized.pop("teacher", None)
        results.append(serialized)
    return {"results": results}, 200

@app.route("/admin/bell-delay", methods=["POST"])
@require_login
@require_role(["admin"])
def modify_bell_delay():
    """
    Modifies the bell delay.
    """
    if not request.is_json:
        return error_response("Invalid request."), 400
    data = request.json
    if "delay" not in data:
        return error_response("Missing delay."), 400
    try:
        delay = float(data["delay"])
    except ValueError:
        return error_response("Invalid delay."), 400
    change_bell_delay(delay)
    return success_response(f"Bell delay changed by {delay} seconds."), 200

@app.route("/admin/reset-bell-delay", methods=["POST"])
@require_login
@require_role(["admin"])
def reset_bell_delay_route():
    """
    Resets the bell delay to zero.
    """
    reset_bell_delay()
    return success_response("Bell delay reset to zero."), 200