# pylint: disable=redefined-outer-name, import-error, cyclic-import
"""
This file tests the user functions, like login and registration, and general user actions.
"""

import os
import base64
from datetime import datetime, timedelta
import pytest
import freezegun
os.environ["END_OF_SEMESTER"] = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
from app import app # pylint: disable=wrong-import-position, import-error, cyclic-import

# If anyone can help me split this into test_users and test_classes, that would be great. I'm not sure how to do that.

app.config['TESTING'] = True
app.config['END_OF_SEMESTER'] = datetime.strptime(os.environ["END_OF_SEMESTER"], '%Y-%m-%d').date()

@pytest.fixture(scope="session")
def client():
    """
    Creates a test client
    """
    with app.test_client(False) as cclient:
        yield cclient

@pytest.fixture(scope="session")
def admintoken(client): # Simulates the first registration, with no classes
    """
    Creates an admin user
    """
    print("Creating user")
    response = client.post("/register", json={"email": "admin.pytest@s.stemk12.org"})
    assert response.status_code == 200
    assert response.json.get('emailid')
    emailid = response.json.get('emailid')
    response = client.post(f"/register/{emailid}", json={"username": "admin", "password": "password123"})
    assert response.status_code == 400
    response = client.post(f"/register/{emailid}", json={"username": "pytrwy", "password": "password123"})
    assert response.status_code == 200
    assert response.json.get('token')
    ntoken = response.json.get('token')
    assert ntoken
    yield ntoken


@pytest.fixture(scope="session")
def token(client): # Simulates a users first login and actions, with classes
    """
    Creates a normal user
    """
    print("Creating user")
    response = client.post("/register", json={"email": "a.a@s.stemk12.org"})
    if response.status_code != 200:
        pytest.fail(f"Failed to get emailid: {response.status_code}")
        return
    if response.json.get('emailid') is None:
        pytest.fail("Failed to get emailid")
        return
    emailid = response.json.get('emailid')
    response = client.post(f"/register/{emailid}", json={"username": "admin", "password": "password123"})
    if response.status_code != 400:
        pytest.fail(f"User was allowed to register \"admin\" as a username: {response.status_code}")
        return
    response = client.post(f"/register/{emailid}", json={"username": "pytrwy", "password": "password123"})
    if response.status_code != 400:
        pytest.fail(
            f"User was allowed to take what should have been an already taken username, check the tests order: {response.status_code}"
        )
        return
    response = client.post(f"/register/{emailid}", json={"username": "pytest", "password": "password123"})
    if response.status_code != 200:
        pytest.fail(f"Failed to register user: {response.status_code}")
        return
    if response.json.get('token') is None:
        pytest.fail("Failed to get token")
        return
    ntoken = response.json.get('token')
    assert ntoken
    with open("tests/democlasses.txt", encoding="utf-8") as f:
        classlist = f.read().split("\n")
    response = client.post("/addclasses", json=classlist, headers={"Authorization": f"Bearer {ntoken}"})
    assert response.status_code == 200
    assert response.json.get('status') == "success"
    yield ntoken

def test_dashboard_no_token(client):
    """
    Tests the dashboard route without a token, should fail
    """
    response = client.get("/dashboard", follow_redirects=False, headers={"Authorization": ""})
    assert response.status_code == 302
    assert response.location == "/login"

def test_create_admin(client, admintoken): #pylint: disable=unused-argument
    """
    Checks if the admin user is able to be created
    """
    assert True

def test_create_user(client, token): #pylint: disable=unused-argument
    """
    Checks if the normal user is able to be created, forces the creation of the admin user to happen first
    """
    assert True

def test_export_data_admin(client, admintoken):
    """
    Tests the export route for an admin
    """
    response = client.get("/export", headers={"Authorization": f"Bearer {admintoken}"})
    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert response.json.get('status') == "success"
    assert response.json.get('username') == "pytrwy"
    assert response.json.get('email') == "admin.pytest@s.stemk12.org"
    assert response.json.get('role') == "admin"
    assert response.json.get('classes') == []
    assert len(response.json.get('sessions')) == 1

def test_export_data(client, token):
    """
    Tests the export route for a user
    """
    response = client.get("/export", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert response.json.get('status') == "success"
    assert response.json.get('username') == "pytest"
    assert response.json.get('email') == "a.a@s.stemk12.org"
    assert response.json.get('role') == "user"
    assert len(response.json.get('classes')) == 9
    assert {"canvasid": None,"lunch": None,"name":"Class 5","period":"1","room":"333"} in response.json.get('classes')
    assert len(response.json.get('sessions')) == 1

def test_basic_auth(client, token): # pylint: disable=unused-argument
    """
    Tests the dashboard route with basic auth
    """
    response = client.get("/dashboard", headers={"Authorization": f"Basic {base64.b64encode(b'pytest:password123').decode()}"})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'

def test_dashboard_invalid_basic_auth(client):
    """
    Tests the dashboard route with invalid basic auth
    """
    response = client.get("/dashboard", headers={"Authorization": "Basic invalidtoken"})
    assert response.status_code == 400

def test_dashboard_incorrect_basic_auth(client):
    """
    Tests the dashboard route with incorrect basic auth
    """
    response = client.get("/dashboard", headers={"Authorization": "Basic " + base64.b64encode(b"pytest:password823").decode()})
    assert response.status_code == 401

def test_dashboard_legacy_auth(client, token):
    """
    Tests the dashboard route with a legacy token
    """
    response = client.get("/dashboard", headers={"Authorization": f"pytest {token}"})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'

def test_dashboard_invalid_legacy_auth(client):
    """
    Tests the dashboard route with an invalid legacy token
    """
    response = client.get("/dashboard", headers={"Authorization": "pytest invalidtoken"})
    assert response.status_code in (302, 400)

@freezegun.freeze_time("2025-03-12 11:14:00")
def test_dashboard_wensday(client, token):
    """
    Tests the dashboard route on a Wednesday
    """
    response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert b"Class 5" in response.data
    assert b"Class2" not in response.data
    assert b"Access" in response.data

@freezegun.freeze_time("2025-03-11 11:14:00")
def test_dashboard_tuesday(client, token):
    """
    Tests the dashboard route on a Tuesday
    """
    response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert b"Class 5" not in response.data
    assert b"Class2" in response.data
    assert b"Access" not in response.data

@freezegun.freeze_time("2025-03-14 11:14:00")
def test_dashboard_friday(client, token):
    """
    Tests the dashboard route on a Friday
    """
    response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert b"Class 5" in response.data
    assert b"Class2" in response.data
    assert b"Access" not in response.data

def test_dashboard_invalid_token(client):
    """
    Tests the dashboard route with an invalid token
    """
    response = client.get("/dashboard", headers={"Authorization": "Bearer invalidtoken"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.location == "/login"

def test_account(client, token):
    """
    Tests the account route
    """
    response = client.get("/account", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'

def test_schedule_pdf(client, token):
    """
    Tests the schedule route
    """
    response = client.get("/classes/exportschedule", headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        pytest.fail(f"Failed to get load schedule settings page: {response.status_code}")
    response = client.get(
        "/classes/schedulepdf/monday,tuesday,wednesday,thursday,friday,eb,eg?",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        pytest.fail(f"Failed to get schedule pdf: {response.status_code}")
    if response.content_type != "application/pdf":
        pytest.fail(f"Failed to get schedule pdf: {response.content_type}")
    response = client.get(
        "/classes/schedulepdf/monday,tuesday,wednesday,eb,eg?notime=true&noperiod=true",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        pytest.fail("Failed to get 2nd schedule pdf: {response.status_code}")
    if response.content_type != "application/pdf":
        pytest.fail("Failed to get 2nd schedule pdf: {response.content_type}")

def test_calendar(client, token):
    """
    Tests the calendar route
    """
    response = client.get("/classes/calendar", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert b"Create Calendar" in response.data
    response = client.get("/download/calendar.ics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'text/calendar; charset=utf-8'
    assert b"BEGIN:VCALENDAR" in response.data
    assert b"END:VCALENDAR" in response.data
    response = client.get(f"/{token}/calendar.ics")
    assert response.status_code == 200
    assert response.content_type == 'text/calendar; charset=utf-8'
    assert b"BEGIN:VCALENDAR" in response.data
    assert b"END:VCALENDAR" in response.data

def test_delete_user(client, token):
    """
    Tests the delete user route
    """
    response = client.post("/account/delete", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json.get('status') == "success"
    # Check if the user is actually deleted
    response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.location == "/login"  # Should redirect to login after deletion
