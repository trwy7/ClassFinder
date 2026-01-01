from datetime import datetime, timezone
from flask import jsonify, request
from app import app
from app.utilities.users import require_login
from app.utilities.config import canvas_url

@app.route('/api/v2/server-time')
def api_server_time():
    """
    Allows clients to sync their time with the server, as some devices may have incorrect time settings.
    """
    return jsonify(time=int(datetime.now(timezone.utc).timestamp()*1000))

@app.route("/api/v2/chronisconfig")
@require_login
def chronis_config():
    """
    Returns configuration data for the service worker.
    More fields may be added in the future, when requested/needed.
    """
    return jsonify({
        "canvas_url": canvas_url,
        "color_hue": request.user.color_hue
    })