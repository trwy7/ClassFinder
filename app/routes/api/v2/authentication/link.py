"""
This module handles the linking of external applications for authentication purposes.
"""

import random
from flask import request, render_template, redirect, url_for
from app import app
from app.utilities.responses import success_response, error_response
from app.utilities.users import create_token, require_login
from app.addons.limiter import limiter


link_codes = {}

@app.route("/api/v2/link/create", methods=["POST", "GET"])
@limiter.limit("5/minute")
def create_link_code():
    """
    Create a link code for an external application to use to link to the user's account.
    """
    code = random.randint(100000, 999999)
    link_codes[code] = {"ip": request.remote_addr, "user": None}
    app.logger.debug(f"Code {code} generated for IP {request.remote_addr[:3] + '*' * (len(request.remote_addr) - 3)}")
    return success_response("Code generated", {"code": code})

@app.route("/api/v2/link/verify", methods=["GET"])
def verify_link_code():
    """
    Verify that a link code is valid, and return the user's information if it is.
    """
    code = int(request.args.get("code"))
    app.logger.debug(f"Verifying code {code} for IP {request.remote_addr[:3] + '*' * (len(request.remote_addr) - 3)}")
    if code not in link_codes:
        app.logger.debug(f"Code {code} not found: {link_codes}")
        return error_response("Invalid code"), 404
    if link_codes[code]["ip"] != request.remote_addr:
        return error_response("Code not generated from this IP"), 403
    if link_codes[code]["user"] is None:
        return success_response("Code verified", {"user": None}), 204
    ctype = request.args.get("type", "api")
    if ctype not in ["api", "app", "refresh"]:
        return error_response("Invalid type"), 400
    token = create_token(link_codes[code]["user"].username, ctype)
    nuser = link_codes[code]["user"].username
    del link_codes[code]
    response = success_response("Code verified", {"user": nuser, "token": token.token})
    response.set_cookie("token", token.token, httponly=True, samesite="Lax", secure=True, max_age=604800)
    app.logger.info(f"User {nuser} linked to {ctype} with code {code}")
    return response

@app.route("/link")
def redir_link():
    """
    Redirect to the link page.
    """
    return redirect(url_for("account_link"))

@app.route("/account/link")
@require_login
def account_link():
    """
    The account linking page.
    """
    user = request.user
    return render_template("link.html", user=user)

@app.route("/account/link/<int:code>")
@require_login
def account_link_code(code):
    """
    Link the user's account to an external application.
    """
    user = request.user
    if code not in link_codes:
        return redirect(url_for("account_link"))
    return render_template("finallink.html", user=user, code=code, codedata=link_codes[code], ip=request.remote_addr)

@app.route("/account/link/<int:code>", methods=["POST"])
@require_login
def account_link_confirm(code):
    """
    Confirm the linking of the user's account to an external application.
    """
    user = request.user
    if code not in link_codes:
        return error_response("Invalid code"), 404
    link_codes[code]["user"] = user
    return success_response("Code confirmed")
