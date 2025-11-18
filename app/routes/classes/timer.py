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

# @app.route('/timer')
# @app.route('/timer/')
# def timer():
#     """
#     Handles the timer page
#     """
#     user = request.user
#     app.logger.debug(f"User: {user}")
#     # Determine server local timezone once
#     local_tz = datetime.now().astimezone().tzinfo
#     app.logger.debug(request.args.get('noredirect', "false"))
#     if user is None:
#         period = get_current_period()
#         if period is None:
#             if request.args.get('noredirect', "false") != "false":
#                 return render_template('timer.html', nextclass="nothing", period=None)
#             return redirect(url_for('dashboard'))
#         end_dt = datetime.combine(datetime.now().date(), period['end']).replace(tzinfo=local_tz)
#         start_dt = datetime.combine(datetime.now().date(), period['start']).replace(tzinfo=local_tz)
#         end_readable = end_dt.strftime('%I:%M %p')
#         seconds_left = max(0, int((end_dt - datetime.now(local_tz)).total_seconds()))
#         hours = seconds_left // 3600
#         minutes = (seconds_left % 3600) // 60
#         seconds = seconds_left % 60
#         if hours > 0:
#             time_left_readable = f"{hours}h{minutes}m{seconds}s"
#         elif minutes > 0:
#             time_left_readable = f"{minutes}m{seconds}s"
#         else:
#             time_left_readable = f"{seconds}s"
#         # formatted_end_time = end_dt.strftime('%m/%d/%Y %I:%M:%S %p')
#         # formatted_start_time = start_dt.strftime('%m/%d/%Y %I:%M:%S %p')
#         end_time_unix_seconds = int(end_dt.timestamp()*1000)
#         start_time_unix_seconds = int(start_dt.timestamp()*1000)
#         response = make_response(render_template(
#             'timer.html',
#             nextclass=end_time_unix_seconds,
#             startclass=start_time_unix_seconds,
#             current_epoch=int(datetime.now().timestamp()*1000),
#             status=status,
#             period=period,
#             user=None,
#             redirect=request.args.get('noredirect', "false") == "false",
#             end_readable=end_readable,
#             time_left_readable=time_left_readable
#         ))
#         return response
#     period = get_user_current_period(user)
#     if period is None:
#         if request.args.get('noredirect', "false") != "false":
#             return render_template('timer.html', nextclass="nothing", period=None)
#         return redirect(url_for('dashboard'))
#     end_dt = datetime.combine(datetime.now().date(), period['end']).replace(tzinfo=local_tz)
#     start_dt = datetime.combine(datetime.now().date(), period['start']).replace(tzinfo=local_tz)
#     # formatted_end_time = end_dt.strftime('%m/%d/%Y %I:%M:%S %p')
#     # formatted_start_time = start_dt.strftime('%m/%d/%Y %I:%M:%S %p')
#     end_time_unix_seconds = int(end_dt.timestamp()*1000)
#     start_time_unix_seconds = int(start_dt.timestamp()*1000)
#     end_readable = end_dt.strftime('%I:%M %p')
#     seconds_left = max(0, int((end_dt - datetime.now(local_tz)).total_seconds()))
#     hours = seconds_left // 3600
#     minutes = (seconds_left % 3600) // 60
#     seconds = seconds_left % 60
#     if hours > 0:
#         time_left_readable = f"{hours}h{minutes}m{seconds}s"
#     elif minutes > 0:
#         time_left_readable = f"{minutes}m{seconds}s"
#     else:
#         time_left_readable = f"{seconds}s"

#     # seconds_until_end_readable = f"{seconds_left} seconds"
#     response = make_response(render_template(
#         'timer.html',
#         nextclass=end_time_unix_seconds,
#         startclass=start_time_unix_seconds,
#         current_epoch=int(datetime.now().timestamp()*1000),
#         status=status,
#         period=period,
#         user=user,
#         redirect=request.args.get('noredirect', "false") == "false",
#         end_readable=end_readable,
#         time_left_readable=time_left_readable
#     ))
#     return response

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
