from datetime import datetime, timezone
from flask import jsonify
from app import app

@app.route('/api/v2/server-time')
def api_server_time():
    """
    Allows clients to sync their time with the server, as some devices may have incorrect time settings.
    """
    return jsonify(time=int(datetime.now(timezone.utc).timestamp()*1000))