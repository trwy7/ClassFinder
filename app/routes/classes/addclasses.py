"""
This file contains the routes for adding classes to a user's account.
"""
import asyncio
from flask import render_template, redirect, request, send_from_directory
import better_profanity
from app import app
from app.utilities.other import split_list
from app.utilities.users import verify_user
from app.utilities.classes import (
    add_class,
    add_user_to_class,
    check_if_class_exists,
    get_course,
    check_if_user_in_class,
    get_periods_of_user_classes,
    neededperiods,
)
from app.db import db
from app.utilities.validation import validate_room
from app.utilities.responses import error_response, success_response

@app.route("/addclasses")
@verify_user
def addclasses():
    """
    Checks if the user has all of their classes, and if not, renders the addclasses page.
    """
    user = request.user
    if len(get_periods_of_user_classes(user)) == len(neededperiods):
        app.logger.debug(
            f"User already has all of their classes. ({len(get_periods_of_user_classes(user))}/{len(neededperiods)})"
        )
        return redirect("/")
    return render_template(
        "addcourses.html",
        neededperiods=[
            period
            for period in neededperiods
            if period not in get_periods_of_user_classes(user)
        ],
    )


@app.route("/addclasses", methods=["POST"])
@verify_user(
    onfail=lambda:({"status": "error", "message": "You must be logged in to do that."}, 401)
)
def addclasses_post():
    """
    Adds the classes to the user's account.
    """
    user = request.user
    if len(get_periods_of_user_classes(user)) == len(neededperiods):
        return error_response("You already have all of your classes."), 400
    classes = [
        course.strip() for course in request.json
        if "day: t" not in course.strip().lower()
        and "day: w" not in course.strip().lower()
        and "day: m" not in course.strip().lower()
        and "day: r" not in course.strip().lower()
        and "day: f" not in course.strip().lower()
        and "day: early release- blue" not in course.strip().lower()
        and "day: early release- gold" not in course.strip().lower()
        and course.strip() != ""
        and not course.strip().lower().startswith("start: ")
        and not course.strip().lower().startswith("end: ") # I have not confirmed this is a real value, but just in case
    ]
    if len(classes) % 5 != 0:
        if classes[0].strip() == "Schedule":
            app.logger.debug("Ctrl+A moment")
            classes = classes[5:]
        if len(classes) % 5 != 0:
            app.logger.debug(f"Invalid number of classes: {len(classes)}")
            return (
                error_response(
                    "Make sure you copied your classes from infinite campus, and that you have copied everything."
                ),
                400,
            )
    classes = split_list(classes, 5)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = [process_course(course, user) for course in classes]
    results = loop.run_until_complete(asyncio.gather(*tasks))
    for result in results:
        if result is not None:
            return result
    loop.close()
    # Create another new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    existing_tasks = [process_existing_course(course, user) for course in classes]
    loop.run_until_complete(asyncio.gather(*existing_tasks))
    loop.close()
    db.session.commit()
    return success_response("Classes added successfully."), 200

async def process_existing_course(course, user):
    """Add a user to an existing course."""
    period = course[0].strip()
    room = course[4].strip().replace("Room: ", "")

    # Skip if user already has a class in this period
    user_periods = get_periods_of_user_classes(user)
    if period in user_periods:
        return

    # Get course and add user if not already enrolled
    newclass = get_course(period, room)
    if newclass and not check_if_user_in_class(user, newclass):
        add_user_to_class(user, newclass)


async def process_course(course, user):
    """Process a course and add it to the user's account."""
    # period = course[0].strip()
    # name = course[1].strip().removeprefix("MS ")
    # room = course[4].strip().replace("Room: ", "")

    # # Validate period
    # if period not in neededperiods:
    #     app.logger.debug(f"Invalid period: {period}")
    #     return error_response("Invalid period for a course."), 400

    # # Check if user already has a class in this period
    # user_periods = get_periods_of_user_classes(user)
    # if period in user_periods:
    #     return None

    # # Validate room and name
    # if not validate_room(room):
    #     app.logger.debug(f"Invalid room number: {room}")
    #     return error_response("Invalid room number for a course."), 400

    # if better_profanity.profanity.contains_profanity(name):
    #     app.logger.debug(f"Course name with profanity: {name}")
    #     return error_response("Invalid course name."), 400

    # # Process the class
    # if check_if_class_exists(room, period):
    #     return None

    # # Create class and add user
    # createdclass = add_class(
    #     name, period, room, created_by=user.username, commit=False
    # )
    # add_user_to_class(user, createdclass)
    # return None

@app.route("/addclasses/help.gif")
def addclasses_help():
    """
    Renders the help gif for adding classes.
    """
    return send_from_directory("static", "addclasses.gif")
