"""
This file contains the route for setting the lunch period for a class.
"""
from flask import request, render_template
from app import app
from app.utilities.users import require_login
from app.utilities.classes import set_lunch, get_course_by_id
from app.utilities.responses import success_response, error_response

@app.route("/class/<courseid>/setlunch")
@require_login
def setlunch(courseid):
    """
    Renders the setlunch page.
    """
    course = get_course_by_id(courseid)
    if not course:
        return error_response("Course not found."), 404
    return render_template("setlunch.html", course=course)

@app.route("/class/<courseid>/setlunch", methods=["POST"])
@require_login
def setlunch_post(courseid):
    """
    Sets the lunch period for a class.
    """
    user = request.user
    course = get_course_by_id(courseid)
    if course not in user.classes:
        return error_response("Course not found."), 404
    lunch = request.json.get("lunch")
    if lunch in ["A", "B", "C"]:
        set_lunch(course, lunch)
        return success_response("Lunch set."), 200
    app.logger.debug(f"Invalid lunch period: {lunch}")
    return error_response("Invalid lunch period."), 400
