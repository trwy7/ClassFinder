"""
This file contains the routes for linking the user's classes to canvas courses.
"""
import requests
from flask import render_template, request, redirect, url_for
from app import app
from app.utilities.users import require_login
from app.utilities.classes import set_canvas_id
from app.utilities.responses import success_response
from app.utilities.config import canvas_url
from app.addons.limiter import limiter

@app.route("/classes/canvaslink")
@limiter.limit("4/minute", exempt_when=lambda: request.args.get("token") is None)
@require_login
def canvaslink():
    """
    Asks the user to link their classes to canvas courses.
    """
    user = request.user
    newcourses = []
    for course in user.classes:
        app.logger.debug(
            f"Checking if course {course.name} is linked to a canvas course."
        )
        if course.canvasid is None:
            app.logger.debug(f"Course {course.name} is not linked to a canvas course.")
            newcourses.append(course)
            if request.args.get("token") is None:
                return render_template("canvasaskfortoken.html", canvas_url=canvas_url)
        else:
            app.logger.debug(
                f"Course {course.name} is already linked to a canvas course: {course.canvasid}"
            )
    if len(newcourses) == 0:
        app.logger.debug(f"User {user.username} has no courses to link to canvas.")
        return redirect(url_for("dashboard"))
    try:
        cards = requests.get(
            f"{canvas_url}/api/v1/dashboard/dashboard_cards",
            headers={"Authorization": f'Bearer {request.args.get("token")}'},
            timeout=5,
        )
    except requests.exceptions.Timeout:
        app.logger.error("Request to Canvas API timed out.")
        return render_template("canvasaskfortoken.html", canvas_url=canvas_url, error="Request to Canvas API timed out.")
    app.logger.debug(cards.text)
    if cards.status_code != 200:
        return redirect(url_for("canvaslink"))
    newcards = {}
    ids_for_existing_courses = []
    for course in user.classes:
        if course.canvasid is not None:
            ids_for_existing_courses.append(course.canvasid)
    for card in cards.json():
        if card["id"] in ids_for_existing_courses:
            continue
        newcards[card["id"]] = card["shortName"]
    return render_template("canvaslink.html", courses=newcourses, cards=newcards)

@app.route("/classes/canvaslink", methods=["POST"])
@limiter.limit("2/minute")
@require_login
def canvaslink_post():
    """
    Links the user's classes to canvas courses.
    """
    user = request.user
    token = request.args.get("token")
    for course in user.classes:
        if course.canvasid is None:
            if request.json.get(str(course.id)) is not None:
                if request.json.get(str(course.id)).isdigit():
                    set_canvas_id(course, request.json.get(str(course.id)))
                else:
                    app.logger.debug(
                        f"Course {course.name} was not linked to a canvas course by {user.username} because the canvas course id was not a number."
                    )
            else:
                app.logger.debug(
                    f"Course {course.name} was not linked to a canvas course by {user.username}"
                )
        else:
            app.logger.debug(
                f"Course {course.name} is already linked to a canvas course: {course.canvasid}"
            )
    if isinstance(token, str):
        requests.delete(
            f"{canvas_url}/login/oauth2/token",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
    return success_response("Courses linked successfully."), 200
