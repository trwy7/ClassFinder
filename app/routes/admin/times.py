"""
This file contains the routes for the admin schedule times page.
"""
from datetime import datetime
from flask import render_template, request
from app import app
from app.db import Schedule, db
from app.utilities.times import set_schedule, readable_days
from app.utilities.users import require_login, require_role
from app.utilities.responses import success_response, error_response


@app.route("/admin/times/schedule")
@require_login
@require_role(["admin"])
def schedule():
    """
    This route displays the schedule times page.
    """
    return render_template("schedule.html", schedules=Schedule.query.all(), readable_days=readable_days)


@app.route("/admin/times/schedule", methods=["POST"])
@require_login
@require_role(["admin"])
def schedule_post():
    """
    This route handles the schedule times form submission.
    """
    start = datetime.strptime(request.json.get("start"), "%Y-%m-%d").date()
    end = datetime.strptime(request.json.get("end"), "%Y-%m-%d").date()
    day = int(request.json.get("day"))
    app.logger.info(f"Received schedule request for {start} to {end} with day {day}")
    set_schedule(start, end, day)
    return success_response("Schedule set")

@app.route("/admin/times/schedule/<day>", methods=["DELETE"])
@require_login
@require_role(["admin"])
def schedule_delete(day):
    """
    This route deletes a schedule for a specific day.
    """
    app.logger.info(f"Deleting schedule for {day}")
    newday = datetime.strptime(day, "%Y-%m-%d").date()
    newschedule = Schedule.query.filter_by(day=newday).first()
    if newschedule:
        db.session.delete(newschedule)
        db.session.commit()
    else:
        return error_response("Schedule not found"), 404
    return success_response("Schedule deleted")
