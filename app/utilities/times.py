"""
This file contains the functions and data structures for the schedule of the school.
"""

import os
from datetime import date, timedelta, time, datetime
from reportlab.pdfgen import canvas
from app import app
from app.db import Schedule, db, User

now = datetime.now()
class ClassTime:
    """Representation of a class time slot with helpers to access attributes as a mapping."""
    __slots__ = ("start", "end", "period", "passing", "lunchactive")
    def __init__(self, period: str, start: time, end: time, passing: bool, lunchactive: bool):
        self.start = start
        self.end = end
        self.period = period
        self.passing = passing
        self.lunchactive = lunchactive
class LunchPeriod:
    """Representation of a lunch period with helpers to access attributes as a mapping."""
    __slots__ = ("start", "end", "period")
    def __init__(self, period: str, start: time, end: time):
        self.period = period
        self.start = start
        self.end = end

class DaySchedule:
    """Container for a day's schedule that supports attribute and mapping access."""
    __slots__ = ("name", "classtimes", "lunchtimes")
    def __init__(self, name: str, classtimes: list[ClassTime], lunchtimes: list[LunchPeriod]):
        self.name = name
        self.classtimes = classtimes
        self.lunchtimes = lunchtimes

classtime_dict = {
    0: DaySchedule("Monday", [
        ClassTime("1", time(7, 40), time(8, 0), True, False),
        ClassTime("1", time(8, 0), time(9, 45), False, False),
        ClassTime("3", time(9, 45), time(9, 50), True, False),
        ClassTime("3", time(9, 50), time(11, 30), False, False),
        ClassTime("5", time(11, 30), time(11, 35), True, False),
        ClassTime("5", time(11, 35), time(13, 45), False, True),
        ClassTime("7", time(13, 45), time(13, 50), True, False),
        ClassTime("7", time(13, 50), time(15, 30), False, False),
    ], [
        LunchPeriod("A", time(11, 35), time(12, 5)),
        LunchPeriod("B", time(12, 15), time(12, 45)),
        LunchPeriod("C", time(13, 10), time(13, 45)),
    ]),
    1: DaySchedule("Tuesday", [
        ClassTime("2", time(7, 40), time(8, 0), True, False),
        ClassTime("2", time(8, 0), time(9, 45), False, False),
        ClassTime("4", time(9, 45), time(9, 50), True, False),
        ClassTime("4", time(9, 50), time(11, 30), False, False),
        ClassTime("6", time(11, 30), time(11, 35), True, False),
        ClassTime("6", time(11, 35), time(13, 45), False, True),
        ClassTime("8", time(13, 45), time(13, 50), True, False),
        ClassTime("8", time(13, 50), time(15, 30), False, False),
    ], [
        LunchPeriod("A", time(11, 35), time(12, 5)),
        LunchPeriod("B", time(12, 15), time(12, 45)),
        LunchPeriod("C", time(13, 10), time(13, 45)),
    ]),
    2: DaySchedule("Wednesday", [
        ClassTime("1", time(7, 40), time(8, 0), True, False),
        ClassTime("1", time(8, 0), time(9, 20), False, False),
        ClassTime("3", time(9, 20), time(9, 25), True, False),
        ClassTime("3", time(9, 25), time(10, 45), False, False),
        ClassTime("Access", time(10, 45), time(10, 50), True, False),
        ClassTime("Access", time(10, 50), time(12, 0), False, False),
        ClassTime("5", time(12, 0), time(12, 5), True, False),
        ClassTime("5", time(12, 5), time(14, 5), False, True),
        ClassTime("7", time(14, 5), time(14, 10), True, False),
        ClassTime("7", time(14, 10), time(15, 30), False, False),
    ], [
        LunchPeriod("A", time(12, 5), time(12, 35)),
        LunchPeriod("B", time(12, 40), time(13, 10)),
        LunchPeriod("C", time(13, 30), time(14, 5)),
    ]),
    3: DaySchedule("Thursday", [
        ClassTime("2", time(7, 40), time(8, 0), True, False),
        ClassTime("2", time(8, 0), time(9, 20), False, False),
        ClassTime("4", time(9, 20), time(9, 25), True, False),
        ClassTime("4", time(9, 25), time(10, 45), False, False),
        ClassTime("Access", time(10, 45), time(10, 50), True, False),
        ClassTime("Access", time(10, 50), time(12, 0), False, False),
        ClassTime("6", time(12, 0), time(12, 5), True, False),
        ClassTime("6", time(12, 5), time(14, 5), False, True),
        ClassTime("8", time(14, 5), time(14, 10), True, False),
        ClassTime("8", time(14, 10), time(15, 30), False, False),
    ], [
        LunchPeriod("A", time(12, 5), time(12, 35)),
        LunchPeriod("B", time(12, 40), time(13, 10)),
        LunchPeriod("C", time(13, 30), time(14, 5)),
    ]),
    4: DaySchedule("Friday", [
        ClassTime("1", time(7, 40), time(8, 0), True, False),
        ClassTime("1", time(8, 0), time(8, 45), False, False),
        ClassTime("2", time(8, 45), time(8, 50), True, False),
        ClassTime("2", time(8, 50), time(9, 35), False, False),
        ClassTime("3", time(9, 35), time(9, 40), True, False),
        ClassTime("3", time(9, 40), time(10, 25), False, False),
        ClassTime("4", time(10, 25), time(10, 30), True, False),
        ClassTime("4", time(10, 30), time(11, 15), False, False),
        ClassTime("5", time(11, 15), time(11, 20), True, False),
        ClassTime("5", time(11, 20), time(13, 0), False, True),
        ClassTime("6", time(13, 0), time(13, 5), True, False),
        ClassTime("6", time(13, 5), time(13, 50), False, False),
        ClassTime("7", time(13, 50), time(13, 55), True, False),
        ClassTime("7", time(13, 55), time(14, 40), False, False),
        ClassTime("8", time(14, 40), time(14, 45), True, False),
        ClassTime("8", time(14, 45), time(15, 30), False, False),
    ], [
        LunchPeriod("A", time(11, 20), time(11, 50)),
        LunchPeriod("B", time(11, 55), time(12, 25)),
        LunchPeriod("C", time(12, 25), time(13, 0)),
    ]),
    5: DaySchedule("No school", [], []),
    6: DaySchedule("No school", [], []),
    7: DaySchedule("Early Release Blue", [
        ClassTime("1", time(7, 40), time(8, 0), True, False),
        ClassTime("1", time(8, 0), time(8, 55), False, False),
        ClassTime("3", time(8, 55), time(9, 0), True, False),
        ClassTime("3", time(9, 0), time(9, 55), False, False),
        ClassTime("5", time(9, 55), time(10, 0), True, False),
        ClassTime("5", time(10, 0), time(10, 55), False, False),
        ClassTime("7", time(10, 55), time(11, 0), True, False),
        ClassTime("7", time(11, 0), time(11, 55), False, False),
    ], []),
    8: DaySchedule("Early Release Gold", [
        ClassTime("2", time(7, 40), time(8, 0), True, False),
        ClassTime("2", time(8, 0), time(8, 55), False, False),
        ClassTime("4", time(8, 55), time(9, 0), True, False),
        ClassTime("4", time(9, 0), time(9, 55), False, False),
        ClassTime("6", time(9, 55), time(10, 0), True, False),
        ClassTime("6", time(10, 0), time(10, 55), False, False),
        ClassTime("8", time(10, 55), time(11, 0), True, False),
        ClassTime("8", time(11, 0), time(11, 55), False, False),
    ], []),
    9: DaySchedule("Development", [
        ClassTime("1", (now - timedelta(minutes=3)).time(), (now + timedelta(minutes=0.2)).time(), True, False),
        ClassTime("2", (now + timedelta(minutes=0.3)).time(), (now + timedelta(minutes=10)).time(), True, False),
        ClassTime("3", (now + timedelta(minutes=10)).time(), (now + timedelta(minutes=15)).time(), False, False),
        ClassTime("4", (now + timedelta(minutes=15)).time(), (now + timedelta(minutes=20)).time(), False, False),
    ], []),
    10: DaySchedule("Delayed Monday", [
        ClassTime("1", time(9, 30), time(10, 0), True, False),
        ClassTime("1", time(10, 0), time(11, 15), False, False),
        ClassTime("3", time(11, 15), time(11, 20), True, False),
        ClassTime("3", time(11, 20), time(12, 30), False, False),
        ClassTime("5", time(12, 30), time(12, 35), True, False),
        ClassTime("5", time(12, 35), time(14, 15), False, True),
        ClassTime("7", time(14, 15), time(14, 20), True, False),
        ClassTime("7", time(14, 20), time(15, 30), False, False),
    ], [
        LunchPeriod("A", time(12, 35), time(13, 5)),
        LunchPeriod("B", time(13, 10), time(13, 40)),
        LunchPeriod("C", time(13, 45), time(14, 15)),
    ]),
    11: DaySchedule("Delayed Tuesday", [
        ClassTime("2", time(9, 30), time(10, 0), True, False),
        ClassTime("2", time(10, 0), time(11, 15), False, False),
        ClassTime("4", time(11, 15), time(11, 20), True, False),
        ClassTime("4", time(11, 20), time(12, 30), False, False),
        ClassTime("6", time(12, 30), time(12, 35), True, False),
        ClassTime("6", time(12, 35), time(14, 15), False, True),
        ClassTime("8", time(14, 15), time(14, 20), True, False),
        ClassTime("8", time(14, 20), time(15, 30), False, False),
    ], [
        LunchPeriod("A", time(12, 35), time(13, 5)),
        LunchPeriod("B", time(13, 10), time(13, 40)),
        LunchPeriod("C", time(13, 45), time(14, 15)),
    ]),
    12: DaySchedule("Delayed Wednesday", [
        ClassTime("1", time(9, 30), time(10, 0), True, False),
        ClassTime("1", time(10, 0), time(11, 5), False, False),
        ClassTime("3", time(11, 5), time(11, 10), True, False),
        ClassTime("3", time(11, 10), time(12, 10), False, False),
        ClassTime("Access", time(12, 10), time(12, 15), True, False),
        ClassTime("Access", time(12, 15), time(12, 45), False, False),
        ClassTime("5", time(12, 45), time(12, 50), True, False),
        ClassTime("5", time(12, 50), time(13, 20), False, True),
        ClassTime("7", time(13, 20), time(14, 30), True, False),
        ClassTime("7", time(14, 30), time(15, 30), False, False),
    ], [
        LunchPeriod("A", time(12, 50), time(13, 20)),
        LunchPeriod("B", time(13, 25), time(13, 55)),
        LunchPeriod("C", time(14, 0), time(14, 30)),
    ]),
    13: DaySchedule("Delayed Thursday", [
        ClassTime("2", time(9, 30), time(10, 0), True, False),
        ClassTime("2", time(10, 0), time(11, 5), False, False),
        ClassTime("4", time(11, 5), time(11, 10), True, False),
        ClassTime("4", time(11, 10), time(12, 10), False, False),
        ClassTime("Access", time(12, 10), time(12, 15), True, False),
        ClassTime("Access", time(12, 15), time(12, 45), False, False),
        ClassTime("6", time(12, 45), time(12, 50), True, False),
        ClassTime("6", time(12, 50), time(13, 20), False, True),
        ClassTime("8", time(13, 20), time(14, 30), True, False),
        ClassTime("8", time(14, 30), time(15, 30), False, False),
    ], [
        LunchPeriod("A", time(12, 50), time(13, 20)),
        LunchPeriod("B", time(13, 25), time(13, 55)),
        LunchPeriod("C", time(14, 0), time(14, 30)),
    ]),
    14: DaySchedule("Delayed Friday", [
        ClassTime("1", time(10, 0), time(10, 30), False, False),
        ClassTime("2", time(10, 30), time(10, 35), True, False),
        ClassTime("2", time(10, 35), time(11, 0), False, False),
        ClassTime("3", time(11, 0), time(11, 5), True, False),
        ClassTime("3", time(11, 5), time(11, 30), False, False),
        ClassTime("4", time(11, 30), time(11, 35), True, False),
        ClassTime("4", time(11, 35), time(12, 0), False, False),
        ClassTime("5", time(12, 0), time(12, 5), True, False),
        ClassTime("5", time(12, 5), time(13, 45), False, True),
        ClassTime("6", time(13, 45), time(13, 50), True, False),
        ClassTime("6", time(13, 50), time(14, 20), False, False),
        ClassTime("7", time(14, 20), time(14, 25), True, False),
        ClassTime("7", time(14, 25), time(14, 55), False, False),
        ClassTime("8", time(14, 55), time(15, 0), True, False),
        ClassTime("8", time(15, 0), time(15, 30), False, False),
    ], [
        LunchPeriod("A", time(12, 5), time(12, 35)),
        LunchPeriod("B", time(12, 40), time(13, 10)),
        LunchPeriod("C", time(13, 15), time(13, 45)),
    ]),
}
del now
# TODO: Webhooks with custom data? Possibly for ntfy/discord notifications?

bell_delay = 0.0 # pylint: disable=invalid-name # This is not a constant, but it gets flagged as one.

def change_bell_delay(delay_seconds: float, commit: bool=True):
    """
    Change the bell delay for all class times.

    Args:
        delay_seconds (float): The delay in seconds to add to each class time.
    """
    global bell_delay # pylint: disable=global-statement
    # last_bell_delay = bell_delay
    bell_delay += delay_seconds
    if os.environ.get("BELL_DELAY_PATH") and delay_seconds != 0.0 and commit:
        with open(os.environ.get("BELL_DELAY_PATH"), "w", encoding="utf-8") as f:
            f.write(str(bell_delay))
            app.logger.info(f"Saved bell delay of {bell_delay} seconds to {os.environ.get('BELL_DELAY_PATH')}")

if os.environ.get("BELL_DELAY_PATH") and os.path.isfile(os.environ.get("BELL_DELAY_PATH")):
    with open(os.environ.get("BELL_DELAY_PATH"), "r", encoding="utf-8") as bf:
        change_bell_delay(float(bf.read().strip()), commit=False)
        app.logger.info(f"Loaded bell delay of {bell_delay} seconds from {os.environ.get('BELL_DELAY_PATH')}")

def reset_bell_delay():
    """
    Reset the bell delay to 0 seconds.
    """
    change_bell_delay(-bell_delay)

def get_bell_delay() -> float:
    """
    Get the current bell delay.

    Returns:
        float: The current bell delay in seconds.
    """
    return bell_delay

def get_current_day(oday: date=None):
    """
    Get the current day of the week, as defined by the schedule.

    Returns:
        int: The simulated day of the week.
    """
    if oday is not None:
        app.logger.debug(f"Getting simulated day {oday}")
        day = oday
    else:
        app.logger.debug("Getting current day")
        day = datetime.today().date()
    with app.app_context():
        app.logger.debug(f"Getting schedule for {day}")
        schedule = Schedule.query.filter_by(day=day).first()
    if schedule:
        app.logger.debug(f"Schedule found for {day}: {schedule.type}")
        return schedule.type
    app.logger.debug(f"No schedule found for {day}, using current day")
    return day.weekday()

def get_classtimes(day: int=None):
    """
    Get the class times for the current day.

    Returns:
        list: A list of class times.
    """
    return classtime_dict[get_current_day() if day is None else day].classtimes

def get_classtime_by_period(period: str, passing: bool=False, day: int=None):
    """
    Get the class time for a specific period.

    Args:
        period (str): The period to get the class time for.
        passing (bool): Whether to get the passing time.

    Returns:
        dict: The class time for the specified period.
    """
    classtimes = get_classtimes(day)
    for classtime in classtimes:
        if classtime['period'] == period and classtime['passing'] == passing:
            return classtime
    return None

def get_lunchtimes(day: int=None):
    """
    Get the lunch times for the current day.

    Returns:
        dict: A dictionary of lunch
    """
    return classtime_dict[get_current_day() if day is None else day]['lunchtimes']

def set_schedule(start: date, end: date, simulated_day: int):
    """
    Set the schedule for a range of days.

    Args:
        start (date): The start date.
        end (date): The end date.
        simulated_day (int): The type of day to simulate.

    Returns:
        None
    """
    app.logger.info(f"Setting schedule for {start} to {end}")
    schedules = []
    for i in range((end - start).days + 1):
        day = start + timedelta(days=i)
        schedules.append(Schedule(day=day, type=simulated_day))
    app.logger.info(f"Schedules set from {start} to {end} for day type {simulated_day}")
    for schedule in schedules:
        existing_schedule = Schedule.query.filter_by(day=schedule.day).first()
        if existing_schedule:
            db.session.delete(existing_schedule)
        db.session.add(schedule)
    db.session.commit()

def day_has_override(day: date) -> bool:
    """
    Check if a day has an override.

    Args:
        day (date): The day to check.

    Returns:
        bool: True if the day has an override, False otherwise.
    """
    with app.app_context():
        schedule = Schedule.query.filter_by(day=day).first()
    return schedule is not None and schedule.type != day.weekday()

def create_schedule_pdf( # pylint: disable=too-many-arguments, too-many-positional-arguments, too-many-locals, too-many-branches, too-many-statements
        user: User=None,
        days: list[int]=None,
        separate: bool=False,
        showperiod: bool=True,
        showclass: bool=True,
        showroom: bool=True,
        showtime: bool=True,
        showlunch: bool=True,
        smalltext: bool=False
    ):
    """
    Create a PDF of the schedule for a user.

    Args:
        user (User): The user to create the schedule for.
        days (list[int]): The days to create the schedule for.
        separate (bool): Whether to separate the days.
        showperiod (bool): Whether to show the period.
        showclass (bool): Whether to show the class.
        showroom (bool): Whether to show the room.
        showtime (bool): Whether to show the time.
        showlunch (bool): Whether to show the lunch.
        smalltext (bool): Whether to use small text.
    """
    if not days:
        days = [get_current_day()]
    file_path = f"/tmp/{user.username if user else 'schedule'}CFSchedule.pdf"
    c = canvas.Canvas(file_path)
    c.setTitle("School Schedule")
    c.setFont("Helvetica", 20 if not smalltext else 12)
    y = 820 if not smalltext else 818
    app.logger.debug(f"Creating schedule PDF for {user.username if user else 'a guest user'} for days {days}")
    app.logger.debug(f"seperate: {separate}, showclass: {showclass}, showroom: {showroom}, showtime: {showtime}, showlunch: {showlunch}, smalltext: {smalltext}") # pylint: disable=line-too-long
    for day in days:
        y -= 10 if not smalltext else 5
        c.setFont("Helvetica-Bold", 16 if not smalltext else 10)
        c.drawString(50, y, readable_days[day])
        y -= 20 if not smalltext else 10
        c.setFont("Helvetica", 12 if not smalltext else 8)
        classtimes = classtime_dict[day].classtimes
        for ctime in classtimes:
            if ctime['passing']:
                continue
            course = None
            if user:
                for ncourse in user.classes:
                    if ncourse.period == ctime['period']:
                        course = ncourse
                        break
            start_time = ctime['start'].strftime("%I:%M %p")
            end_time = ctime['end'].strftime("%I:%M %p")
            drawthings = []
            if showperiod:
                drawthings.append(f"Period {ctime['period'] if ctime['period'] != 'Access' else 'Access'}")
            if showtime:
                drawthings.append(f"{start_time} - {end_time}")
            if showclass and course:
                drawthings.append(course.name)
            if showroom and course:
                drawthings.append(course.room)
            if drawthings:
                c.drawString(50, y, " - ".join(drawthings))
                y -= 15 if not smalltext else 10
            if showlunch and ctime['lunchactive'] and course and course.lunch:
                lunchtime = classtime_dict[day]['lunchtimes'][course.lunch]
                start_time = lunchtime['start'].strftime("%I:%M %p")
                end_time = lunchtime['end'].strftime("%I:%M %p")
                #c.drawString(50, y, f"{course.lunch} lunch" + (f": {start_time} - {end_time}" if showtime else ""))
                drawthings = []
                drawthings.append(f"{course.lunch} lunch")
                if showtime:
                    drawthings.append(f"{start_time} - {end_time}")
                c.drawString(50, y, " - ".join(drawthings))
                y -= 15 if not smalltext else 10
        if separate:
            c.showPage()
            c.setFont("Helvetica", 20 if not smalltext else 12)
            y = 820 if not smalltext else 818
    c.showPage()
    c.save()
    return file_path

def get_full_schedule(day: date=None, user: User=None): # For simpler applications that cannot generate this themselves, or for caching purposes
    """
    Get the schedule for a user on a specific day.

    Args:
        day (date): The day to get the schedule for.
        user (User): The user to get the schedule for.
    Returns:
        list: A list of class times for the user on the specified day, with lunch breaks included.
    """
    day_type = get_current_day(day)
    classtimes = get_classtimes(day_type)
    schedule = []
    for ctime in classtimes:
        class_info = {
            "start": ctime['start'],
            "end": ctime['end'],
            "period": ctime['period'],
            "passing": ctime['passing'],
            "lunchactive": ctime['lunchactive'],
            "class": None
        }
        if user:
            for uclass in user.classes:
                if uclass.period == ctime['period']:
                    class_info['class'] = uclass
                    break
        schedule.append(class_info)
    # Find lunch period
    for entry in schedule:
        if entry['lunchactive'] and entry['class'] and entry['class'].lunch:
            lunchtime = get_lunchtimes(day_type)[entry['class'].lunch]
            lunch_entry = {
                "start": lunchtime['start'],
                "end": lunchtime['end'],
                "period": "Lunch",
                "passing": False,
                "lunchactive": True,
                "class": None
            }
            schedule.insert(schedule.index(entry) + 1, lunch_entry)
            # Break the original schedule to mark the period end/start around lunch
            if entry['class'].lunch == 'A':
                app.logger.debug(f"Processing A lunch for {entry['class'].name}: lunch first, then class")
                entry['start'] = lunchtime['end']
            elif entry['class'].lunch == 'B':
                app.logger.debug(f"Processing B lunch for {entry['class'].name}: lunch in middle of class")
                # Move end time to lunch start
                original_end = entry['end']
                entry['end'] = lunchtime['start']
                # Create new entry for post-lunch class time
                post_lunch_entry = {
                    "start": lunchtime['end'],
                    "end": original_end,
                    "period": entry['period'],
                    "passing": entry['passing'],
                    "lunchactive": entry['lunchactive'],
                    "class": entry['class']
                }
                schedule.insert(schedule.index(entry) + 2, post_lunch_entry)
            elif entry['class'].lunch == 'C':
                app.logger.debug(f"Processing C lunch for {entry['class'].name}: class first, then lunch")
                entry['end'] = lunchtime['start']
            break
    return schedule
