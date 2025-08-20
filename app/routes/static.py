# pylint: disable=missing-function-docstring
"""
Static routes for the application.
"""
import os
from flask import Response, request
from flask import send_from_directory, render_template
from app import app
from app.utilities.config import devmode
from app.utilities.users import verify_user
from app.addons.limiter import limiter

def load_css():
    """
    Loads the CSS file.
    """
    with open(os.path.join(app.static_folder, "index.css"), "r", encoding="UTF-8") as f:
        return f.read()

index_css = load_css()

@app.route("/index.css")
@verify_user(required=False)
def index_cssf():
    """
    Serves the index.css file.
    """
    global index_css
    if request.user and request.user.color_hue:
        # If the user has a color, we add it to the CSS
        color_hue = request.user.color_hue
        if devmode:
            index_css = load_css()
        return Response(index_css + f"\n:root {{ --user-prefered-color: {color_hue}; }}", mimetype="text/css")
    return send_from_directory("static", "index.css")

@app.route("/favicon.ico")
def favicon():
    """
    Serves the favicon.
    """
    return send_from_directory("static", "favicondev.ico" if devmode else "favicon.ico")

@app.route("/privacy")
def privacy():
    """
    Serves the privacy policy.
    """
    return render_template("privacy.html")

@app.route("/ping")
@limiter.limit("3 per second")
def ping():
    """
    Pings the server.
    """
    return "Pong"

@app.route("/robots.txt")
def robots():
    """
    Returns a robots.txt.
    """
    return """
        User-agent: *
        Disallow: /
    """ # There is no reason to allow robots to index this site, as it is not a public site.
