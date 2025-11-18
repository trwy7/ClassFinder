import datetime
from flask import Response, request, render_template
from app import app
from app.utilities.users import require_login
from app.db import User, db
from app.utilities.config import devmode
from app.utilities.responses import error_response, success_response

light_warm_color = """
@media (prefers-color-scheme: light) {
    :root {
        --secondary-text-color: black;
    }
}
"""

@app.route("/color<int:color>.css")
@app.route("/color.css")
def color_css(color: int = None):
    """
    Serves the color CSS file.
    """
    # If the user has a color, we add it to the CSS
    if color is None:
        color = 234 if devmode else 155
    color = str(color)
    if request.cookies.get("color_hue"):
        color = request.cookies.get("color_hue")
    if not (color.isdigit() and 0 <= int(color) <= 360):
        color = "234" if devmode else "155"
    return Response(
        f":root {{ --user-prefered-color: {color}; }}" +
        (light_warm_color if 32 <= int(color) <= 188 else ""),
        mimetype="text/css"
    )

@app.route("/user.css")
@require_login
def user_css():
    """
    Serves the user's custom CSS.
    """
    return Response(request.user.custom_css, mimetype="text/css")

@app.route("/resetcss")
@app.route("/account/resetcss")
@require_login
def reset_user_css_get():
    """
    Asks the user to confirm resetting their custom CSS.
    """
    return render_template("account/reset_css.html")

@app.route("/account/resetcss", methods=["POST"])
@require_login
def reset_user_css_post():
    """
    Resets the user's custom CSS.
    """
    request.user.custom_css = None
    request.user.custom_css_last_updated = None
    db.session.commit()
    return success_response("Custom CSS reset successfully.")

@app.route("/account/setcss", methods=["POST"])
@require_login
def set_user_css_post():
    """
    Sets the user's custom CSS.
    """
    data = request.get_json()
    css = data.get("css", "").strip(" \t\n\r")
    if not css:
        request.user.custom_css = None
        request.user.custom_css_last_updated = None
        db.session.commit()
        return success_response("Custom CSS cleared successfully.")
    if not isinstance(css, str) or len(css) > 25000:
        return error_response("Invalid CSS provided. Make sure it's a string and less than 25,000 characters.")
    request.user.custom_css = css
    request.user.custom_css_last_updated = datetime.datetime.now().timestamp()
    db.session.commit()
    return success_response("Custom CSS updated successfully.")
