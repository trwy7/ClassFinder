"""
This file contains the routes for the class API endpoints.
These endpoints are used to get information about the user's classes and schedule.
"""
from datetime import datetime
from flask import request
from app import app
from app.utilities.users import require_login, require_scopes
from app.utilities.classes import get_user_current_period, get_today_courses, get_current_period
from app.utilities.times import get_day_schedule
from app.utilities.responses import success_response, error_response

@app.route("/api/v2/classes/current")
@require_login
@require_scopes([["read-classes"]])
def current_classes():
    """
    Returns the current classes for the user.
    """
    user = request.user
    currentperiod = get_user_current_period(user)
    app.logger.debug(f"Current period: {currentperiod}")
    return success_response(None, {
        "classes": {
            c.period: {
                "id": c.id,
                "displayname": c.name,
                "name": c.campus_name,
                "room": c.room,
                "lunch": c.lunch,
                "verified": c.verified,
                "canvasid": c.canvasid,
                "teacher": c.teacher
            } for c in get_today_courses(user)
        },
        "period": currentperiod.period if currentperiod is not None else None,
        "endtime": int(datetime.combine(datetime.today(), currentperiod.end).timestamp()) if (currentperiod is not None) else None,
        "passing": currentperiod.passing if currentperiod is not None else None,
        "lunch": currentperiod.lunch if currentperiod is not None else None
    })

@app.route("/api/v2/classes/all")
@require_login
@require_scopes([["read-classes"]])
def all_classes():
    """
    Returns all classes for the user.
    """
    user = request.user
    return success_response(None, {
        "classes": {
            c.id: {
                "displayname": c.name,
                "name": c.campus_name,
                "room": c.room,
                "period": c.period,
                "lunch": c.lunch,
                "verified": c.verified,
                "canvasid": c.canvasid,
                "teacher": c.teacher
            } for c in user.classes
        }
    })

@app.route("/api/v2/classes/timeuntilend")
def time_until_end():
    """
    Returns the time until the end of the current period.
    """
    currentperiod = get_current_period()
    return success_response(None, {
        "time": int(datetime.combine(datetime.today(), currentperiod.end).timestamp()) if (currentperiod is not None) else None,
        "passing": currentperiod.passing if currentperiod is not None else None,
        "period": currentperiod.period if currentperiod is not None else None
    })

@app.route("/api/v2/schedule/today")
@app.route("/api/v2/schedule/<string:date>")
def schedule_today(date=None):
    """
    Returns the user's schedule for today.
    """
    user = request.user
    if date is not None:
        try:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return error_response("Invalid date format. Use YYYY-MM-DD."), 400
    app.logger.debug(f"Fetching schedule for user {user.username if user else 'guest'} on date {date if date else 'today'}")
    schedule = get_day_schedule(user=user, day=date)
    app.logger.debug({
        "schedule": [
            {
                "start": datetime.combine(date if date is not None else datetime.today().date(), entry.start).timestamp(),
                "end": datetime.combine(date if date is not None else datetime.today().date(), entry.end).timestamp(),
                "period": entry.period,
                "passing": entry.passing,
                "lunchactive": entry.lunchactive,
                "class": {
                    "id": entry.course.id,
                    "displayname": entry.course.name,
                    "name": entry.course.campus_name,
                    "room": entry.course.room,
                    "period": entry.course.period,
                    "lunch": entry.course.lunch,
                    "verified": entry.course.verified,
                    "canvasid": entry.course.canvasid,
                    "teacher": entry.course.teacher
                } if bool(entry.course) else None
            } for entry in schedule
        ]
    })
    # TODO: Move this to a utility function to avoid duplication across get_current_period, the calendar, and here
    return success_response(None, {
        "schedule": [
            {
                "start": datetime.combine(date if date is not None else datetime.today().date(), entry.start).timestamp(),
                "end": datetime.combine(date if date is not None else datetime.today().date(), entry.end).timestamp(),
                "period": entry.period,
                "passing": entry.passing,
                "lunchactive": entry.lunchactive,
                "class": {
                    "id": entry.course.id,
                    "displayname": entry.course.name,
                    "name": entry.course.campus_name,
                    "room": entry.course.room,
                    "period": entry.course.period,
                    "lunch": entry.course.lunch,
                    "verified": entry.course.verified,
                    "canvasid": entry.course.canvasid,
                    "teacher": entry.course.teacher
                } if entry.course is not None else None
            } for entry in schedule
        ]
    })