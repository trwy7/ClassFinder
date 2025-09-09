"""
Handles the timer page
"""
from datetime import datetime
from flask import render_template, url_for, redirect, request, make_response
from app import app
from app.utilities.config import status
from app.utilities.classes import get_user_current_period, get_current_period
from app.utilities.users import verify_user

@app.route('/timer/')
@verify_user(required=False)
def timer():
    """
    Handles the timer page
    """
    user = request.user
    # Determine server local timezone once
    local_tz = datetime.now().astimezone().tzinfo
    app.logger.debug(request.args.get('noredirect', "false"))
    if user is None:
        period = get_current_period()
        if period is None:
            if request.args.get('noredirect', "false") != "false":
                return render_template('timer.html', nextclass="nothing")
            return redirect(url_for('dashboard'))
        end_dt = datetime.combine(datetime.now().date(), period['end']).replace(tzinfo=local_tz)
        start_dt = datetime.combine(datetime.now().date(), period['start']).replace(tzinfo=local_tz)
        formatted_end_time = end_dt.strftime('%m/%d/%Y %I:%M:%S %p')
        formatted_start_time = start_dt.strftime('%m/%d/%Y %I:%M:%S %p')
        response = make_response(render_template(
            'timer.html',
            nextclass=formatted_end_time,
            startclass=formatted_start_time,
            current_epoch=int(datetime.now().timestamp()*1000),
            status=status,
            period=period,
            user=None,
            redirect=request.args.get('noredirect', "false") == "false"
        ))
        return response
    period = get_user_current_period(user)
    if period is None:
        if request.args.get('noredirect', "false") != "false":
            return render_template('timer.html', nextclass="nothing")
        return redirect(url_for('dashboard'))
    end_dt = datetime.combine(datetime.now().date(), period['end']).replace(tzinfo=local_tz)
    start_dt = datetime.combine(datetime.now().date(), period['start']).replace(tzinfo=local_tz)
    formatted_end_time = end_dt.strftime('%m/%d/%Y %I:%M:%S %p')
    formatted_start_time = start_dt.strftime('%m/%d/%Y %I:%M:%S %p')
    response = make_response(render_template(
        'timer.html',
        nextclass=formatted_end_time,
        startclass=formatted_start_time,
        current_epoch=int(datetime.now().timestamp()*1000),
        status=status,
        period=period,
        user=user,
        redirect=request.args.get('noredirect', "false") == "false"
    ))
    return response
