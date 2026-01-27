"""
This file contains the route for exporting a schedule to a PDF.
"""
from flask import request, send_file, render_template
from app import app
from app.utilities.times import create_schedule_pdf

@app.route("/classes/exportschedule", methods=["GET"])
def exportpdf():
    """
    Shows PDF export options.
    """
    user = request.user
    return render_template("pdf.html", user=user)

@app.route("/classes/schedulepdf", methods=["GET"])
def schedulepdf():
    """
    Exports the user's schedule to a PDF.
    """
    user = request.user
    return send_file(create_schedule_pdf(user), download_name="schedule.pdf")

@app.route("/classes/schedulepdf/<days>", methods=["GET"])
def schedulepdfday(days):
    """
    Exports the user's schedule to a PDF for specific days.
    """
    user = request.user
    if days == "all":
        ndays = "0,1,2,3,4,7,8"
    else:
        ndays = days.lower().replace("monday", "0").replace("tuesday", "1").replace("wednesday", "2").replace("thursday", "3").replace("friday", "4").replace("eb", "7").replace("eg", "8") #pylint: disable=line-too-long
    return send_file(create_schedule_pdf(
        user=user if 'nopersonal' not in request.args else None,
        days=[int(day) for day in ndays.split(",")],
        separate='separate' in request.args,
        showclass='noclass' not in request.args,
        showroom='noroom' not in request.args,
        showtime='notime' not in request.args,
        showlunch='nolunch' not in request.args,
        smalltext='smalltext' in request.args,
        showperiod='noperiod' not in request.args,
    ), download_name="schedule.pdf")
