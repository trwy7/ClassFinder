"""
Allows getting data of a user. Used differently from /export as this is to be used by scoped tokens to get user data.
"""

from flask import request
from app import app
from app.utilities.users import require_login, require_scopes
from app.utilities.responses import success_response

@app.route("/api/v2/data", methods=["GET"])
@require_login
@require_scopes([])
def get_user_data():
    """
    Allows getting data of a user. Used differently from /export as this is to be used by scoped tokens to get user data.
    """
    return_data = {"id": request.user.id}
    token_scopes = request.token.scopes.split(" ") if request.token.scopes is not None else None
    return_data["token_scopes"] = token_scopes
    allow_all = token_scopes is None
    if allow_all or "read-username" in token_scopes:
        return_data["username"] = request.user.username
    if allow_all or "read-email" in token_scopes:
        return_data["email"] = request.user.email
    if allow_all or "read-classes" in token_scopes:
        return_data["classes"] = sorted([
            {
                "name": course.campus_name,
                "displayname": course.name,
                "room": course.room,
                "period": course.period,
                "lunch": course.lunch,
                "canvasid": course.canvasid,
                "verified": course.verified,
                "teacher": course.teacher if allow_all else None,
            }
            for course in request.user.classes
        ], key=lambda x: x["period"])
    if allow_all or "read-misc" in token_scopes:
        return_data["created_at"] = round(request.user.created_at.timestamp())
        return_data["created_by"] = request.user.created_by
        return_data["requires_username_change"] = request.user.requires_username_change
        return_data["role"] = request.user.role
    if allow_all:
        return_data["sessions"] = [
            {
                "token": session.token[:8],
                "type": session.type,
                "expire_on": round(session.expire.timestamp()) if session.expire is not None else None,
                "scopes": session.scopes.split(" ") if session.scopes is not None else None,
                "granted_to": session.granted_to,
            }
            for session in request.user.tokens
        ]
    return success_response("User data retrieved successfully", return_data)
