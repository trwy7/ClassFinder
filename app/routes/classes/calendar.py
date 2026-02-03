"""
Allows exporting classes to a icalendar file for use in google calendar
"""
from datetime import date, timedelta, datetime
import pytz
from ics import Calendar, Event
from flask import request, Response, render_template
from app import app
from app.utilities.users import require_login, require_scopes
from app.utilities.times import get_day_schedule, get_current_day, readable_days

#GEN_CAL_LENGTH = 91  # Number of days to generate calendar for
tz = pytz.timezone("America/Denver")
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
    """Generate a calendar file."""
    app.logger.info(f"Generating calendar for {request.user.username}")

    cal = Calendar()
    cal.name = f"{request.user.username}'s Schedule"

    # Generate events
    gen_cal_length = (app.config.get("END_OF_SEMESTER") - date.today()).days if app.config.get("END_OF_SEMESTER") else 91
    generate_events_for_date_range(cal, gen_cal_length + 5)

    # Export the calendar
    #calendar_path = f"/tmp/{request.user.id}_calendar.ics"
    #with open(calendar_path, "w", encoding="UTF-8") as f:
    #    f.write(cal.serialize())
    #return send_file(calendar_path, as_attachment=True, download_name="calendar.ics", mimetype="text/calendar")
    return Response(cal.serialize(), mimetype="text/calendar", headers={"Content-Disposition": 'attachment; filename="calendar.ics"'})

def generate_events_for_date_range(cal: Calendar, num_days: int):
    """Generate calendar events for a date range."""
    for day_offset in range(num_days):
        current_date = date.today() + timedelta(days=day_offset)
        # Skip weekends
        if current_date.weekday() >= 5:
            continue
        cday = get_current_day(current_date)
        day_schedule = get_day_schedule(request.user, cday)
        # Add all day event with the day schedule name
        all_day_event = Event()
        all_day_event.name = readable_days[cday]
        all_day_event.begin = tz.localize(datetime.combine(current_date, datetime.min.time()))
        all_day_event.make_all_day()
        cal.events.add(all_day_event)
        for uct in day_schedule:
            if uct.passing and not uct.period == "Lunch":
                continue  # Skip passing periods
            event = Event()
            if uct.period == "Lunch":
                event.name = "Lunch"
                event.description = uct.course.lunch
            else:
                event.name = uct.course.name
                event.description = f"{uct.course.campus_name}\nPeriod {uct.period}\nTaught by {uct.course.teacher} in room {uct.course.room}"
                event.location = uct.course.room
            event.begin = tz.localize(datetime.combine(current_date, uct.start))
            event.end = tz.localize(datetime.combine(current_date, uct.end))
            cal.events.add(event)
    app.logger.debug(f"Generated events for {num_days} days starting from {date.today()}")
    # At the final day, add an end of semester note
    final_date = date.today() + timedelta(days=num_days)
    event = Event()
    event.name = "End of semester" if app.config.get("END_OF_SEMESTER") else "End of calendar"
    event.begin = tz.localize(datetime.combine(final_date, datetime.min.time()))
    event.description = "End of the current semester." if app.config.get("END_OF_SEMESTER") else "End of generated calendar events."
    event.make_all_day()
    cal.events.add(event)
    app.logger.debug("Added end of semester event")
