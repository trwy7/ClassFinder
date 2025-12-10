"""
Allows users to reset their password.
"""
from flask import render_template, request, redirect, url_for
from app import app
from app.utilities.config import devmode
from app.utilities.users import get_user_by_email, create_token, change_password
from app.utilities.validation import validate_email
from app.utilities.email import send_email, create_reset_email_id, check_reset_email_id
from app.utilities.responses import error_response, success_response


@app.route("/resetpassword")
def reset_password():
    """
    Display the reset password page.
    """
    return render_template("resetpassword.html")


@app.route("/resetpassword", methods=["POST"])
def reset_password_post():
    """
    Handle the reset password form submission.
    """
    email = request.json.get("email")
    if not validate_email(email):
        return error_response("Invalid email"), 400
    user = get_user_by_email(email)
    if user is None:
        return error_response("User not found"), 400
    remailid = create_reset_email_id(email)
    send_email(
        email=email,
        subject="Reset your password",
        message="Reset your password at "
        + url_for(
            "reset_password_confirm",
            _external=True,
            emailid=remailid,
        ),
    )
    return success_response("Email sent", {"emailid": remailid} if app.config['TESTING'] else {}), 200


@app.route("/resetpassword/<emailid>")
def reset_password_confirm(emailid):
    """
    Confirm the reset password request.
    """
    email = check_reset_email_id(emailid)
    if email is None:
        return redirect(url_for("reset_password"))
    user = get_user_by_email(email)
    if user is None:
        return redirect(url_for("reset_password")), 400
    return render_template("resetpassword_final.html", user=user)


@app.route("/resetpassword/<emailid>", methods=["POST"])
def reset_password_confirm_post(emailid):
    """
    Handle the final reset password step.
    """
    email = check_reset_email_id(emailid)
    if email is None:
        return error_response("Invalid email id"), 400
    password = request.json.get("password")
    user = get_user_by_email(email)
    if user is None:
        return error_response("User not found"), 400
    change_password(user, password)
    response = success_response("Password changed")
    response.set_cookie(
            "token",
            create_token(user.username, 'refresh').token,
            httponly=True,
            samesite="Lax",
            secure=not devmode,
            max_age=604800,
        )
    return response, 200
