"""
This file has the legacy class API endpoints
"""
from datetime import datetime
from flask import jsonify, request
from app import app
from app.utilities.users import require_login
from app.utilities.classes import get_user_current_period, get_today_courses, get_current_period

@app.route('/api/v1/currentcourses/', methods=['GET'])
@require_login
def apicurrentcourses():
    """
    Returns the current courses for the user.
    """
    user = request.user
    currentperiod = get_user_current_period(user)
    today = get_today_courses(user)
    return jsonify({
        'status': 'success',
        'courses': {
            c.period: {
                'id': c.id,
                'name': c.name,
                'room': c.room,
                'lunch': c.lunch,
                'verified': c.verified,
                'canvasid': c.canvasid
            } for c in today
        },
        'currentperiod': currentperiod['period'] if currentperiod is not None else None,
        'nextclass': int(datetime.combine(datetime.today(), currentperiod['end']).timestamp()) if (currentperiod is not None) else None,
        'dayoff': today == [] or today is None #pylint: disable=use-implicit-booleaness-not-comparison
    })

@app.route('/api/v1/currentperiod/', methods=['GET'])
def apicurrentperiod():
    """
    Returns the current period for the user.
    """
    user = request.user
    currentperiod = get_user_current_period(user) if user is not None else get_current_period()
    response = jsonify({
        'status': 'success',
        'currentperiod': currentperiod['period'] if currentperiod is not None else None,
        'nextclass': int(datetime.combine(datetime.today(), currentperiod['end']).timestamp()) if (currentperiod is not None) else None,
    })
    return response
