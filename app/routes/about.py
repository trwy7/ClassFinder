"""
About route, shows basic info about the site.
"""

from flask import render_template, redirect, request
from app import app
from app.utilities.config import devmode
from app.utilities.users import get_user_count, require_logged_out


@app.route("/")
@require_logged_out
def index():
    """
    Index route, redirects to dashboard if user is logged in, shows basic info about the site.
    """
    return render_template("index.html", devmode=devmode, user_count=get_user_count())
