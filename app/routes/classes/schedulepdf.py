"""
This file contains the route for exporting a schedule to a PDF.
"""
from flask import request, send_file
from app import app
from app.utilities.times import create_schedule_pdf
from app.utilities.users import require_login

@app.route("/classes/schedulepdf", methods=["GET"])
@require_login
def schedulepdfday():
    """
    Exports the user's schedule to a PDF for specific days.
    """
    return send_file(create_schedule_pdf(user=request.user), download_name="schedule.pdf")
