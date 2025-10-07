"""
This file contains the route for the /canvas endpoint, which redirects the user to the Canvas course page.
"""
from flask import redirect, request
from app import app
from app.utilities.config import canvas_url
from app.utilities.classes import get_user_current_period
from app.utilities.users import require_login
from app.utilities.responses import error_response

valid_paths = ["assignments", "grades", "announcements", "discussions", "modules"]

@app.route("/canvas")
@require_login
def canvas():
    """
    Redirects the user to the Canvas course page.
    """
    user = request.user
    period = get_user_current_period(user)
    has_no_period = period is None
    has_no_course = period is not None and period["course"] is None
    has_no_canvas_id = period is not None and period["course"] is not None and period["course"].canvasid is None
    is_access = False
    if period is not None and period["course"] is not None:
        course_name_lower = period['course'].name.lower()
        is_access = "access" in course_name_lower or "study hall" in course_name_lower
    requires_redirect = has_no_period or has_no_course or (has_no_canvas_id and (not is_access or "ia" in request.args))
    if requires_redirect:
        reason = "no current period" if period is None else "no course for period" if period["course"] is None else "course has no Canvas ID"
        app.logger.debug(f"Redirecting user {user.username} to Canvas homepage: {reason}")
        return redirect(canvas_url)
    app.logger.debug(f"Redirecting user {user.username} to Canvas course {period['course'].canvasid}")
    return redirect(f"{canvas_url}/courses/{period['course'].canvasid}")


@app.route("/canvas/<path>")
@require_login
def canvas_with_path(path):
    """
    Redirects the user to the Canvas course page with a path
    """
    user = request.user
    period = get_user_current_period(user)
    if period is None or period["course"] is None or period["course"].canvasid is None:
        reason = "no current period" if period is None else "no course for period" if period["course"] is None else "course has no Canvas ID"
        app.logger.debug(f"Redirecting user {user.username} to Canvas homepage: {reason}")
        return redirect(f"{canvas_url}/")
    app.logger.debug(f"Redirecting user {user.username} to Canvas course {period['course'].canvasid} with path {path}")
    if path not in valid_paths:
        app.logger.debug(f"Invalid path {path}")
        return error_response("Invalid path", {"valid_paths": valid_paths}), 400
    return redirect(f"{canvas_url}/courses/{period['course'].canvasid}/{path}")
