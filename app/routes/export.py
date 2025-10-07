"""
Allows exporting user data to json.
"""

from datetime import datetime
from flask import request
from app import app
from app.utilities.users import require_login
from app.utilities.responses import success_response


@app.route("/export")
@require_login
def export():
    """
    This route allows the user to export their data.
    """
    user = request.user
    return success_response("Export complete", {
        "username": user.username,
        "email": user.email,
        "classes": sorted([
            {
                "name": course.name,
                "room": course.room,
                "period": course.period,
                "lunch": course.lunch,
                "canvasid": course.canvasid
            }
            for course in user.classes
        ], key=lambda x: x["period"]),
        "created_at": user.created_at,
        "created_by": user.created_by,
        "role": user.role,
        "requires_username_change": user.requires_username_change,
        "sessions": [
            {
                "token": token.token[:5] + "*" * (len(token.token) - 5),
                "type": token.type,
                "expiry": int(datetime.timestamp(token.expire)),
                "scopes": token.scopes.split(" ") if token.scopes is not None else None

            }
            for token in user.tokens
        ]
    })
