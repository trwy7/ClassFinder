"""
Sets up the flask app and imports all routes.
This file should not be modified unless you know what you are doing, routes are automatically imported from the routes directory.
Any pull requests that modify this file will be examined carefully, and may be subject to additional tests.
"""

import os
import sys
import importlib
import logging
import ipaddress
import re
from datetime import datetime
from flask import Flask, request
from flask_apscheduler import APScheduler
import requests
from app.utilities.config import devmode
import signal
start_init_time = datetime.now()

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

from app.utilities.users import auth_user
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
    # The below is not used for cloudflare, but is here for other code, feel free to move it to a new function
    # request.user = None
    # request.token = None
    request.user, request.token = None, None
    request.user, request.token = auth_user()

@app.before_request
def before_request3():
    """
    Checks if the incoming request is from a Cloudflare IP address.
    """
    request.is_cloudflare = False
    if devmode or app.config.get("TESTING"):
        return None
    if app.config.get("CLOUDFLARE_IP_RANGES"):
        request_ip = ipaddress.ip_address(request.origin_remote_addr)
        for ip_range in app.config["CLOUDFLARE_IP_RANGES"]:
            if request_ip in ipaddress.ip_network(ip_range, strict=False):
                request.is_cloudflare = True
                return None
        app.logger.warning(
            "Request from IP %s not in CloudFlare IP ranges (oip: %s, pip: %s)",
            request.remote_addr,
            request.origin_remote_addr,
            request.proxy_remote_addr
        )
        # return {"message": "You seem to be bypassing CloudFlare, or your IP is using IPv6.", "status": "error"}, 403
        return None
    app.logger.warning("CLOUDFLARE_IP_RANGES not set. We cannot access https://www.cloudflare.com/ips-v4.")
    app.logger.warning("People may be able to bypass rate limits.")
    return None

@app.context_processor
def inject_user():
    """
    Injects the user into the template context.
    """
    return dict(user=auth_user()[0], devmode=devmode)

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
    for log in os.listdir(os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs')):
        if log.endswith(".log"):
            try:
                os.remove(os.path.join(os.environ.get('LOG_DIR', 'logs' if not devmode else 'devlogs'), log))
                app.logger.debug("Removed old log file: %s", log)
            except Exception as e: # pylint: disable=broad-exception-caught
                app.logger.error("Failed to remove old log file %s: %s", log, e)
                continue
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
    request.error_code = None
    reset_color = "\033[0m"
    method_colors = {
        "GET": "\033[92m",  # green
        "POST": "\033[96m", # cyan
        "PUT": "\033[95m",  # purple
        "DELETE": "\033[91m", # red
        "PATCH": "\033[94m", # blue
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
        if params.get("token"):
            params["token"] = params["token"][:3] + "*" * (len(params["token"]) - 2)
    app.logger.debug(f"Processing {method_color}{request.method}{reset_color} {request.path} with {str(params)}")
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
        401: "\033[91m",  # red
        403: "\033[91m",  # red
        404: "\033[91m",  # red
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
    # PostHog integration
    if "text/html" in response.content_type:
        if app.config.get("POSTHOG_API_KEY") and not (devmode or app.config.get("TESTING")):
            api_key = app.config["POSTHOG_API_KEY"]
            script = """
            <script>   !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug getPageViewId".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);    posthog.init('{api_key}', {        api_host: 'https://us.i.posthog.com',        person_profiles: 'identified_only', }); posthog.identify('{username}') </script>
            """.replace("{api_key}", api_key)
            if request.user:
                script = script.replace("{username}", request.user.email)
            else:
                app.logger.debug("Anonymous user request")
                script = script.replace("{username}", "anonymous")
            response.data = response.data.decode("utf-8").replace("</head>", f"{script}</head>").encode("utf-8")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
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
                imbtime = datetime.now()
                importlib.import_module(module_name)
                imatime = datetime.now()
                app.logger.debug(f"Imported {module_name.removeprefix("app.routes.")} in {(imatime - imbtime).total_seconds()}s")

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

# Request CloudFlare IP ranges
if not devmode and not app.config.get("TESTING"):
    cf_ip_ranges = []
    # Get IPv4 ranges
    cf_ip_ranges_req_v4 = requests.get("https://www.cloudflare.com/ips-v4", timeout=10)
    if cf_ip_ranges_req_v4.status_code != 200:
        app.logger.critical("Failed to get CloudFlare IPv4 IP ranges. Status code: %s", cf_ip_ranges_req_v4.status_code)
        sys.exit(1)
    else:
        v4_ranges = [ip for ip in cf_ip_ranges_req_v4.text.splitlines() if not ip.startswith("#")]
        cf_ip_ranges.extend(v4_ranges)
        app.logger.debug("CloudFlare IPv4 IP ranges request successful")
        app.logger.debug(f"CloudFlare IPv4 IP ranges: {v4_ranges}")
    # Get IPv6 ranges
    cf_ip_ranges_req_v6 = requests.get("https://www.cloudflare.com/ips-v6", timeout=10)
    if cf_ip_ranges_req_v6.status_code != 200:
        app.logger.critical("Failed to get CloudFlare IPv6 IP ranges. Status code: %s", cf_ip_ranges_req_v6.status_code)
        sys.exit(1)
    else:
        v6_ranges = [ip for ip in cf_ip_ranges_req_v6.text.splitlines() if not ip.startswith("#")]
        cf_ip_ranges.extend(v6_ranges)
        app.logger.debug("CloudFlare IPv6 IP ranges request successful")
        app.logger.debug(f"CloudFlare IPv6 IP ranges: {v6_ranges}")
else:
    app.logger.debug("Running in dev/test mode, not requesting CloudFlare IP ranges")
    cf_ip_ranges = []
app.config["CLOUDFLARE_IP_RANGES"] = cf_ip_ranges

end_init_time = datetime.now()

app.logger.info(f"Initialization completed in {(end_init_time - start_init_time).total_seconds()}s")

app.logger.info(f"Starting app on {os.environ.get('FLASK_RUN_HOST', '127.0.0.1')}:{os.environ.get('FLASK_RUN_PORT', '5000')} ...")
