"""
Admin route for viewing system logs and analytics
"""
from collections import defaultdict, Counter
from datetime import datetime
from flask import render_template, request
from app import app, get_logs, get_request_logs, start_init_time
from app.utilities.users import require_login, require_role

# Most of this was AI, I have attempted making it more readable, but this code needs work anyway.

@app.route("/admin/logs")
@app.route("/admin/analytics")
@require_login
@require_role(["admin"])
def logs():
    """
    Display the logs analytics dashboard.
    """
    user = request.user

    # Get logs data
    request_logs = get_request_logs()
    app_logs = get_logs()

    # Limit to the most recent logs (newest first)
    app_logs = sorted(app_logs, key=lambda x: x.get('time', datetime.min), reverse=True)[:100]

    # Calculate analytics
    analytics = calculate_analytics(request_logs)

    return render_template(
        "logs.html", 
        user=user,
        analytics=analytics,
        app_logs=app_logs,
        total_requests=len(request_logs),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        start_time=start_init_time.strftime("%Y-%m-%d %H:%M:%S"),
    )

def calculate_analytics(request_logs):
    """
    Calculate analytics from the request logs.
    
    Returns:
        dict: Various analytics data
    """
    analytics = {}

    # Calculate status code distribution
    status_codes = Counter([log.get("returncode") for log in request_logs])
    total_count = sum(status_codes.values())

    analytics["status_codes"] = [
        {
            "code": code,
            "count": count,
            "percentage": round((count / total_count) * 100, 2)
        }
        for code, count in sorted(status_codes.items(), key=lambda x: x[1], reverse=True)
    ]

    # Calculate path+method analytics
    path_time = defaultdict(list)
    path_count = Counter()

    api_requests = 0
    time_requests = 0
    cal_requests = 0

    for log in request_logs:
        # Skip 308 redirects, these are done by flask, also most 404s are bots
        if log.get("returncode") == 308 or log.get("returncode") == 404:
            continue

        # Skip index.css and index.html
        if log.get("url") in ["/index.css", "/index.html", "/favicon.ico"]:
            continue

        path = log.get("url")
        method = log.get("method", "GET")
        if path.endswith("/calendar.ics"):
            path = "/calendar.ics"
            cal_requests += 1
        elif path.startswith("/resetpassword") and path != "/resetpassword":
            path = "/resetpassword/final"
        elif path.startswith("/register") and path != "/register":
            path = "/register/final"
        elif path.startswith("/admin/"):
            continue  # Skip admin paths for now, this can be expanded later
        elif path == "/api/v2/server-time":
            time_requests += 1
        if path.startswith("/api/"):
            api_requests += 1
        path_method = f"{method} {path}"
        path_count[path_method] += 1

        # Calculate processing time in milliseconds
        if "time" in log and "returntime" in log:
            try:
                time_diff = (log["returntime"] - log["time"]).total_seconds() * 1000
                path_time[path_method].append(time_diff)
            except (TypeError, AttributeError):
                # Skip if time calculation fails
                pass

    # Calculate total time spent on path+method
    path_total_time = {
        path_method: sum(times) for path_method, times in path_time.items()
    }

    # Calculate total time across all path+method for percentage
    total_processing_time = sum(path_total_time.values()) if path_total_time else 1  # Avoid div by 0

    analytics["path_time_total"] = [
        {
            "path": path_method,
            "total_time_ms": round(total_time, 2),
            "count": path_count[path_method],
            "time_percentage": round((total_time / total_processing_time) * 100, 2)
        }
        for path_method, total_time in sorted(path_total_time.items(), key=lambda x: x[1], reverse=True)
    ][:20]  # Top 20

    # Most requested path+method
    total_requests = sum(path_count.values())
    analytics["most_requested_paths"] = [
        {
            "path": path_method,
            "count": count,
            "percentage": round((count / total_requests) * 100, 2)
        }
        for path_method, count in path_count.most_common(20)  # Top 20
    ]

    # Average time per path+method
    path_avg_time = {
        path_method: sum(times) / len(times) if times else 0
        for path_method, times in path_time.items()
    }
    analytics["path_time_avg"] = [
        {"path": path_method, "avg_time_ms": round(avg_time, 2), "count": path_count[path_method]}
        for path_method, avg_time in sorted(path_avg_time.items(), key=lambda x: x[1], reverse=True)
    ][:20]  # Top 20

    analytics["api_requests"] = api_requests
    analytics["cal_requests"] = cal_requests
    analytics["time_requests"] = time_requests

    return analytics
