"""
This file is used for plain API endpoints, for applications like cURL
"""
import datetime
from flask import request
from app import app
from app.utilities.users import require_login
from app.utilities.classes import get_user_current_period

@app.route("/api/plain/endtime")
@require_login
def api_plain_endtime():
    """
    Returns the end time for the current period.
    """
    user = request.user
    period = get_user_current_period(user)
    end_time = period.get('end')
    if end_time:
        return datetime.datetime.combine(datetime.date.today(), end_time).timestamp()
    return "0"

@app.route("/api/plain/timeuntilclassend")
@require_login
def api_plain_timeuntilclassend():
    """
    Returns the time until the current class ends.
    """
    user = request.user
    period = get_user_current_period(user)
    if period:
        return str(int((datetime.datetime.combine(datetime.date.today(), period.get('end')) - datetime.datetime.now()).total_seconds()))
    return "0"
