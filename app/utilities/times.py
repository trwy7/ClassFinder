"""
This file contains the functions and data structures for the schedule of the school.
"""

import os
from datetime import date, timedelta, time, datetime
from reportlab.pdfgen import canvas
from app import app
from app.db import Schedule, db, User, Class

now = datetime.now()
class ClassTime:
    """Representation of a class time slot with helpers to access attributes as a mapping."""
    __slots__ = ("start", "end", "period", "passing", "lunchactive")
    def __init__(self, period: str, start: time, end: time, lunchactive: bool):
        self.start = start
        self.end = end
        self.period = period
        self.lunchactive = lunchactive
    def copy(self):
        """Create a copy of the ClassTime instance."""
        return ClassTime(self.period, self.start, self.end, self.lunchactive)
class LunchPeriod:
    """Representation of a lunch period with helpers to access attributes as a mapping."""
    __slots__ = ("start", "end", "period")
    def __init__(self, period: str, start: time, end: time):
        self.period = period
        self.start = start
        self.end = end
    def copy(self):
        """Create a copy of the LunchPeriod instance."""
        return LunchPeriod(self.period, self.start, self.end)

class UserClassTime:
    """Container for a specific user's class time, that can include modifications."""
    __slots__ = ("start", "end", "period", "passing", "lunchactive", "mods", "course", "lunch", "original_classtime")
    def __init__(self, classtime: ClassTime, course: Class=None, passing: tuple=False, mods: list=None, period: str=None):
        if mods is None:
            mods = []
        if mods and passing:
            raise ValueError("Mods should not be applied to passing times.")
        mod_start = classtime.start if not passing else passing[0]
        mod_end = classtime.end if not passing else passing[1]
        for mod in mods:
            if mod[2] == "start":
                if isinstance(mod[3], timedelta):
                    mod_start = (datetime.combine(date.today(), mod_start) + mod[3]).time()
                elif isinstance(mod[3], time):
                    mod_start = mod[3]
            elif mod[2] == "end":
                if isinstance(mod[3], timedelta):
                    mod_end = (datetime.combine(date.today(), mod_end) + mod[3]).time()
                elif isinstance(mod[3], time):
                    mod_end = mod[3]
        self.start = mod_start
        self.end = mod_end
        self.period = classtime.period if period is None else period
        self.passing = bool(passing)
        self.lunchactive = classtime.lunchactive and not passing
        self.mods = mods
        self.course = course
        self.lunch = course.lunch if course else None
        self.original_classtime = classtime.copy()

class DaySchedule:
    """Container for a day's schedule that supports attribute and mapping access."""
    __slots__ = ("name", "classtimes", "lunchtimes")
    def __init__(self, name: str, classtimes: list[ClassTime], lunchtimes: list[LunchPeriod]):
        self.name = name
        self.classtimes = classtimes
        self.lunchtimes = lunchtimes

classtime_dict = {
    0: DaySchedule("Monday", [
        ClassTime("1", time(8, 0), time(9, 45), False),
        ClassTime("3", time(9, 50), time(11, 30), False),
        ClassTime("5", time(11, 35), time(13, 45), True),
        ClassTime("7", time(13, 50), time(15, 30), False),
    ], [
        LunchPeriod("A", time(11, 35), time(12, 5)),
        LunchPeriod("B", time(12, 15), time(12, 45)),
        LunchPeriod("C", time(13, 10), time(13, 45)),
    ]),
    1: DaySchedule("Tuesday", [
        ClassTime("2", time(8, 0), time(9, 45), False),
        ClassTime("4", time(9, 50), time(11, 30), False),
        ClassTime("6", time(11, 35), time(13, 45), True),
        ClassTime("8", time(13, 50), time(15, 30), False),
    ], [
        LunchPeriod("A", time(11, 35), time(12, 5)),
        LunchPeriod("B", time(12, 15), time(12, 45)),
        LunchPeriod("C", time(13, 10), time(13, 45)),
    ]),
    2: DaySchedule("Wednesday", [
        ClassTime("1", time(8, 0), time(9, 20), False),
        ClassTime("3", time(9, 25), time(10, 45), False),
        ClassTime("Access", time(10, 50), time(12, 0), False),
        ClassTime("5", time(12, 5), time(14, 5), True),
        ClassTime("7", time(14, 10), time(15, 30), False),
    ], [
        LunchPeriod("A", time(12, 5), time(12, 35)),
        LunchPeriod("B", time(12, 40), time(13, 10)),
        LunchPeriod("C", time(13, 30), time(14, 5)),
    ]),
    3: DaySchedule("Thursday", [
        ClassTime("2", time(8, 0), time(9, 20), False),
        ClassTime("4", time(9, 25), time(10, 45), False),
        ClassTime("Access", time(10, 50), time(12, 0), False),
        ClassTime("6", time(12, 5), time(14, 5), True),
        ClassTime("8", time(14, 10), time(15, 30), False),
    ], [
        LunchPeriod("A", time(12, 5), time(12, 35)),
        LunchPeriod("B", time(12, 40), time(13, 10)),
        LunchPeriod("C", time(13, 30), time(14, 5)),
    ]),
    4: DaySchedule("Friday", [
        ClassTime("1", time(8, 0), time(8, 45), False),
        ClassTime("2", time(8, 50), time(9, 35), False),
        ClassTime("3", time(9, 40), time(10, 25), False),
        ClassTime("4", time(10, 30), time(11, 15), False),
        ClassTime("5", time(11, 20), time(13, 0), True),
        ClassTime("6", time(13, 5), time(13, 50), False),
        ClassTime("7", time(13, 55), time(14, 40), False),
        ClassTime("8", time(14, 45), time(15, 30), False),
    ], [
        LunchPeriod("A", time(11, 20), time(11, 50)),
        LunchPeriod("B", time(11, 55), time(12, 25)),
        LunchPeriod("C", time(12, 25), time(13, 0)),
    ]),
    5: DaySchedule("No school", [], []),
    6: DaySchedule("No school", [], []),
    7: DaySchedule("Early Release Blue", [
        ClassTime("1", time(8, 0), time(8, 55), False),
        ClassTime("3", time(9, 0), time(9, 55), False),
        ClassTime("5", time(10, 0), time(10, 55), False),
        ClassTime("7", time(11, 0), time(11, 55), False),
    ], []),
    8: DaySchedule("Early Release Gold", [
        ClassTime("2", time(8, 0), time(8, 55), False),
        ClassTime("4", time(9, 0), time(9, 55), False),
        ClassTime("6", time(10, 0), time(10, 55), False),
        ClassTime("8", time(11, 0), time(11, 55), False),
    ], []),
    9: DaySchedule("Development", [
        ClassTime("3", (now + timedelta(minutes=10)).time(), (now + timedelta(minutes=15)).time(), False),
        ClassTime("4", (now + timedelta(minutes=15)).time(), (now + timedelta(minutes=20)).time(), False),
    ], []),
    10: DaySchedule("Delayed Monday", [
        ClassTime("1", time(10, 0), time(11, 15), False),
        ClassTime("3", time(11, 20), time(12, 30), False),
        ClassTime("5", time(12, 35), time(14, 15), True),
        ClassTime("7", time(14, 20), time(15, 30), False),
    ], [
        LunchPeriod("A", time(12, 35), time(13, 5)),
        LunchPeriod("B", time(13, 10), time(13, 40)),
        LunchPeriod("C", time(13, 45), time(14, 15)),
    ]),
    11: DaySchedule("Delayed Tuesday", [
        ClassTime("2", time(10, 0), time(11, 15), False),
        ClassTime("4", time(11, 20), time(12, 30), False),
        ClassTime("6", time(12, 35), time(14, 15), True),
        ClassTime("8", time(14, 20), time(15, 30), False),
    ], [
        LunchPeriod("A", time(12, 35), time(13, 5)),
        LunchPeriod("B", time(13, 10), time(13, 40)),
        LunchPeriod("C", time(13, 45), time(14, 15)),
    ]),
    12: DaySchedule("Delayed Wednesday", [
        ClassTime("1", time(10, 0), time(11, 5), False),
        ClassTime("3", time(11, 10), time(12, 10), False),
        ClassTime("Access", time(12, 15), time(12, 45), False),
        ClassTime("5", time(12, 50), time(13, 20), True),
        ClassTime("7", time(14, 30), time(15, 30), False),
    ], [
        LunchPeriod("A", time(12, 50), time(13, 20)),
        LunchPeriod("B", time(13, 25), time(13, 55)),
        LunchPeriod("C", time(14, 0), time(14, 30)),
    ]),
    13: DaySchedule("Delayed Thursday", [
        ClassTime("2", time(10, 0), time(11, 5), False),
        ClassTime("4", time(11, 10), time(12, 10), False),
        ClassTime("Access", time(12, 15), time(12, 45), False),
        ClassTime("6", time(12, 50), time(13, 20), True),
        ClassTime("8", time(14, 30), time(15, 30), False),
    ], [
        LunchPeriod("A", time(12, 50), time(13, 20)),
        LunchPeriod("B", time(13, 25), time(13, 55)),
        LunchPeriod("C", time(14, 0), time(14, 30)),
    ]),
    14: DaySchedule("Delayed Friday", [
        ClassTime("1", time(10, 0), time(10, 30), False),
        ClassTime("2", time(10, 35), time(11, 0), False),
        ClassTime("3", time(11, 5), time(11, 30), False),
        ClassTime("4", time(11, 35), time(12, 0), False),
        ClassTime("5", time(12, 5), time(13, 45), True),
        ClassTime("6", time(13, 50), time(14, 20), False),
        ClassTime("7", time(14, 25), time(14, 55), False),
        ClassTime("8", time(15, 0), time(15, 30), False),
    ], [
        LunchPeriod("A", time(12, 5), time(12, 35)),
        LunchPeriod("B", time(12, 40), time(13, 10)),
        LunchPeriod("C", time(13, 15), time(13, 45)),
    ]),
}
del now
readable_days = {did: day.name for did, day in classtime_dict.items()}
day_schedule_cache = {}
# {(user_id, include_delay): (schedule list, day type, user.classes)}
current_day = (-1, None)  # (day int, date)
# classtime 'mods' key
# ("id", "name", "mod",  modvalue)
# id is a string, seperated by dashes
# name is a human-readable name
# mod is either start or end
# modvalue is either a time, or timedelta
# e.x. ("sys-lunch-amid", "During lunch A", "start", time(12, 5))
# e.x. ("usr-custom-start", "Custom start delay", "start", timedelta(minutes=5))
# e.x. ("sys-demo-endearly", "End a class early", "end", timedelta(minutes=-5))
# TODO: Webhooks with custom data? Possibly for ntfy/discord notifications?

bell_delay = 0.0 # pylint: disable=invalid-name # This is not a constant, but it gets flagged as one.

def get_day_schedule(user: User | None, day: date | int | None=None, include_delay: bool = True) -> list:
    """
    Get the schedule for a specific user. Includes any modifications, including PTECH, lunch, and custom mods.

    Args:
        user (User): The user to get the schedule for.
    Returns:
        list: The schedule for the user.
    """
    app.logger.debug(f"Getting schedule for user {user} on day {day}")
    cache_key = user.id if user else "guest"
    cday = get_current_day(day) if isinstance(day, date) or day is None else day
    if (not day) and (cache_key, include_delay) in day_schedule_cache:
        if cday == day_schedule_cache[(cache_key, include_delay)][1] and \
          list(user.classes if user else []) == day_schedule_cache[(cache_key, include_delay)][2]:
            app.logger.debug(f"Using cached schedule for user {cache_key}")
            return day_schedule_cache[(cache_key, include_delay)][0]
    schedule = []
    classtimes = get_classtimes(day=cday)
    lcts = []
    # Get what lunch the class has
    app.logger.debug(f"Length of classtimes before lunch processing: {len(classtimes)}")
    for orct in classtimes:
        ct = orct.copy()
        dadd = False
        if ct.lunchactive and user:
            app.logger.debug(f"Class time {ct.period} has lunch active for user {user}")
            for course in user.classes:
                if course.period == ct.period:
                    app.logger.debug(f"Found class {course.id} for user {user}")
                    if course.lunch == "A":
                        # Shorten class time to start at lunch A end
                        clt = get_lunchtimes(day=cday)[0]
                        app.logger.debug(f"User {user} has lunch A for class {course.id} in period {ct.period}")
                        ct.start = clt.end
                        # Add lunch to the schedule
                        lunch_ct = UserClassTime(ct, course=course, passing=(clt.start, clt.end), period="Lunch")
                        lcts.append(lunch_ct)
                        lcts.append(ct)
                        dadd = True
                    elif course.lunch == "B":
                        # Split class time into two parts, and put lunch in between
                        clt = get_lunchtimes(day=cday)[1]
                        app.logger.debug(f"User {user} has lunch B for class {course.id} in period {ct.period}")
                        first_part = ct.copy()
                        first_part.end = clt.start
                        second_part = ct.copy()
                        second_part.start = clt.end
                        # Add first part
                        lcts.append(first_part)
                        # Add lunch to the schedule
                        lunch_ct = UserClassTime(ct, course=course, passing=(clt.start, clt.end), period="Lunch")
                        lcts.append(lunch_ct)
                        # Add second part
                        lcts.append(second_part)
                        dadd = True
                    elif course.lunch == "C":
                        # Shorten class time to end at lunch C start
                        app.logger.debug(f"User {user} has lunch C for class {course.id} in period {ct.period}")
                        clt = get_lunchtimes(day=cday)[2]
                        ct.end = clt.start
                        # Add lunch to the schedule
                        lunch_ct = UserClassTime(ct, course=course, passing=(clt.start, clt.end), period="Lunch")
                        lcts.append(ct)
                        lcts.append(lunch_ct)
                        dadd = True
        if not dadd:
            lcts.append(ct)
    app.logger.debug(f"Class times after lunch processing: {len(lcts)}")
    for ct in lcts: # We re-add passing times later # TODO: this is worth a whole app rewrite
        if ct.period == "Lunch":
            schedule.append(ct)
            continue
        mods = []
        user_class = None
        for course in user.classes if user else []:
            if course.period == ct.period:
                user_class = course
                break
        apply_bell_delay_start = True
        apply_bell_delay_end = True
        # PTECH check
        if user_class and "PTECH" in user_class.room:
            mods.append(("sys-ptech-start", "PTECH classes start late", "start", timedelta(minutes=5)))
            mods.append(("sys-ptech-end", "PTECH classes end early", "end", timedelta(minutes=-5)))
            apply_bell_delay_start = False
            apply_bell_delay_end = False
        # Check for custom delays
        if user and user.custom_start_delay is not None:
            mods.append(("usr-custom-start", "User custom start delay", "start", timedelta(seconds=user.custom_start_delay)))
            apply_bell_delay_start = False
        if user and user.custom_end_delay is not None:
            mods.append(("usr-custom-end", "User custom end delay", "end", timedelta(seconds=user.custom_end_delay)))
            apply_bell_delay_end = False
        # Add bell delay
        if include_delay and bell_delay != 0.0 and apply_bell_delay_start:
            mods.append(("sys-bell-delay-start", "Bell delay start", "start", timedelta(seconds=bell_delay)))
        if include_delay and bell_delay != 0.0 and apply_bell_delay_end:
            mods.append(("sys-bell-delay-end", "Bell delay end", "end", timedelta(seconds=bell_delay)))
        uct = UserClassTime(ct, course=user_class, mods=mods)
        # Get the last added class time to determine passing time
        if schedule:
            last_ct = schedule[-1]
            passing_start = last_ct.end
            passing_end = uct.start
            if passing_start != passing_end:
                passing_uct = UserClassTime(ct, course=None, passing=(passing_start, passing_end))
                schedule.append(passing_uct)
        else:
            passing_uct = UserClassTime(ct, course=None, passing=(time(0, 0), uct.start))
            schedule.append(passing_uct)
        schedule.append(uct)
    # Cache
    day_schedule_cache[(cache_key, include_delay)] = (schedule, cday, list(user.classes if user else []))
    return schedule

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
    global current_day  # pylint: disable=global-statement
    odaymod = False
    if oday is not None:
        app.logger.debug(f"Getting simulated day {oday}")
        day = oday
        odaymod = True
    else:
        app.logger.debug("Getting current day")
        day = datetime.today().date()
    if current_day[1] == day:
        app.logger.debug(f"Using cached current day: {current_day[0]} from date {current_day[1]}")
        return current_day[0]
    with app.app_context():
        app.logger.debug(f"Getting schedule for {day}")
        schedule = Schedule.query.filter_by(day=day).first()
    if schedule:
        app.logger.debug(f"Schedule found for {day}: {schedule.type}")
        if not odaymod:
            current_day = (schedule.type, day)
        return schedule.type
    app.logger.debug(f"No schedule found for {day}, using current day")
    if not odaymod:
        current_day = (day.weekday(), day)
    return day.weekday()

def get_classtimes(day: int=None):
    """
    Get the class times for the current day.

    Returns:
        list: A list of class times.
    """
    return classtime_dict[get_current_day() if day is None else day].classtimes

def get_classtime_by_period(period: str, passing: bool=False, day: int=None, user: User=None):
    """
    Get the class time for a specific period.

    Args:
        period (str): The period to get the class time for.
        passing (bool): Whether to get the passing time.

    Returns:
        dict: The class time for the specified period.
    """
    classtimes = get_day_schedule(user, day)
    for classtime in classtimes:
        if classtime.period == period and classtime.passing == passing:
            return classtime
    return None

def get_lunchtimes(day: int=None):
    """
    Get the lunch times for the current day.

    Returns:
        dict: A dictionary of lunch
    """
    return classtime_dict[get_current_day() if day is None else day].lunchtimes

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
    global current_day  # pylint: disable=global-statement
    app.logger.info(f"Setting schedule for {start} to {end}")
    # If today is within the range, update current_day
    today = datetime.today().date()
    if start <= today <= end:
        current_day = (simulated_day, today)
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

def create_schedule_pdf(user: User):
    """
    Create a PDF of the schedule for a user.

    Args:
        user (User): The user to create the schedule for.
    Returns:
        str: The path to the created PDF file.
    """
    # AI territory
    file_path = f"/tmp/{user.id if user else 'schedule'}CFSchedule.pdf"
    c = canvas.Canvas(file_path)
    c.setTitle("School Schedule")
    c.setFont("Helvetica", 12)
    # FIXME: Goes off the page when you only have B lunch
    dayorder_front = ["0", "1", "2", "3", "4", "7"]
    dayorder_back = ["10", "11", "12", "13", "14", "8"]

    page_width = c._pagesize[0]  # pylint: disable=protected-access
    layout = {"margin": 50, "start_y": 800, "header_gap": 20, "line_gap": 15, "block_gap": 10}
    fonts = {"header": ("Helvetica-Bold", 14), "body": ("Helvetica", 12)}

    def _draw_day(day_id: int, y_pos: int, right_align: bool = False) -> int:
        cdata = classtime_dict[day_id]
        csched = get_day_schedule(user, day=day_id)

        draw_text = c.drawRightString if right_align else c.drawString
        base_x = (page_width - layout["margin"]) if right_align else layout["margin"]
        body_x = (base_x - 5) if right_align else (base_x + 5)

        c.setFont(*fonts["header"])
        draw_text(base_x, y_pos, cdata.name)
        y_pos -= layout["header_gap"]

        c.setFont(*fonts["body"])
        for ct in csched:
            if ct.passing and not ct.period == "Lunch":
                continue
            class_name = ct.course.name if ct.course else "Free Period"
            start_str = ct.start.strftime("%I:%M %p")
            end_str = ct.end.strftime("%I:%M %p")
            if ct.period == "Lunch":
                draw_text(body_x, y_pos, f"Lunch ({start_str} - {end_str})")
            else:
                roomtext = 'room ' + ct.course.room if 'PTECH' not in ct.course.room else ct.course.room
                periodtext = f"Period {ct.period}: " if ct.period.isdigit() else ""
                draw_text(body_x, y_pos, f"{periodtext}{class_name} in {roomtext} ({start_str} - {end_str})")
            y_pos -= layout["line_gap"]

        y_pos -= layout["block_gap"]
        return y_pos

    # Page 1: front days, record each block's top y so the back page can reuse it.
    y = layout["start_y"]
    front_y_positions: list[int] = []
    for did in map(int, dayorder_front):
        front_y_positions.append(y)
        y = _draw_day(did, y)

    # Page 2: back days, drawn starting at the same y positions as their front counterparts.
    c.showPage()
    c.setTitle("School Schedule")
    c.setFont("Helvetica", 12)

    for y_start, did in zip(front_y_positions, map(int, dayorder_back), strict=True):
        _draw_day(did, y_start, right_align=True)

    c.save()
    return file_path
