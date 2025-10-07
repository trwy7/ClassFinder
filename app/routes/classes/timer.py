"""
Handles the timer page
"""
from datetime import datetime
from flask import render_template, url_for, redirect, request, make_response
from app import app
from app.utilities.config import status
from app.utilities.classes import get_user_current_period, get_current_period

@app.route('/timer')
@app.route('/timer/')
def timer():
    """
    Handles the timer page
    """
    user = request.user
    app.logger.debug(f"User: {user}")
    # Determine server local timezone once
    local_tz = datetime.now().astimezone().tzinfo
    app.logger.debug(request.args.get('noredirect', "false"))
    if user is None:
        period = get_current_period()
        if period is None:
            if request.args.get('noredirect', "false") != "false":
                return render_template('timer.html', nextclass="nothing", period=None)
            return redirect(url_for('dashboard'))
        end_dt = datetime.combine(datetime.now().date(), period['end']).replace(tzinfo=local_tz)
        start_dt = datetime.combine(datetime.now().date(), period['start']).replace(tzinfo=local_tz)
        end_readable = end_dt.strftime('%I:%M %p')
        seconds_left = max(0, int((end_dt - datetime.now(local_tz)).total_seconds()))
        hours = seconds_left // 3600
        minutes = (seconds_left % 3600) // 60
        seconds = seconds_left % 60
        if hours > 0:
            time_left_readable = f"{hours}h{minutes}m{seconds}s"
        elif minutes > 0:
            time_left_readable = f"{minutes}m{seconds}s"
        else:
            time_left_readable = f"{seconds}s"
        # formatted_end_time = end_dt.strftime('%m/%d/%Y %I:%M:%S %p')
        # formatted_start_time = start_dt.strftime('%m/%d/%Y %I:%M:%S %p')
        end_time_unix_seconds = int(end_dt.timestamp()*1000)
        start_time_unix_seconds = int(start_dt.timestamp()*1000)
        response = make_response(render_template(
            'timer.html',
            nextclass=end_time_unix_seconds,
            startclass=start_time_unix_seconds,
            current_epoch=int(datetime.now().timestamp()*1000),
            status=status,
            period=period,
            user=None,
            redirect=request.args.get('noredirect', "false") == "false",
            end_readable=end_readable,
            time_left_readable=time_left_readable
        ))
        return response
    period = get_user_current_period(user)
    if period is None:
        if request.args.get('noredirect', "false") != "false":
            return render_template('timer.html', nextclass="nothing", period=None)
        return redirect(url_for('dashboard'))
    end_dt = datetime.combine(datetime.now().date(), period['end']).replace(tzinfo=local_tz)
    start_dt = datetime.combine(datetime.now().date(), period['start']).replace(tzinfo=local_tz)
    # formatted_end_time = end_dt.strftime('%m/%d/%Y %I:%M:%S %p')
    # formatted_start_time = start_dt.strftime('%m/%d/%Y %I:%M:%S %p')
    end_time_unix_seconds = int(end_dt.timestamp()*1000)
    start_time_unix_seconds = int(start_dt.timestamp()*1000)
    end_readable = end_dt.strftime('%I:%M %p')
    seconds_left = max(0, int((end_dt - datetime.now(local_tz)).total_seconds()))
    hours = seconds_left // 3600
    minutes = (seconds_left % 3600) // 60
    seconds = seconds_left % 60
    if hours > 0:
        time_left_readable = f"{hours}h{minutes}m{seconds}s"
    elif minutes > 0:
        time_left_readable = f"{minutes}m{seconds}s"
    else:
        time_left_readable = f"{seconds}s"

    seconds_until_end_readable = f"{seconds_left} seconds"
    response = make_response(render_template(
        'timer.html',
        nextclass=end_time_unix_seconds,
        startclass=start_time_unix_seconds,
        current_epoch=int(datetime.now().timestamp()*1000),
        status=status,
        period=period,
        user=user,
        redirect=request.args.get('noredirect', "false") == "false",
        end_readable=end_readable,
        time_left_readable=time_left_readable
    ))
    return response
