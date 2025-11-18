from app import app
from flask import Response, request
from app.utilities.config import devmode

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