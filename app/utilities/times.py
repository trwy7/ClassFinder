"""
This file contains the functions and data structures for the schedule of the school.
"""

from datetime import date, timedelta, time, datetime
from reportlab.pdfgen import canvas
from app import app
from app.db import Schedule, db, User

# classtime_dict = {daynumber: {
#   "classtimes": [...],
#   "lunchtimes": {}
#}
now = datetime.now()
classtime_dict = {
    0: { # Monday
        "classtimes": [
            {
                "start": time(7, 40),
                "end": time(8, 0),
                "period": "1",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(8, 0),
                "end": time(9, 45),
                "period": "1",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(9, 45),
                "end": time(9, 50),
                "period": "3",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(9, 50),
                "end": time(11, 30),
                "period": "3",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(11, 30),
                "end": time(11, 35),
                "period": "5",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(11, 35),
                "end": time(13, 45),
                "period": "5",
                "passing": False,
                "lunchactive": True,
            },
            {
                "start": time(13, 45),
                "end": time(13, 50),
                "period": "7",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(13, 50),
                "end": time(15, 30),
                "period": "7",
                "passing": False,
                "lunchactive": False,
            },
        ],
        "lunchtimes": {
            "A": {"start": time(11, 35), "end": time(12, 5)},
            "B": {"start": time(12, 15), "end": time(12, 45)},
            "C": {"start": time(13, 15), "end": time(13, 45)},
        }
    },
    1: { # Tuesday
        "classtimes": [
            {
                "start": time(7, 40),
                "end": time(8, 0),
                "period": "2",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(8, 0),
                "end": time(9, 45),
                "period": "2",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(9, 45),
                "end": time(9, 50),
                "period": "4",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(9, 50),
                "end": time(11, 30),
                "period": "4",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(11, 30),
                "end": time(11, 35),
                "period": "6",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(11, 35),
                "end": time(13, 45),
                "period": "6",
                "passing": False,
                "lunchactive": True,
            },
            {
                "start": time(13, 45),
                "end": time(13, 50),
                "period": "8",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(13, 50),
                "end": time(15, 30),
                "period": "8",
                "passing": False,
                "lunchactive": False,
            },
        ],
        "lunchtimes": {
            "A": {"start": time(11, 35), "end": time(12, 5)},
            "B": {"start": time(12, 15), "end": time(12, 45)},
            "C": {"start": time(13, 15), "end": time(13, 45)},
        }
    },
    2: { # Wednesday
        "classtimes": [
            {
                "start": time(7, 40),
                "end": time(8, 0),
                "period": "1",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(8, 0),
                "end": time(9, 20),
                "period": "1",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(9, 20),
                "end": time(9, 25),
                "period": "3",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(9, 25),
                "end": time(10, 45),
                "period": "3",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(10, 45),
                "end": time(10, 50),
                "period": "Access",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(10, 50),
                "end": time(12, 0),
                "period": "Access",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(12, 0),
                "end": time(12, 5),
                "period": "5",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(12, 5),
                "end": time(14, 5),
                "period": "5",
                "passing": False,
                "lunchactive": True,
            },
            {
                "start": time(14, 5),
                "end": time(14, 10),
                "period": "7",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(14, 10),
                "end": time(15, 30),
                "period": "7",
                "passing": False,
                "lunchactive": False,
            },
        ],
        "lunchtimes": {
            "A": {"start": time(12, 5), "end": time(12, 35)},
            "B": {"start": time(12, 40), "end": time(13, 10)},
            "C": {"start": time(13, 35), "end": time(14, 5)},
        }
    },
    3: { # Thursday
        "classtimes": [
            {
                "start": time(7, 40),
                "end": time(8, 0),
                "period": "2",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(8, 0),
                "end": time(9, 20),
                "period": "2",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(9, 20),
                "end": time(9, 25),
                "period": "4",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(9, 25),
                "end": time(10, 45),
                "period": "4",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(10, 45),
                "end": time(10, 50),
                "period": "Access",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(10, 50),
                "end": time(12, 0),
                "period": "Access",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(12, 0),
                "end": time(12, 5),
                "period": "6",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(12, 5),
                "end": time(14, 5),
                "period": "6",
                "passing": False,
                "lunchactive": True,
            },
            {
                "start": time(14, 5),
                "end": time(14, 10),
                "period": "8",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(14, 10),
                "end": time(15, 30),
                "period": "8",
                "passing": False,
                "lunchactive": False,
            },
        ],
        "lunchtimes": {
            "A": {"start": time(12, 5), "end": time(12, 35)},
            "B": {"start": time(12, 40), "end": time(13, 10)},
            "C": {"start": time(13, 35), "end": time(14, 5)},
        }
    },
    4: { # Friday
        "classtimes": [
            {
                "start": time(7, 40),
                "end": time(8, 0),
                "period": "1",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(8, 0),
                "end": time(8, 45),
                "period": "1",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(8, 45),
                "end": time(8, 50),
                "period": "2",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(8, 50),
                "end": time(9, 35),
                "period": "2",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(9, 35),
                "end": time(9, 40),
                "period": "3",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(9, 40),
                "end": time(10, 25),
                "period": "3",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(10, 25),
                "end": time(10, 30),
                "period": "4",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(10, 30),
                "end": time(11, 15),
                "period": "4",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(11, 15),
                "end": time(11, 20),
                "period": "5",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(11, 20),
                "end": time(13, 0),
                "period": "5",
                "passing": False,
                "lunchactive": True,
            },
            {
                "start": time(13, 0),
                "end": time(13, 5),
                "period": "6",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(13, 5),
                "end": time(13, 50),
                "period": "6",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(13, 50),
                "end": time(13, 55),
                "period": "7",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(13, 55),
                "end": time(14, 40),
                "period": "7",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(14, 40),
                "end": time(14, 45),
                "period": "8",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(14, 45),
                "end": time(15, 30),
                "period": "8",
                "passing": False,
                "lunchactive": False,
            },
        ],
        "lunchtimes": {
            "A": {"start": time(11, 20), "end": time(11, 50)},
            "B": {"start": time(11, 55), "end": time(12, 25)},
            "C": {"start": time(12, 30), "end": time(13, 0)},
        }
    },
    5: { # No school
        "classtimes": [],
        "lunchtimes": {}
    },
    6: { # No school
        "classtimes": [],
        "lunchtimes": {}
    },
    7: { # Early Release Blue
        "classtimes": [
            {
                "start": time(7, 40),
                "end": time(8, 0),
                "period": "1",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(8, 0),
                "end": time(8, 55),
                "period": "1",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(8, 55),
                "end": time(9, 0),
                "period": "3",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(9, 0),
                "end": time(9, 55),
                "period": "3",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(9, 55),
                "end": time(10, 0),
                "period": "5",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(10, 0),
                "end": time(10, 55),
                "period": "5",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(10, 55),
                "end": time(11, 0),
                "period": "7",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(11, 0),
                "end": time(11, 55),
                "period": "7",
                "passing": False,
                "lunchactive": False,
            },
        ],
        "lunchtimes": {}
    },
    8: { # Early Release Gold
        "classtimes": [
            {
                "start": time(7, 40),
                "end": time(8, 0),
                "period": "2",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(8, 0),
                "end": time(8, 55),
                "period": "2",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(8, 55),
                "end": time(9, 0),
                "period": "4",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(9, 0),
                "end": time(9, 55),
                "period": "4",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(9, 55),
                "end": time(10, 0),
                "period": "6",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(10, 0),
                "end": time(10, 55),
                "period": "6",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(10, 55),
                "end": time(11, 0),
                "period": "8",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(11, 0),
                "end": time(11, 55),
                "period": "8",
                "passing": False,
                "lunchactive": False,
            },
        ],
        "lunchtimes": {}
    },
    9: { # Development
        "classtimes": [
            {
                "start": now.time(),
                "end": (now + timedelta(minutes=5)).time(),
                "period": "1",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": (now + timedelta(minutes=5)).time(),
                "end": (now + timedelta(minutes=10)).time(),
                "period": "2",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": (now + timedelta(minutes=10)).time(),
                "end": (now + timedelta(minutes=15)).time(),
                "period": "3",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": (now + timedelta(minutes=15)).time(),
                "end": (now + timedelta(minutes=20)).time(),
                "period": "4",
                "passing": False,
                "lunchactive": False,
            }
        ],
        "lunchtimes": {}
    },
    10: { # Delayed Monday
        "classtimes": [
            {
                "start": time(9, 30),
                "end": time(10, 0),
                "period": "1",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(10, 0),
                "end": time(11, 15),
                "period": "1",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(11, 15),
                "end": time(11, 20),
                "period": "3",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(11, 20),
                "end": time(12, 30),
                "period": "3",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(12, 30),
                "end": time(12, 35),
                "period": "5",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(12, 35),
                "end": time(14, 15),
                "period": "5",
                "passing": False,
                "lunchactive": True,
            },
            {
                "start": time(14, 15),
                "end": time(14, 20),
                "period": "7",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(14, 20),
                "end": time(15, 30),
                "period": "7",
                "passing": False,
                "lunchactive": False,
            }
        ],
        "lunchtimes": {
            "A": {"start": time(12, 35), "end": time(13, 5)},
            "B": {"start": time(13, 10), "end": time(13, 40)},
            "C": {"start": time(13, 45), "end": time(14, 15)},
        }
    },
    11: { # Delayed Tuesday
        "classtimes": [
            {
                "start": time(9, 30),
                "end": time(10, 0),
                "period": "2",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(10, 0),
                "end": time(11, 15),
                "period": "2",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(11, 15),
                "end": time(11, 20),
                "period": "4",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(11, 20),
                "end": time(12, 30),
                "period": "4",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(12, 30),
                "end": time(12, 35),
                "period": "6",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(12, 35),
                "end": time(14, 15),
                "period": "6",
                "passing": False,
                "lunchactive": True,
            },
            {
                "start": time(14, 15),
                "end": time(14, 20),
                "period": "8",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(14, 20),
                "end": time(15, 30),
                "period": "8",
                "passing": False,
                "lunchactive": False,
            }
        ],
        "lunchtimes": {
            "A": {"start": time(12, 35), "end": time(13, 5)},
            "B": {"start": time(13, 10), "end": time(13, 40)},
            "C": {"start": time(13, 45), "end": time(14, 15)},
        }
    },
    12: { # Delayed Wednesday
        "classtimes": [
            {
                "start": time(9, 30),
                "end": time(10, 0),
                "period": "1",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(10, 0),
                "end": time(11, 5),
                "period": "1",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(11, 5),
                "end": time(11, 10),
                "period": "3",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(11, 10),
                "end": time(12, 10),
                "period": "3",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(12, 10),
                "end": time(12, 15),
                "period": "Access",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(12, 15),
                "end": time(12, 45),
                "period": "Access",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(12, 45),
                "end": time(12, 50),
                "period": "5",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(12, 50),
                "end": time(13, 20),
                "period": "5",
                "passing": False,
                "lunchactive": True,
            },
            {
                "start": time(13, 20),
                "end": time(14, 30),
                "period": "7",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(14, 30),
                "end": time(15, 30),
                "period": "7",
                "passing": False,
                "lunchactive": False,
            },
        ],
        "lunchtimes": {
            "A": {"start": time(12, 50), "end": time(13, 20)},
            "B": {"start": time(13, 25), "end": time(13, 55)},
            "C": {"start": time(14, 00), "end": time(14, 30)},
        }
    },
    13: { # Delayed Thursday
        "classtimes": [
            {
                "start": time(9, 30),
                "end": time(10, 0),
                "period": "2",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(10, 0),
                "end": time(11, 5),
                "period": "2",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(11, 5),
                "end": time(11, 10),
                "period": "4",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(11, 10),
                "end": time(12, 10),
                "period": "4",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(12, 10),
                "end": time(12, 15),
                "period": "Access",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(12, 15),
                "end": time(12, 45),
                "period": "Access",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(12, 45),
                "end": time(12, 50),
                "period": "6",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(12, 50),
                "end": time(13, 20),
                "period": "6",
                "passing": False,
                "lunchactive": True,
            },
            {
                "start": time(13, 20),
                "end": time(14, 30),
                "period": "8",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(14, 30),
                "end": time(15, 30),
                "period": "8",
                "passing": False,
                "lunchactive": False,
            },
        ],
        "lunchtimes": {
            "A": {"start": time(12, 50), "end": time(13, 20)},
            "B": {"start": time(13, 25), "end": time(13, 55)},
            "C": {"start": time(14, 00), "end": time(14, 30)},
        }
    },
    14: { # Delayed Friday
        "classtimes": [
            {
                "start": time(10, 0),
                "end": time(10, 30),
                "period": "1",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(10, 30),
                "end": time(10, 35),
                "period": "2",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(10, 35),
                "end": time(11, 0),
                "period": "2",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(11, 0),
                "end": time(11, 5),
                "period": "3",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(11, 5),
                "end": time(11, 30),
                "period": "3",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(11, 30),
                "end": time(11, 35),
                "period": "4",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(11, 35),
                "end": time(12, 0),
                "period": "4",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(12, 0),
                "end": time(12, 5),
                "period": "5",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(12, 5),
                "end": time(13, 45),
                "period": "5",
                "passing": False,
                "lunchactive": True,
            },
            {
                "start": time(13, 45),
                "end": time(13, 50),
                "period": "6",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(13, 50),
                "end": time(14, 20),
                "period": "6",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(14, 20),
                "end": time(14, 25),
                "period": "7",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(14, 25),
                "end": time(14, 55),
                "period": "7",
                "passing": False,
                "lunchactive": False,
            },
            {
                "start": time(14, 55),
                "end": time(15, 0),
                "period": "8",
                "passing": True,
                "lunchactive": False,
            },
            {
                "start": time(15, 0),
                "end": time(15, 30),
                "period": "8",
                "passing": False,
                "lunchactive": False,
            }
        ],
        "lunchtimes": {
            "A": {"start": time(12, 5), "end": time(12, 35)},
            "B": {"start": time(12, 40), "end": time(13, 10)},
            "C": {"start": time(13, 15), "end": time(13, 45)},
        }
    }
}
readable_days = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "No school",
    6: "No school",
    7: "Early Release Blue",
    8: "Early Release Gold",
    9: "Development",
    10: "Delayed Monday",
    11: "Delayed Tuesday",
    12: "Delayed Wednesday",
    13: "Delayed Thursday",
    14: "Delayed Friday"
}

# TODO: Webhooks?

BELL_DELAY = 4 if not app.config['TESTING'] else 0 # Seconds to add to each time to account for bell delay.
PASSING_BELL_DELAY = 4.006 if not app.config['TESTING'] else 0 # Not used, just for reference.

for d, dtimes in classtime_dict.items():
    app.logger.debug(f"Setting times for {readable_days[d]}")
    for time in dtimes['classtimes']:
        app.logger.debug(f"Original time for period {time}")
        time['start'] = datetime.combine(date.today(), time['start'])
        time['end'] = datetime.combine(date.today(), time['end'])
        time['start'] += timedelta(seconds=BELL_DELAY)
        time['end'] += timedelta(seconds=BELL_DELAY)
        time['start'] = time['start'].time()
        time['end'] = time['end'].time()
        classtime_dict[d]['classtimes'] = dtimes['classtimes']

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
    return classtime_dict[get_current_day() if day is None else day]['classtimes']

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
        classtimes = classtime_dict[day]['classtimes']
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
