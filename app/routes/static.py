# pylint: disable=missing-function-docstring
"""
Static routes for the application.
"""
import re
import os
from flask import Response, request
from flask import send_from_directory, render_template
from app import app
from app.utilities.config import devmode
from app.addons.limiter import limiter
from app.utilities.other import optimize_css

def load_css():
    """
    Loads the CSS file.
    """
    with open(os.path.join(app.static_folder, "index.css"), "r", encoding="UTF-8") as f:
        return f.read()

index_css = load_css()
if not devmode:
    if os.path.exists("/tmp/chroniscache"):
        app.logger.debug("Clearing chroniscache directory")
        for file in os.listdir("/tmp/chroniscache"):
            app.logger.debug(f"Removing cached file: {file}")
            os.remove(os.path.join("/tmp/chroniscache", file))
    else:
        os.mkdir("/tmp/chroniscache")

    # Create optimized CSS version
    optimized_css_path = "/tmp/chroniscache/optimized_index.css"
    if not os.path.exists(optimized_css_path):
        optimized_css = optimize_css(index_css)
        with open(optimized_css_path, "w", encoding="UTF-8") as f:
            f.write(optimized_css)
        app.logger.debug("Created optimized CSS file.")

@app.route("/index.css")
def index_cssf():
    """
    Serves the index.css file.
    """
    global index_css
    ua = (request.headers.get("User-Agent") or "").lower()
    app.logger.debug(f"User-Agent: {ua}")
    m = re.search(r"os (\d+)[_.]", ua)
    if ((m and any(x in ua for x in ("iphone", "ipad", "ipod", "cpu"))) or "wiiu" in ua or "3ds" in ua or "msie" in ua or "trident" in ua or "iemobile" in ua):
        try:
            if (not m) or int(m.group(1)) <= 8:
                return send_from_directory("static", "legacycss.css")
        except ValueError:
            pass

    return send_from_directory("/tmp/chroniscache", "optimized_index.css") if not devmode else Response(optimize_css(load_css()), mimetype="text/css")

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
