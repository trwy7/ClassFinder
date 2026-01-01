"""
Handles the timer page
"""
import os
from datetime import datetime
from flask import render_template, request
from app import app
from app.utilities.classes import get_user_current_period, get_current_period

valid_versions = []
valid_notimes = []
for file in os.listdir(os.path.join(app.root_path, app.template_folder, 'timers')):
    if file.endswith('.html') and file.startswith('timer_'):
        try:
            version_num = int(file.removeprefix('timer_').removesuffix('.html'))
            valid_versions.append(version_num)
            if os.path.exists(os.path.join(app.root_path, app.template_folder, 'timers', f'notime_{version_num}.html')):
                valid_notimes.append(version_num)
        except ValueError:
            continue

@app.route('/timer')
@app.route('/timer/')
@app.route('/timer/<int:version>')
def timer(version=1):
    """
    Handles the timer page
    """
    if version not in valid_versions:
        return render_template("templates/error.html", status_code=404, error_message="That timer does not exist. You may use: " + ", ".join([str(i) for i in valid_versions])), 404

    user = request.user

    current_period = get_user_current_period(user) if user and (not request.args.get('genericMode') == "true") else get_current_period()

    if current_period is None:
        # if request.args.get('noredirect', "false") != "false" or request.args.get('genericMode') == "true" or (not user):
        return render_template(f'timers/notime_{version}.html' if version in valid_notimes else 'timers/ntbase.html', period=None)

    app.logger.debug(f"User: {user}")

    period_start = datetime.combine(datetime.today(), current_period['start'])
    period_end = datetime.combine(datetime.today(), current_period['end'])
    
    return render_template(
        f'timers/timer_{version}.html',
        period_end=int(period_end.timestamp() * 1000),
        period_start=int(period_start.timestamp() * 1000),
        current_epoch=int(datetime.now().timestamp() * 1000),
        period=current_period
    )

@app.route('/timers.json')
def timers_json():
    """
    Returns a list of valid timer versions
    """
    return valid_versions