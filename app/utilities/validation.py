"""
Provides functions to validate user input.
"""

import re
import better_profanity
from app import app

profanity = better_profanity.Profanity()
try:
    with open("profanity.txt", "r", encoding="UTF-8") as f:
        bwords = f.read().splitlines()
except FileNotFoundError:
    try:
        with open("/profanity.txt", "r", encoding="UTF-8") as f:
            bwords = f.read().splitlines()
    except FileNotFoundError:
        app.logger.warning("profanity.txt not found, using basic matching.")
        bwords = []

def validate_email(email: str):
    """
    Check if an email is valid

    Args:
        email (str): The email to check.
    """
    if len(email) <= 50 and len(email) >= 15 and re.fullmatch(r"[a-z]*\.[a-z]*[0-9]{0,1}(@s.stemk12.org|@stemk12.org)", email):
        app.logger.debug(f"Email '{email}' passed regex validation.")
        # smail = email.split("@")[0]
        # for word in bwords: # Too many false positives
        #     if word.lower() in smail.lower():
        #         app.logger.warning(f"Email '{email}' contains a profane word: {word}")
        #         return False
        app.logger.debug(f"Email '{email}' passed validation.")
        return True
    app.logger.debug(f"Email '{email}' failed validation.")
    return False


def validate_username(username: str):
    """
    Check if a username is valid

    Args:
        username (str): The username
        
    Returns:
        bool: True if the username is valid, False otherwise
    """
    if profanity.contains_profanity(username):
        return False
    if username.lower() in ["admin", "root", "superuser", "moderator", "mod"]:
        return False
    if username.lower().startswith("admin"):
        return False
    pusername = username.strip() \
        .replace("3", "e") \
        .replace("0", "o") \
        .replace("1", "i") \
        .replace("4", "a") \
        .replace("5", "s") \
        .replace("7", "t") \
        .replace("8", "b") \
        .replace("9", "g") \
        .replace("6", "b")
    for word in bwords:
        if word.lower() in pusername.lower():
            app.logger.warning(f"Username '{username}' ({pusername}) contains a profane word: {word}")
            return False
    return re.fullmatch(r"[a-z0-9_]{3,15}", username)
