# pylint: disable=wrong-import-position, wrong-import-order, ungrouped-imports
"""
Sets up the flask app and imports all routes.
This file should not be modified unless you know what you are doing, routes are automatically imported from the routes directory.
Any pull requests that modify this file will be examined carefully, and may be subject to additional tests.
"""

from datetime import datetime
start_init_time = datetime.now()
import os
import sys
import importlib
import logging
import re
import signal
from flask import Flask, request
from flask_apscheduler import APScheduler
from app.utilities.config import devmode, get_status

app = Flask(__name__, template_folder="pages", static_folder="static")

def stop_server():
    """
    Kills the server process. When in production, this is caught by docker and the server is restarted.
    Really, dont use this unless what was changed requires a full restart.
    """
    os.kill(os.getpid(), signal.SIGINT)

if 'pytest' in sys.modules:
    app.config['TESTING'] = True
app.config['END_OF_SEMESTER'] = os.environ.get('END_OF_SEMESTER', None)
if app.config['END_OF_SEMESTER'] is not None:
    app.config['END_OF_SEMESTER'] = datetime.strptime(app.config['END_OF_SEMESTER'], '%Y-%m-%d').date()

from flask import redirect
from app.utilities.users import auth_user
from app.utilities.responses import error_response
@app.before_request
def before_request2():
    """
    Fixes the IP address when proxied through Cloudflare.
    """
    request.proxy_remote_addr = request.remote_addr
    # app.logger.debug("Proxy address: %s", request.proxy_remote_addr)
    request.origin_remote_addr = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For", request.remote_addr)
    # app.logger.debug("Origin address: %s", request.origin_remote_addr)
    request.remote_addr = request.headers.get("Cf-Connecting-Ip", request.origin_remote_addr)
    # app.logger.debug("Remote address: %s", request.remote_addr)
    # request.user = None
    # request.token = None
    request.error_code = None
    request.user, request.token = None, None
    request.user, request.token = auth_user()

@app.before_request
def check_verify_required(): # pylint: disable=inconsistent-return-statements
    """
    Checks if the user needs to reverify their email.
    """
    if request.user and request.user.requires_reverification:
        if request.path.startswith("/api/"):
            if request.path.startswith("/api/plain"):
                return
            return error_response("Email re-verification required"), 403
        if request.path.startswith("/timer") or \
            request.path.startswith("/account/verify") or \
            request.path.startswith("/logout") or \
            request.path.startswith("/account/delete") or \
            request.path.startswith("/static/") or \
            request.path.endswith("/calendar.ics") or \
            request.path == "/favicon.ico" or \
            request.path.endswith(".css") or \
            request.path.endswith(".js"):
            return
        return redirect("/account/verify")

@app.context_processor
def inject_vars():
    """
    Injects variables into the template context.
    """
    return {"user": auth_user()[0], "devmode": devmode, "site_status": get_status()}

# Analytics
logs: list[dict[str, any]] = []
## Logs structure:
## {
##     "time": "datetime()",
##     "level": "INFO",
##     "message": "message",
##     "path": "path",
##     "line": num,
## }
request_logs: list[dict[str, any]] = []
## Request logs structure:
## {
##     "time": "datetime()",
##     "returntime": "datetime()",
##     "method": "GET",
##     "url": "/api/v1/some/endpoint",
##     "returncode": 200
## }

app.secret_key = os.environ.get("APP_KEY", "devkey")

app.logger.setLevel(os.environ.get("LOG_LEVEL", "DEBUG" if devmode else "INFO"))

app.config["POSTHOG_API_KEY"] = os.environ.get("POSTHOG_API_KEY")

class CustomFormatter(logging.Formatter):
    """
    Custom formatter for app.logger that adds color to the output.
    """
    def format(self, record):
        relative_path = os.path.relpath(record.pathname, os.path.dirname(__file__)).removesuffix(".py")
        reset_color = "\033[0m"
        level_color = {
            "DEBUG": "\033[97m",  # white
            "INFO": "\033[94m",   # blue
            "WARNING": "\033[93m", # yellow
            "ERROR": "\033[91m",  # red
            "CRITICAL": "\033[91m" # red
        }.get(record.levelname, reset_color)  # default to no color
        bold = "\033[1m"
        # Strip ANSI color codes from log messages
        logs.append({
            "time": datetime.now(),
            "level": record.levelname,
            "message": re.sub(r'\033\[[0-9;]*m', '', record.getMessage()),
            "path": relative_path,
            "line": record.lineno,
        })
        # current_request_logs.append(f"({record.levelname}) {relative_path}:{record.lineno} {record.getMessage()}")
        if os.path.basename(record.pathname) == "__init__.py":
            return f"{bold}{level_color}{record.levelname}{reset_color}{level_color}: {record.getMessage().replace('\033[0m', '\033[0m'+level_color)}{reset_color}" # pylint: disable=line-too-long
        return f"{bold}{level_color}{record.levelname}{reset_color}{level_color} in {bold}{relative_path}{reset_color}{level_color} at {bold}{record.lineno}{reset_color}{level_color}: {record.getMessage()}{reset_color}" # pylint: disable=line-too-long

formatter = CustomFormatter()
handler = logging.StreamHandler()
handler.setFormatter(formatter)
app.logger.handlers.clear()
app.logger.addHandler(handler)

app.logger.debug("Logger initialized")
app.logger.debug("Log level set to %s and devmode is %s", app.logger.level, devmode)
if not app.config.get("TESTING", False):
    if os.path.isdir(os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs')):
        for log in os.listdir(os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs')):
            if log.endswith(".log"):
                try:
                    os.remove(os.path.join(os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs'), log))
                    app.logger.debug("Removed old log file: %s", log)
                except Exception as e: # pylint: disable=broad-exception-caught
                    app.logger.error("Failed to remove old log file %s: %s", log, e)
                    continue
    else:
        if os.path.exists(os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs')):
            raise NotADirectoryError(f"{os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs')} exists and is not a directory!")
        os.mkdir(os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs'))
app.logger.debug("Old log files removed")

# Configure waitress logger to use the same handler
waitress_logger = logging.getLogger('waitress')
waitress_logger.handlers.clear()
waitress_logger.addHandler(handler)

@app.before_request
def log_request():
    """
    Logs the request method and path with the parameters.
    """
    reset_color = "\033[0m"
    method_colors = {
        "GET": "\033[92m",  # green
        "POST": "\033[96m", # cyan
        "PUT": "\033[95m",  # purple
        "DELETE": "\033[91m", # red
        "PATCH": "\033[94m", # blue
        "OPTIONS": "\033[93m", # yellow
    }
    method_color = method_colors.get(request.method, "\033[97m")  # white
    if request.content_type == "application/json":
        try:
            params = request.get_json() or {}
        except Exception as e: # pylint: disable=broad-exception-caught
            app.logger.error("Failed to parse JSON request body: %s", e)
            params = {}
    else:
        try:
            params = request.args.to_dict()
        except Exception as e: # pylint: disable=broad-exception-caught
            app.logger.error("Failed to parse query parameters: %s", e)
            params = {}
    params = params.copy()
    if isinstance(params, dict):
        if params.get("password"):
            params["password"] = ("*" * len(params["password"])) if len(params["password"]) < 25 else "*****"
        if params.get("authtoken"):
            params["authtoken"] = params["authtoken"][:3] + "*" * (len(params["authtoken"]) - 2)
    params = str(params)
    if len(params) > 50:
        params = params[:50] + "..."
    app.logger.debug(f"Processing {method_color}{request.method}{reset_color} {request.path} with {params}")
    request.start_time = datetime.now()

@app.after_request
def log_response(response):
    """
    Logs the response status code.
    """
    reset_color = "\033[0m"
    status_colors = {
        200: "\033[92m",  # green
        201: "\033[96m",  # cyan
        204: "\033[96m",  # cyan
        304: "\033[96m",  # cyan
        300: "\033[96m",  # cyan
        301: "\033[96m",  # cyan
        302: "\033[96m",  # cyan
        400: "\033[93m",  # yellow
        401: "\033[93m",  # yellow
        403: "\033[93m",  # yellow
        404: "\033[93m",  # yellow
        405: "\033[93m",  # yellow
        429: "\033[93m",  # yellow
        500: "\033[91m",  # red
    }
    method_colors = {
        "GET": "\033[92m",  # green
        "POST": "\033[96m", # cyan
        "PUT": "\033[95m",  # purple
        "DELETE": "\033[91m", # red
        "PATCH": "\033[94m", # blue
    }
    status_color = status_colors.get(response.status_code, "\033[97m")  # white
    method_color = method_colors.get(request.method, "\033[97m") # white
    app.logger.debug(f"Response for {method_color}{request.method}{reset_color} {request.path} is {status_color}{response.status_code}{reset_color}")
    if response.status_code == 302:
        app.logger.debug(f"Redirecting to {response.headers.get('Location')}")
    if "text/html" in response.content_type or "application/json" in response.content_type:
        # Disable caching for HTML and JSON responses
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    if "text/css" in response.content_type or \
        "application/javascript" in response.content_type or \
        "text/javascript" in response.content_type or \
        request.path == "/favicon.ico":
        # CSS and JS can be cached for a day
        response.headers["Cache-Control"] = "public, max-age=86400"

    # Log the request
    req_url = request.path
    if req_url.endswith("/calendar.ics"):
        req_url = "/calendar.ics"
    try:
        request_logs.append({
            "time": request.start_time if hasattr(request, 'start_time') else datetime.now(),
            "returntime": datetime.now(),
            "method": request.method,
            "url": req_url,
            "returncode": response.status_code,
            "error_code": request.error_code,
        })
    except Exception as e: # pylint: disable=broad-exception-caught
        app.logger.error("Failed to log request: %s", e)
    # Add Server-Timing header
    try:
        duration = (datetime.now() - (request.start_time if hasattr(request, 'start_time') else datetime.now())).total_seconds() * 1000
        response.headers["Server-Timing"] = f"app;dur={duration:.2f}"
    except Exception as e: # pylint: disable=broad-exception-caught
        app.logger.error("Failed to set Server-Timing header: %s", e)
    return response

def import_routes(directory):
    """
    Imports all routes in the specified directory. Should not be called manually.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                module_name = (
                    os.path.join(root, file)
                    .replace(directory, "app.routes")
                    .replace(os.sep, ".")
                    .replace(".py", "")
                )
                # imbtime = datetime.now()
                importlib.import_module(module_name)
                # imatime = datetime.now()
                # app.logger.debug(f"Imported {module_name.removeprefix("app.routes.")} in {(imatime - imbtime).total_seconds()}s")

def get_logs():
    """
    Returns the logs.
    """
    return logs

def get_request_logs():
    """
    Returns the request logs.
    """
    return request_logs

import_routes(os.path.join(os.path.dirname(__file__), "routes"))

scheduler = APScheduler()
from app.db import db_cleanup # pylint: disable=wrong-import-position # This import wont work if it is at the top of the file as it causes a circular import

@scheduler.task("cron", hour=2, misfire_grace_time=3600)
def do_daily_tasks():
    """
    Cleans up the database and does other daily tasks. (Runs at 2am)
    """
    app.logger.info("Cleaning up database...")
    db_cleanup()

app.logger.info("Running daily tasks for initialization")
with app.app_context():
    btime = datetime.now()
    do_daily_tasks()
    atime = datetime.now()
    app.logger.info(f"Daily tasks completed in {(atime - btime).total_seconds()}s")

scheduler.init_app(app)
scheduler.start()

# Disable the werkzeug logger to prevent double logging
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

for logger in [logging.getLogger('waitress')]:
    logger.disabled = True

for handler in app.logger.handlers[:]:
    app.logger.removeHandler(handler)
app.logger.addHandler(handler)

class CustomWerkzeugFormatter(logging.Formatter):
    """
    Custom formatter for werkzeug logger that only logs exceptions. I cant tell if this actually does anything. 
    """
    def format(self, record):
        return ""

werkzeug_logger.handlers.clear()
werkzeug_handler = logging.StreamHandler()
werkzeug_handler.setFormatter(CustomWerkzeugFormatter())
werkzeug_handler.addFilter(lambda record: False)
werkzeug_logger.addHandler(werkzeug_handler)
logging.basicConfig(handlers=[werkzeug_handler], level=app.logger.level)

end_init_time = datetime.now()

app.logger.info(f"Initialization completed in {(end_init_time - start_init_time).total_seconds()}s")

app.logger.info(f"Starting app on {os.environ.get('FLASK_RUN_HOST', '127.0.0.1')}:{os.environ.get('FLASK_RUN_PORT', '5000')} ...")
