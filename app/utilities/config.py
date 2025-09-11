"""
Stores configuration variables for the application.
This module will removed in future releases as configuration is moved to app.config.
"""

import platform
import os

devmode = not platform.uname()[1] == "classfinder"
canvas_url = os.environ.get("CANVAS_URL", "https://canvas.instructure.com")
campus_url = os.environ.get("INFINITECAMPUS_URL", "https://www.infinitecampus.com")
allow_leave = os.environ.get("ALLOW_LEAVE", "false") == "true"
status = os.environ.get("STATUS")
