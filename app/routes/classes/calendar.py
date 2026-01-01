"""
Allows exporting classes to a icalendar file for use in google calendar
"""
from datetime import date, timedelta, datetime
import pytz
from ics import Calendar, Event
from flask import request, send_file, render_template
from app import app
from app.utilities.config import canvas_url
from app.utilities.users import require_login, require_scopes
from app.utilities.times import get_current_day, get_classtime_by_period, readable_days, get_lunchtimes
from app.utilities.classes import get_today_courses

#GEN_CAL_LENGTH = 91  # Number of days to generate calendar for

@app.route('/classes/calendar')
@require_login
def calendar_page():
    """
    Render the calendar page.
    """
    return render_template('calendar.html')

@app.route('/<authtoken>/calendar.ics')
@app.route('/calendar.ics')
@require_login
@require_scopes(required_scopes=[['read-classes'], ['calendar']])
def calendar_req(authtoken=None): # pylint: disable=unused-argument
    """Generate a calendar file for the current and next 90 days."""
    start_datetime = datetime.now()
    app.logger.info(f"Generating calendar for {request.user.username}")

    cal = Calendar()
    cal.name = f"{request.user.username}'s Calendar"

    # Generate events
    gen_cal_length = (app.config.get("END_OF_SEMESTER") - date.today()).days if app.config.get("END_OF_SEMESTER") else 91
    generate_events_for_date_range(cal, gen_cal_length + 5)
    add_end_of_calendar_event(cal)

    # Export the calendar
    calendar_path = f"/tmp/{request.user.username}_calendar.ics"
    with open(calendar_path, "w", encoding="UTF-8") as f:
        f.write(cal.serialize())

    app.logger.debug(f"Calendar generated in {datetime.now() - start_datetime}")
    return send_file(calendar_path, as_attachment=True, download_name="calendar.ics", mimetype="text/calendar")

def generate_events_for_date_range(calendar, days):
    """Generate calendar events for a specified number of days."""
    for i in range(0, days):
        current_date = date.today() + timedelta(days=i)
        app.logger.debug(f"Generating calendar for {current_date}")
        generate_events_for_date(calendar, current_date)

def generate_events_for_date(calendar, current_date):
    """Generate calendar events for a specific date."""
    current_day = get_current_day(current_date)
    app.logger.debug(f"Current day is {current_day}")

    classes = get_today_courses(request.user, current_day)

    if not classes:
        handle_no_classes_day(calendar, current_date)
        return

    # Add day type event
    if 'adddaytype' in request.args:
        app.logger.debug(f"Adding day type event for {current_date}")
        # Add an all-day event indicating the schedule type
        add_day_type_event(calendar, current_date, current_day)
    else:
        app.logger.debug(f"Skipping day type event for {current_date}")

    # Add events for each class
    for course in classes:
        add_class_event(calendar, course, current_date, current_day)

        if "passing" in request.args:
            add_passing_period_event(calendar, course, current_date, current_day)

def handle_no_classes_day(calendar, current_date):
    """Handle days with no classes."""
    # Skip weekends
    if current_date.weekday() == 5 or current_date.weekday() == 6:
        app.logger.debug(f"Weekend on {current_date}")
        return

    app.logger.debug(f"No classes for {current_date}")
    event = Event()
    event.name = "No school"
    event.begin = datetime.combine(current_date, datetime.min.time())
    event.make_all_day()
    event.description = "No school today"
    calendar.events.add(event)

def add_day_type_event(calendar, current_date, current_day):
    """Add an all-day event indicating the schedule type."""
    event = Event()
    event.name = readable_days[current_day]
    event.begin = datetime.combine(current_date, datetime.min.time())
    event.make_all_day()
    event.description = f"School is a {readable_days[current_day]} schedule today."
    calendar.events.add(event)

def add_class_event(calendar, course, current_date, current_day, ignore_lunch=False):
    """Add a class event to the calendar."""
    classtime = get_classtime_by_period(period=course.period, passing=False, day=current_day)
    if not classtime:
        app.logger.warning(f"No class time found for {course.name} on {current_date}")
        return
    app.logger.debug(f"Adding class event for {classtime}")
    if classtime['lunchactive'] and not ignore_lunch:
        add_class_with_lunch_event(calendar, course, classtime, current_date, current_day)
        return
    denver_tz = pytz.timezone('America/Denver')
    start_time = denver_tz.localize(datetime.combine(current_date, classtime['start']))
    end_time = denver_tz.localize(datetime.combine(current_date, classtime['end']))

    event = Event()
    event.name = course.name
    event.begin = start_time
    event.end = end_time
    event.description = f"Taught by {course.teacher} in room {course.room}\n{course.campus_name}"
    event.location = course.room

    if course.canvasid:
        event.url = f"{canvas_url}/courses/{course.canvasid}"

    calendar.events.add(event)

def add_class_with_lunch_event(calendar, course, classtime, current_date, current_day): # pylint: disable=too-many-statements
    """
    Add a class event with lunch to the calendar.
    Splits the event into two or three parts, depending on if it is A, B, or C lunch.
    """
    app.logger.debug(f"Adding class with lunch event for {course.name} (lunch {course.lunch})")

    denver_tz = pytz.timezone('America/Denver')
    start_time = denver_tz.localize(datetime.combine(current_date, classtime['start']))
    end_time = denver_tz.localize(datetime.combine(current_date, classtime['end']))

    lunchtimes = get_lunchtimes(current_day)
    if course.lunch not in lunchtimes:
        app.logger.debug(f"Invalid lunch type '{course.lunch}' for {course.name}, skipping lunch event")
        add_class_event(calendar, course, current_date, current_day, ignore_lunch=True)
        return
    lunch_start_time = denver_tz.localize(datetime.combine(current_date, lunchtimes[course.lunch]['start']))
    lunch_end_time = denver_tz.localize(datetime.combine(current_date, lunchtimes[course.lunch]['end']))

    app.logger.debug(f"Class time: {start_time.time()} - {end_time.time()}, Lunch: {lunch_start_time.time()} - {lunch_end_time.time()}")

    # Before: A
    # During: B
    # After: C
    if course.lunch == "A":
        app.logger.debug(f"Processing A lunch for {course.name}: lunch first, then class")
        # For A lunch, we split the event into two parts: lunch, and after lunch (class)
        # Lunch
        event = Event()
        event.name = "Lunch"
        event.begin = lunch_start_time
        event.end = lunch_end_time
        event.description = "Lunch"
        calendar.events.add(event)
        # Class
        event = Event()
        event.name = course.name
        event.begin = lunch_end_time
        event.end = end_time
        event.description = f"In room {course.room}"
        event.location = f"Room {course.room}"
        if course.canvasid:
            event.url = f"{canvas_url}/courses/{course.canvasid}"
        calendar.events.add(event)
    elif course.lunch == "B":
        app.logger.debug(f"Processing B lunch for {course.name}: class, lunch, then class")
        # For B lunch, we split the event into three parts: before lunch, during lunch, and after lunch
        # Before
        event = Event()
        event.name = course.name
        event.begin = start_time
        event.end = lunch_start_time
        event.description = f"In room {course.room}"
        event.location = f"Room {course.room}"
        if course.canvasid:
            event.url = f"{canvas_url}/courses/{course.canvasid}"
        calendar.events.add(event)

        # During
        event = Event()
        event.name = "Lunch"
        event.begin = lunch_start_time
        event.end = lunch_end_time
        event.description = "Lunch"
        calendar.events.add(event)

        # After
        event = Event()
        event.name = course.name
        event.begin = lunch_end_time
        event.end = end_time
        event.description = f"In room {course.room}"
        event.location = f"Room {course.room}"
        if course.canvasid:
            event.url = f"{canvas_url}/courses/{course.canvasid}"
        calendar.events.add(event)
    elif course.lunch == "C":
        app.logger.debug(f"Processing C lunch for {course.name}: class first, then lunch")
        # For C lunch, we split the event into two parts: before lunch (class) and lunch
        # Class
        event = Event()
        event.name = course.name
        app.logger.debug(f"Class beginning time: {start_time.time()}, lunch start time: {lunch_start_time.time()}")
        event.begin = start_time
        event.end = lunch_start_time
        event.description = f"In room {course.room}"
        event.location = f"Room {course.room}"
        if course.canvasid:
            event.url = f"{canvas_url}/courses/{course.canvasid}"
        calendar.events.add(event)

        # Lunch
        event = Event()
        event.name = "Lunch"
        event.begin = lunch_start_time
        event.end = lunch_end_time
        event.description = "Lunch"
        calendar.events.add(event)
    else:
        # If the lunch is not A, B, or C, we just add the class event, this should not happen
        app.logger.warning(f"Invalid lunch type '{course.lunch}' for {course.name}, adding class event only")
        event = Event()
        event.name = course.name
        event.begin = start_time
        event.end = end_time
        event.description = f"In room {course.room}"
        event.location = f"Room {course.room}"
        if course.canvasid:
            event.url = f"{canvas_url}/courses/{course.canvasid}"
        calendar.events.add(event)

    app.logger.debug(f"Finished adding events for {course.name} with lunch {course.lunch}")

def add_passing_period_event(calendar, course, current_date, current_day):

    """Add a passing period event to the calendar."""
    passing_classtime = get_classtime_by_period(period=course.period, passing=True, day=current_day)
    denver_tz = pytz.timezone('America/Denver')
    start_time = denver_tz.localize(datetime.combine(current_date, passing_classtime['start']))
    end_time = denver_tz.localize(datetime.combine(current_date, passing_classtime['end']))

    event = Event()
    event.name = "Passing period"
    event.begin = start_time
    event.end = end_time
    event.description = f"Passing period for {course.name} in room {course.room}"
    event.location = f"Room {course.room}"

    calendar.events.add(event)

def add_end_of_calendar_event(calendar):
    """Add an event marking the end of the calendar."""
    gen_cal_length = (app.config.get("END_OF_SEMESTER") - date.today()).days if app.config.get("END_OF_SEMESTER") else 91
    final_date = date.today() + timedelta(days=gen_cal_length + 5)
    event = Event()
    event.name = "End of calendar"
    event.begin = datetime.combine(final_date, datetime.min.time())
    event.make_all_day()
    event.description = "End of generated calendar"
    calendar.events.add(event)
