"""
This module contains utility functions for managing courses, as well as a users relationship with courses.
"""
from datetime import datetime, timedelta
import typing
import random
from app.utilities.times import get_classtimes, get_lunchtimes, classtime_dict
from app.db import User, Class, db
from app import app

neededperiods = []
lunchperiods = []
for day, times in classtime_dict.items():
    for ctime in times['classtimes']:
        if ctime["lunchactive"] and ctime["period"] not in lunchperiods:
            lunchperiods.append(ctime["period"])
        neededperiods.append(ctime["period"])
lunchperiods = list(set(lunchperiods))
# TODO: Move most of these functions to a function within a course class

def get_current_period():
    """
    Determine the current period.
    Returns:
        dict: A dictionary containing the current period information, including:
            - "lunchactive" (bool): Whether this periods lunch should be counted for schedule purposes.
            - "period" (str): The current period.
            - "end" (datetime.time): The end time of the current period.
            - "start" (datetime.time): The start time of the current period.
    """
    current_time = datetime.now().time()
    for time in get_classtimes():
        app.logger.debug(f"Checking period {time['period']}")
        if time["start"] <= current_time <= time["end"]:
            app.logger.debug(f"Current period is {time['period']}")
            return time.copy()
    app.logger.debug("No current period")
    return None


def get_user_current_period(user: User):
    """
    Determine the user's current period and lunch status.
    Args:
        user (User): The user object containing class information.
    Returns:
        dict: A dictionary containing the current period information, including:
            - "lunch" (str or None): The lunch period if active, otherwise None.
            - "period" (str): The current period.
            - "end" (datetime.time): The end time of the current period.
            - "start" (datetime.time): The start time of the current period.
            - "course" (Course or None): The current course if found, otherwise None.
    Logs:
        Various debug information about the current period, lunch status, and course checking.
    """
    current_time = datetime.now().time()
    current_period = get_current_period()
    lunchtimes = get_lunchtimes()
    app.logger.debug(f"Current period: {current_period}")
    if current_period is None:
        app.logger.debug("No current period")
        return None
    if not current_period["lunchactive"]:
        app.logger.debug("Lunch not active")
        for course in user.classes:
            if course.period == current_period["period"]:
                app.logger.debug(f"Found course {course.name} for period {current_period['period']}")
                returncourse = course
                if "PTECH" in course.room:
                    app.logger.debug(f"User {user.username} is in a PTECH class.")
                    modified_start_time = datetime.combine(datetime.today(), current_period["start"])
                    modified_end_time = datetime.combine(datetime.today(), current_period["end"])
                    app.logger.debug(f"Original start time: {modified_start_time}, Original end time: {modified_end_time}, it is currently {datetime.now()}")
                    # Start the screwery
                    if current_period['passing']:
                        # Passing periods get 5 more minutes
                        app.logger.debug("We are in a passing period, so PTECH gets 5 extra minutes")
                        modified_end_time += timedelta(minutes=5)
                    elif (datetime.now() < (modified_start_time + timedelta(minutes=5))):
                        # Making sure we arent in the extended time
                        app.logger.debug("We are in the first 5 minutes of normal class, so PTECH starts now")
                        modified_end_time = modified_start_time + timedelta(minutes=5)
                        modified_start_time -= timedelta(minutes=5)
                    elif (datetime.now() > (modified_end_time - timedelta(minutes=5))):
                        # We are in the last 5 minutes of normal class, so PTECH leaves now
                        app.logger.debug("We are in the last 5 minutes of normal class, so PTECH leaves now")
                        modified_start_time = modified_end_time - timedelta(minutes=5)
                        lastperiod = get_classtimes()[-1]
                        if lastperiod['start'] == current_period['start']:
                            # Last period of the day, so PTECH leaves at the end of class, we need to just say they have no class
                            app.logger.debug("This is the last period of the day")
                            return None
                        modified_end_time += timedelta(minutes=5)
                        current_period['leavingptech'] = True
                        returncourse = None
                    else:
                        # Normal class time, so PTECH leaves 5 minutes early and starts 5 minutes late
                        app.logger.debug("We are in normal class time, so PTECH leaves 5 minutes early and starts 5 minutes late")
                        modified_start_time += timedelta(minutes=5)
                        modified_end_time -= timedelta(minutes=5)
                    # Save everything back to the dict
                    current_period['start'] = modified_start_time.time()
                    current_period['end'] = modified_end_time.time()
                    app.logger.debug(f"Modified start time: {current_period['start']}, Modified end time: {current_period['end']}")
                return current_period | {"lunch": None, "course": returncourse}
        app.logger.debug(f"No course found for period {current_period['period']} and user {user.username}")
        return current_period | {"lunch": None, "course": None}
    currentcourse = None
    for course in user.classes:
        app.logger.debug(f"Checking course {course.name}")
        if course.period == current_period["period"]:
            app.logger.debug(
                f"Found course {course.name} for period {current_period['period']}"
            )
            currentcourse = course
            break
    if currentcourse is None:
        app.logger.debug(
            f"No course found for period {current_period['period']} and user {user.username}"
        )
        return {
            "lunch": None,
            "period": current_period["period"],
            "end": current_period["end"],
            "start": current_period["start"],
            "course": None,
        }
    if currentcourse.lunch is None:
        app.logger.debug(
            f"User {user.username} is in period {current_period['period']} for course {currentcourse.name}, no lunch has been set."
        )
        return current_period | {"lunch": None, "course": currentcourse}
    if lunchtimes[currentcourse.lunch]["start"] <= current_time <= lunchtimes[currentcourse.lunch]["end"]:
        app.logger.debug(f"User {user.username} is in lunch {currentcourse.lunch}")
        return {
            "lunch": currentcourse.lunch,
            "period": "Lunch",
            "end": lunchtimes[currentcourse.lunch]["end"],
            "start": lunchtimes[currentcourse.lunch]["start"],
            "course": currentcourse,
        }
    if current_time < lunchtimes[currentcourse.lunch]["start"]:
        app.logger.debug(
            f"User {user.username} is in period {current_period['period']} for course {currentcourse.name}, before lunch"
        )
        return {
            "lunch": None,
            "period": current_period["period"],
            "end": lunchtimes[currentcourse.lunch]["start"],
            "start": current_period["start"],
            "course": currentcourse,
        }
    app.logger.debug(
        f"User {user.username} is in period {current_period['period']} for course {currentcourse.name}, after lunch"
    )
    return current_period | {"lunch": None, "course": currentcourse}


def get_today_courses(user: User, day: int = None):
    """
    Retrieve the list of courses for the given user that are scheduled for today.

    Args:
        user (User): The user object containing information about the user's classes.

    Returns:
        list: A list of courses that the user has scheduled for today.
    """
    app.logger.debug(f"Retrieving today's courses for user {user.username}")
    user_periods = [time["period"] for time in get_classtimes(day)]
    app.logger.debug(f"User {user.username} periods: {user_periods}")
    newcourses = []
    for course in user.classes:
        if course.period in user_periods:
            app.logger.debug(f"Adding course {course.name} for period {course.period}")
            newcourses.append(course)
    app.logger.debug(
        f"User {user.username} courses for today: {[course.name for course in newcourses]}"
    )
    return newcourses

def add_class(name: str, period: int, room: str, created_by: str, teacher: str, campusname: str = None, commit: bool = True):
    """
    Add a new class to the database.
    
    Args:
        name (str): The name of the class.
        period (int): The period of the class.
        room (str): The room of the class.
        created_by (str): The user who created the class.
        commit (bool): Whether to commit the changes to the database.

    Returns:
        Class: The newly created class object.
    """
    nid = f"{room}p{period}"
    if room == "PTECH":
        nid = f"PTECH{random.randint(0, 9999)}p{period}"
        while get_course_by_id(nid):
            nid = f"PTECH{random.randint(0, 9999)}p{period}"
    if campusname is None:
        campusname = name
    newclass = Class(
        id=nid,
        name=name,
        room=room,
        period=period,
        created_by=created_by,
        teacher=teacher,
        campus_name=campusname,
    )
    db.session.add(newclass)
    if commit:
        db.session.commit()
    return newclass


def add_user_to_class(user: User, course: Class):
    """
    Adds a user to a class.

    Args:
        user (User): The user to add to the class.
        course (Class): The class to add the user to.

    Returns:
        User: The updated user object.
    """
    user.classes.append(course)
    db.session.commit()
    return user


def remove_user_from_class(user: User, course: Class):
    """
    Removes a user from a class.

    Args:
        user (User): The user to remove from the class.
        course (Class): The class to remove the user from.

    Returns:
        User: The updated user object.
    """
    user.classes.remove(course)
    db.session.commit()
    return user


def remove_class(course: Class):
    """
    Deletes a class from the database.

    Args:
        course (Class): The class to delete.

    Returns:
        None
    """
    db.session.delete(course)
    db.session.commit()


def get_course(period: int, room: str):
    """
    Retrieve a course by period and room.
    
    Args:
        period (int): The period of the course.
        room (str): The room of the course.
        
    Returns:
        Class: The course object if found, otherwise None.
    """
    return db.session.query(Class).filter_by(period=period, room=room).first()


def get_ptech_class(campusname: str, period: int):
    """
    Retrieve a PTECH class by campusname, period, and room.
    
    Args:
        name (str): The name of the PTECH class.
        period (int): The period of the class.
        room (str): The room of the class.
        
    Returns:
        Class: The PTECH class object if found, otherwise None.
    """
    return db.session.query(Class).filter_by(campus_name=campusname, period=period, room="PTECH").first()

def get_course_by_id(classid: str):
    """
    Retrieve a course by id.

    Args:
        id (str): The id of the course.

    Returns:
        Class: The course object if found, otherwise None.
    """
    return db.session.query(Class).filter_by(id=classid).first()


def check_if_class_exists(room: str, period: int):
    """
    Check if a class exists by room and period.
    
    Args:
        room (str): The room of the class.
        period (int): The period of the class.
        
    Returns:
        bool: True if the class exists, otherwise False.
    """
    return get_course(period=period, room=room) is not None


def check_if_user_in_class(user: User, course: Class):
    """
    Check if a user is in a class.

    Args:
        user (User): The user to check.
        course (Class): The class to check.

    Returns:
        bool: True if the user is in the class, otherwise False.
    """
    return course in user.classes


def get_periods_of_user_classes(user: User):
    """
    Retrieve the periods of the user's classes.

    Args:
        user (User): The user object containing class information

    Returns:
        list: A list of periods that the user has classes in.
    """
    return [course.period for course in user.classes]


def set_canvas_id(course: Class, canvasid: int):
    """
    Set the canvas id for a course.
    
    Args:
        course (Class): The course to set the canvas id for.
        canvasid (int): The canvas id to set.
        
    Returns:
        Class: The updated course object.
    """
    app.logger.debug(f"Setting canvas id for {course.name} to {canvasid}")
    course.canvasid = canvasid
    db.session.commit()
    return course

def get_period_for_user(user: User, period: int):
    """
    Get the course for a user in a specific period.

    Args:
        user (User): The user object.
        period (int): The period to check.

    Returns:
        Class: The course object for the user in the specified period, or None if not found.
    """
    for course in user.classes:
        if course.period == period:
            return course
    return None

def set_lunch(course: Class, lunch: typing.Literal["A", "B", "C"]):
    """
    Set the lunch period for a course.

    Args:
        course (Class): The course to set the lunch period for.
        lunch (str): The lunch period to set.

    Returns:
        Class: The updated course object.
    """
    app.logger.debug(f"Setting lunch for {course.name} to {lunch}")
    course.lunch = lunch
    db.session.commit()
    return course

def get_all_courses():
    """
    Retrieve all courses from the database.

    Returns:
        list: A list of all courses in the database.
    """
    return db.session.query(Class).all()
