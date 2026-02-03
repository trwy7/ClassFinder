"""
Module to handle account settings routes.
"""
from flask import request
from app import app
from app.utilities.users import require_login, set_custom_delays

@app.route('/account/set_delays', methods=['POST'])
@require_login
def set_account_delays():
    """
    Set custom start and end delays for the user's schedule.
    """
    set_custom_delays(request.user, request.json.get('start_delay'), request.json.get('end_delay'))
    return {"status": "success"}