# pylint: disable=missing-function-docstring
"""
Handles error codes.
"""

import traceback
import os
import random
from flask import render_template, request, abort
from app import app, start_init_time
from app.utilities.responses import error_response
from app.utilities.config import devmode

@app.errorhandler(404)
def page_not_found(e): # pylint: disable=unused-argument
    """
    Handles the 404 page
    """
    return render_template("templates/error.html", status_code=404, error_message="Page not found"), 404


@app.errorhandler(401)
def unauthorized(e): # pylint: disable=unused-argument
    """
    Handles the 401 page
    """
    return render_template("templates/error.html", status_code=401, error_message="Unauthorized"), 401

@app.errorhandler(500)
@app.errorhandler(Exception)
def internal_server_error(e):
    """
    Handles the 500 page, and logs the error
    """
    errorcode = random.randbytes(5).hex()
    ret_dict = {"error_code": errorcode}
    app.logger.error(f"Error code: {errorcode}\n" + traceback.format_exc())
    # request_logs = get_current_request_logs()
    if not app.config['TESTING']:
        tb = getattr(e, '__traceback__', None)
        if tb:
            # Walk to the last traceback frame (most recent call)
            while tb.tb_next:
                tb = tb.tb_next
            filename = tb.tb_frame.f_code.co_filename
            lineno = tb.tb_lineno
            error_details = f"{e.__class__.__name__} at {filename}:{lineno}"
            error_details_log = f"{e.__class__.__name__}_in_{str(os.path.basename(filename)).removesuffix(".py")}{lineno}"
        else:
            error_details = e.__class__.__name__
            error_details_log = e.__class__.__name__
        os.makedirs(f"{os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs')}", exist_ok=True)
        # Check if there are any existing logs with the same error type, filename, and line number
        existing_logs = [log for log in os.listdir(os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs')) if log.startswith(error_details_log) and log.endswith(".error.log")]
        if existing_logs:
            app.logger.debug(f"Found existing logs for {error_details_log}, adding error code to existing log.")
            with open(f"{os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs')}/{existing_logs[0]}", "r+", encoding="utf-8") as f:
                existing_content = f.read()
                f.seek(0, 0)
                new_entry = (
                    f"Error code: {errorcode} at " + start_init_time.strftime('%Y-%m-%d %I:%M:%S %p') + "\n"
                )
                f.write(new_entry + existing_content)
        else:
            with open(f"{os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs')}/{error_details_log}.error.log", "w", encoding="utf-8") as f:
                f.write(f"Error code: {errorcode}\n")
                f.write("Date/Time: " + start_init_time.strftime('%Y-%m-%d %I:%M:%S %p') + "\n")
                f.write(str(e) + "\n")
                f.write(traceback.format_exc() + "\n")
                # for rlog in request_logs:
                #     f.write(str(rlog) + "\n")
    request.error_code = errorcode
    if request.path.startswith("/api/") or request.method != "GET":
        if request.path.startswith("/api/plain"):
            return "Internal server error: " + errorcode, 500
        return error_response("Internal server error", ret_dict), 500
    if hasattr(request, "user") and getattr(request.user, "role", None) == "admin" and not app.config['TESTING']:
        error_details_vis = error_details
    else:
        error_details_vis = ""
    return render_template(
        "templates/error.html",
        error_code=errorcode,
        status_code=500,
        error_message="Internal server error",
        error_details=error_details_vis
    ), 500

@app.route("/sim500")
def simulate_500():
    """
    Simulates a 500 error for testing purposes.
    """
    if devmode:
        raise LookupError("Simulated 500 LookupError")
    return abort(404)