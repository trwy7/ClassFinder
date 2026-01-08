"""
Allows users to register using their email.
"""
from flask import render_template, request, url_for, redirect
from app import app
from app.utilities.email import send_email, create_email_id, check_email_id
from app.utilities.users import create_user, check_email, get_user_count, create_token, get_user
from app.utilities.validation import validate_email, validate_username
from app.addons.limiter import limiter
from app.utilities.responses import error_response, success_response
from app.utilities.config import devmode

@app.route("/register")
def register():
    """
    Display the registration page.
    """
    return render_template("register.html", devmode=devmode)


@app.route("/register", methods=["POST"])
@limiter.limit("2/minute;6/hour")
def register_post():
    """
    Handle the registration form submission.
    """
    email = request.json.get("email")
    if check_email(email):
        return error_response("Already taken"), 400
    if not validate_email(email):
        app.logger.debug(f"Invalid email attempted during registration: {email}")
        return error_response("Invalid email, use your school provided email."), 400
    app.logger.info(f"Registering new user with email: {email}")
    pname = email.split(".")[0].capitalize()
    emailid = create_email_id(email)
    send_email(
        email=email,
        subject="Confirm your Chronis account",
        message=f"""Hello {pname}!

        Please confirm your Chronis account by visiting the link below:
        {url_for("register_confirm", _external=True, emailid=emailid, _scheme="https")}

        If you did not request this, no action is needed.
        """ # TODO: Make this look better, while trying to not make it go to spam
    )
    if app.config.get("TESTING"):
        app.logger.info(f"Test mode: returning emailid {emailid}")
        return success_response("Email sent", {"emailid": emailid}), 200
    return success_response("Email sent"), 200


@app.route("/register/<emailid>")
def register_confirm(emailid):
    """
    Confirm the email address.
    """
    email = check_email_id(emailid)
    if email is None:
        return redirect(url_for("register"))
    return render_template("register_final.html", email=email)


@app.route("/register/<emailid>", methods=["POST"])
def register_confirm_post(emailid):
    """
    Handle the final registration step.
    """
    email = check_email_id(emailid)
    if email is None:
        return error_response("Invalid email id"), 400
    username = request.json.get("username")
    if not validate_username(username):
        return error_response("Invalid username"), 400
    password = request.json.get("password")
    role = "user"
    if get_user_count() == 0:
        role = "admin"
        app.logger.info(f"{username} has become the first user and is now an admin")
    if get_user(username):
        return error_response("Username taken"), 400
    if create_user(username, email, password, role=role, created_by="email"):
        newtoken = create_token(username, 'refresh').token
        response = success_response("User created.") if not app.config.get("TESTING") else success_response("User created.", {"token": newtoken})
        response.set_cookie(
            "token",
            newtoken,
            httponly=True,
            samesite="Lax",
            secure=not devmode,
            max_age=604800,
        )
        check_email_id(emailid, delete=True)
        return response, 200
    return error_response("User creation failed."), 400
