"""
Allows administrators to view logs.
"""
from flask import request
from app import app, get_logs, get_request_logs
from app.utilities.users import require_login, require_role

@app.route("/api/v2/logs", methods=["GET"])
@require_login
@require_role(["admin"])
def get_logs_route():
    """
    Returns the logs of the application.
    """
    app.logger.info(f"{request.user.username} requested logs")
    logs = get_logs()
    return logs, 200

@app.route("/api/v2/request_logs", methods=["GET"])
@require_login
@require_role(["admin"])
def get_request_logs_route():
    """
    Returns the request logs of the application.
    """
    app.logger.info(f"{request.user.username} requested request logs")
    logs = get_request_logs()
    return logs, 200
