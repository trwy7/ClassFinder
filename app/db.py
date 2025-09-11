"""
This file contains the database models for the application. 
It also contains a function to clean up the database by removing expired tokens and schedules. 
Before directly using the database, check if there is already a utility function that does what you want.
"""

from datetime import datetime, timedelta
import os
import uuid
from flask_sqlalchemy import SQLAlchemy
from app import app

db_path = os.environ.get("DB_PATH", "sqlite:///db.sqlite3" if not app.config.get("TESTING") else "sqlite:///:memory:")
if db_path == "sqlite:///:memory:":
    app.logger.info("Using in-memory database, probably for testing purposes. Data will not be saved.")
app.config["SQLALCHEMY_DATABASE_URI"] = db_path
db = SQLAlchemy(app)


# if not os.path.exists(db_path):
#     os.makedirs(db_path)
user_class_association = db.Table(
    "user_class",
    db.Model.metadata,
    db.Column(
        "user_id", db.String(20), db.ForeignKey("user.id"), primary_key=True
    ),
    db.Column("class_id", db.String(20), db.ForeignKey("class.id"), primary_key=True),
)


class User(db.Model):
    """
    A user of the application.

    Attributes:
        id (str): The UUID of the user.
        username (str): The username of the user.
        email (str): The email of the user.
        password (str): The hashed password of the user.
        classes (list): The classes the user is in.
        created_at (datetime): The time the user was created.
        created_by (str): The user who created the user.
        role (str): The role of the user.
        tokens (list): The tokens the user has.
    """
    id = db.Column(db.String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False)
    classes = db.relationship(
        "Class", secondary=user_class_association, backref="users", lazy=True
    )
    created_at = db.Column(db.DateTime, default=datetime.now)
    created_by = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    tokens = db.relationship("Token", backref="user", lazy=True)
    requires_username_change = db.Column(db.Boolean, nullable=False, default=False)
    color_hue = db.Column(db.String(3), nullable=True, default=None) # Format "0-360", everything else is handled by the frontend

    def __str__(self):
        return self.username

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Class(db.Model):
    """
    A class in the application.

    Attributes:
        id (str): The ID of the class.
        name (str): The name of the class.
        room (str): The room the class is in.
        period (str): The period the class is in.
        canvasid (int): The ID of the class in Canvas.
        lunch (str): The lunch the class is in.
        created_by (str): The user who created the class.
        verified (bool): Whether the class has been verified.
    """
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    room = db.Column(db.String(7), nullable=False)
    period = db.Column(db.String(10), nullable=False)
    canvasid = db.Column(db.Integer, nullable=True, default=None)
    lunch = db.Column(db.String(1), nullable=True, default=None)
    created_by = db.Column(db.String(36), nullable=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    teacher = db.Column(db.String(100), nullable=False)
    campus_name = db.Column(db.String(100), nullable=False)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Class {self.name} ({self.id})>"

class Token(db.Model):
    """
    A token for the application.

    Attributes:
        token (str): The token string.
        user_id (str): The user the token is for.
    """
    token = db.Column(db.String(60), primary_key=True, unique=True, nullable=False)
    user_id = db.Column(db.String(20), db.ForeignKey("user.username"), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    expire = db.Column(db.DateTime, nullable=True, default=lambda: datetime.now() + timedelta(days=8))
    scopes = db.Column(db.Text, nullable=True, default=None)
    granted_to = db.Column(db.String(255), nullable=True, default=None)

    def __str__(self):
        return self.token + " for " + self.user_id

    def __repr__(self):
        return f"<Token {self.token} ({self.user_id})>"


class Schedule(db.Model):
    """
    A schedule for the application.

    Attributes:
        day (datetime): The day the schedule is for.
        type (int): The type of schedule.
    """
    day = db.Column(db.Date, primary_key=True, nullable=False, unique=True)
    type = db.Column(db.Integer, nullable=False)

    def __str__(self):
        return self.day.strftime("%Y-%m-%d") + " is " + self.type

    def __repr__(self):
        return f"<Schedule {self.day} ({self.type})>"


def db_cleanup():
    """
    Clean up the database by removing everything expired and fix any issues.

    Returns:
        None
    """
    expired_tokens = db.session.query(Token).filter(Token.expire is not None, Token.expire < datetime.now())
    expired_schedules = db.session.query(Schedule).filter(Schedule.day < datetime.now().date())

    expired_tokens_count = expired_tokens.delete(synchronize_session=False)
    expired_schedules_count = expired_schedules.delete(synchronize_session=False)

    app.logger.debug(f"Deleted {expired_tokens_count} expired tokens.")
    if expired_schedules_count == 0:
        app.logger.debug(f"Deleted {expired_schedules_count} expired schedules.")
    else:
        app.logger.info(f"Deleted {expired_schedules_count} expired schedules.")
        
    calendar_tokens = db.session.query(Token).filter(Token.scopes == "calendar")
    for token in calendar_tokens:
        token.expire = None
    db.session.commit()

with app.app_context():
    db.create_all()
    db.session.commit()
