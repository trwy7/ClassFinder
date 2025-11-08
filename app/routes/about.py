"""
About route, shows basic info about the site.
"""

from datetime import datetime
from flask import render_template
from app import app
from app.utilities.config import devmode
from app.utilities.users import get_user_count, require_logged_out
from app.utilities.classes import get_current_period


@app.route("/")
@require_logged_out
def index():
    """
    Index route, redirects to dashboard if user is logged in, shows basic info about the site.
    """
    currentperiod = get_current_period()
    app.logger.debug(f"Current period end time: {currentperiod['end'] if currentperiod else 'None'}")
    return render_template("index.html", devmode=devmode, user_count=get_user_count(), endtime=None if (currentperiod is None) else int(datetime.combine(datetime.today(), currentperiod['end']).timestamp()))

@app.route("/about")
def about():
    """
    About route, shows basic info about the site.
    """
    currentperiod = get_current_period()
    app.logger.debug(f"Current period end time: {currentperiod['end'] if currentperiod else 'None'}")
    return render_template("about.html", devmode=devmode, endtime=None if (currentperiod is None) else int(datetime.combine(datetime.today(), currentperiod['end']).timestamp()))