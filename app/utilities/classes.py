"""
This module contains utility functions for managing courses, as well as a users relationship with courses.
"""
from datetime import datetime
import typing
import random
from app.utilities.times import get_day_schedule, classtime_dict, get_classtimes
from app.db import User, Class, db
from app import app

neededperiods = []
lunchperiods = []
for times in classtime_dict.values():
    for ctime in times.classtimes:
        if ctime.lunchactive:
            lunchperiods.append(ctime.period)
        neededperiods.append(ctime.period)
lunchperiods = list(set(lunchperiods))
neededperiods = sorted(set(neededperiods))
# TODO: Move most of these functions to a function within a course class

def get_current_period(include_delay: bool=True):
    """
    Determine the current period.
    """
    dsched = get_day_schedule(None, include_delay=include_delay)
    current_time = datetime.now().time()
    for ct in dsched:
        if ct.start <= current_time <= ct.end:
            return ct
    return None


def get_user_current_period(user: User):
    """
    Determine the user's current period and lunch status.
    """
    dsched = get_day_schedule(user)
    current_time = datetime.now().time()
    for ct in dsched:
        if ct.start <= current_time <= ct.end:
            return ct
    return None

def search_classes(name: str=None, room: str=None, period: int=None, teacher: str=None):
    """
    Search for classes based on the provided criteria.

    Args:
        name (str, optional): The name of the class to search for.
        room (str, optional): The room of the class to search for.
        period (int, optional): The period of the class to search for.
    Returns:
        list[Class]: A list of classes that match the search criteria.
    """
    query = db.session.query(Class)
    if name:
        query = query.filter(Class.name.ilike(f"%{name}%"))
    if room:
        query = query.filter_by(room=room)
    if period is not None:
        query = query.filter_by(period=period)
    results = query.all()
    app.logger.debug(f"Search results for name={name}, room={room}, period={period}, teacher={teacher}: {[c.name for c in results]}")
    return results

def get_today_courses(user: User, day: int = None):
    """
    Retrieve the list of courses for the given user that are scheduled for today.

    Args:
        user (User): The user object containing information about the user's classes.

    Returns:
        list: A list of courses that the user has scheduled for today.
    """
    app.logger.debug(f"Retrieving today's courses for user {user.username}")
    user_periods = list(dict.fromkeys([time.period for time in get_classtimes(day)]))
    app.logger.debug(f"User {user.username} periods: {user_periods}")
    newcourses = []
    for course in user.classes:
        if course.period in user_periods:
            app.logger.debug(f"Adding course {course.name} for period {course.period}")
            newcourses.append(course)
    # Sort according to the user_periods dict
    newcourses.sort(key=lambda x: user_periods.index(x.period))
    app.logger.debug(
        f"Today {user.username}: {[course.name for course in newcourses]}"
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
    if room == "PTECH" or room.startswith("PTECH-"):
        app.logger.debug("Generating unique ID for PTECH class")
        nid = f"PTECH{random.randint(0, 9999)}p{period}"
        while get_course_by_id(nid):
            nid = f"PTECH{random.randint(0, 9999)}p{period}"
    if campusname is None:
        campusname = name
    app.logger.debug(f"Adding class {name} with ID {nid}")
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
    if course in user.classes:
        app.logger.debug(f"User {user.username} is already in class {course.name}")
        return user
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
    for user in course.users:
        user.classes.remove(course)
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
