# pylint: disable=redefined-outer-name, import-error, cyclic-import, unused-argument
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

def check_html_response(client, path, headers={}, expected_status=200):
    """
    Helper function to check HTML response
    """
    response = client.get(path, headers=headers)
    assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code} for path {path}"
    assert response.content_type == 'text/html; charset=utf-8', f"Expected content type 'text/html; charset=utf-8', got {response.content_type} for path {path}"
    return response

def check_json_response(client, path, headers={}, expected_status=200, method='GET'):
    """
    Helper function to check JSON response
    """
    response = client.open(path, headers=headers, method=method)
    assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code} for path {path}"
    assert response.content_type == 'application/json', f"Expected content type 'application/json', got {response.content_type} for path {path}"
    return response

@pytest.fixture(scope="session")
def client():
    """
    Creates a test client
    """
    with app.test_client(False) as cclient:
        yield cclient

@pytest.fixture(scope="session")
def admintoken(client): # Simulates the first registration, with no classes # TODO: Split into multiple tests
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
def token(client, admintoken): # Simulates a normal user registration, with classes # TODO: Split into multiple tests
    """
    Creates a normal user, and simulates adding classes to them
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

def test_create_admin(client, admintoken):
    """
    Checks if the admin user is able to be created
    """
    assert True

def test_create_user(client, token):
    """
    Checks if the normal user is able to be created, forces the creation of the admin user to happen first
    """
    assert True

def test_export_data_admin(client, admintoken):
    """
    Tests the export route for an admin
    """
    response = check_json_response(client, "/api/v2/data", headers={"Authorization": f"Bearer {admintoken}"})
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
    response = check_json_response(client, "/api/v2/data", headers={"Authorization": f"Bearer {token}"})
    assert response.json.get('status') == "success"
    assert response.json.get('username') == "pytest"
    assert response.json.get('email') == "a.a@s.stemk12.org"
    assert response.json.get('role') == "user"
    assert len(response.json.get('classes')) == 9
    for nclass in response.json.get('classes'):
        assert 'name' in nclass
        assert 'displayname' in nclass
        assert 'room' in nclass
        assert 'period' in nclass
        assert 'lunch' in nclass
        assert 'canvasid' in nclass
        assert 'verified' in nclass
        assert 'teacher' in nclass
        assert nclass['name'].startswith("Class") or nclass['name'].endswith("Access")
        assert nclass['displayname'].startswith("Class") or nclass['displayname'].endswith("Access")
    assert len(response.json.get('sessions')) == 1

def test_basic_auth(client, token):
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
    assert response.status_code in (302, 400)

def test_dashboard_incorrect_basic_auth(client):
    """
    Tests the dashboard route with incorrect basic auth
    """
    response = client.get("/dashboard", headers={"Authorization": "Basic " + base64.b64encode(b"pytest:password823").decode()})
    assert response.status_code in (302, 401)

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

def test_dashboard_no_token(client):
    """
    Tests the dashboard route without a token, should fail
    """
    response = client.get("/dashboard", follow_redirects=False, headers={"Authorization": ""})
    assert response.status_code == 302
    assert response.location == "/login"

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

@freezegun.freeze_time("2025-08-27 11:14:00")
def test_timer(client, token):
    """
    Tests the timer route on a Tuesday
    """
    response = client.get("/timer/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'

def test_timer_invalid(client, token):
    response = client.get("/timer/9999999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404, "Timer with ID of 9999999 should not exist"
    assert response.content_type == 'text/html; charset=utf-8'
    assert b"That timer does not exist. You may use:" in response.data

@freezegun.freeze_time("2025-08-27 11:14:00")
def test_custom_timer(client, token):
    response = client.get("/timers.json", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, "Failed to get timers.json"
    assert response.content_type == 'application/json'
    assert isinstance(response.json, list), "timers.json did not return a list"
    assert len(response.json) >= 1, "timers.json returned an empty list"
    for timer in response.json:
        assert isinstance(timer, int), f"Timer version {timer} is not an integer"
        # Test each timer version
        timer_response = client.get(f"/timer/{timer}", headers={"Authorization": f"Bearer {token}"})
        assert timer_response.status_code == 200, f"Failed to get timer version {timer}"
        assert timer_response.content_type == 'text/html; charset=utf-8'

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

@freezegun.freeze_time("2025-8-25 13:45:30")
def test_ptech_times(client, token):
    """
    Tests the weird PTECH times - Before class
    """
    response = client.get("/api/v2/classes/current", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json['classes'][response.json['period']]['room'] == "PTECH", "It does not think it is in PTECH"
    assert response.json['endtime'] != 1756129800, "The PTECH start delay was not accounted for"
    assert response.json['endtime'] == 1756130100, f"The PTECH start delay messed up somewhere, got {response.json['endtime']}, expected 1756130100"
    assert response.json['passing'] is True, "It does not think it is passing time"

@freezegun.freeze_time("2025-8-25 13:50:30")
def test_ptech_times_duringbefore(client, token):
    """
    Tests the weird PTECH times - "During before" class
    """
    response = client.get("/api/v2/classes/current", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json['classes'][response.json['period']]['room'] == "PTECH", "It does not think it is in PTECH"
    assert response.json['endtime'] != 1756135500, "It thinks it is durring class"
    assert response.json['endtime'] == 1756130100, f"The PTECH start delay messed up somewhere, got {response.json['endtime']}, expected 1756130100"
    assert response.json['passing'] is True, "It does not think it is passing time"

@freezegun.freeze_time("2025-8-25 13:55:30")
def test_ptech_times_during_class(client, token):
    """
    Tests the weird PTECH times - During class
    """
    response = client.get("/api/v2/classes/current", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json['classes'][response.json['period']]['room'] == "PTECH", "It does not think it is in PTECH"
    app.logger.debug(f"Response JSON: {response.json}")
    assert response.json['endtime'] == 1756135500, f"The PTECH end delay messed up somewhere, got {response.json['endtime']}, expected 1756135500"
    assert response.json['passing'] is False, "It does not think it is class time"

@freezegun.freeze_time("2025-8-25 15:25:30")
def test_ptech_times_afterduring_eos(client, token):
    """
    Tests the weird PTECH times - "After during" class, end of school
    """
    response = client.get("/api/v2/classes/current", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json['period'] is None, "It thinks it is class time, but school has ended"
    assert response.json['endtime'] is None, "It thinks it is class time, but school has ended"

@freezegun.freeze_time("2025-8-25 11:25:30")
def test_ptech_times_afterduring(client, token):
    """
    Tests the weird PTECH times - "After during" class, end of school
    """
    response = client.get("/api/v2/classes/current", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json['classes'][response.json['period']]['room'] == "PTECH", "It does not think it is in PTECH"
    assert response.json['endtime'] == 1756121700, f"The PTECH end delay messed up somewhere, got {response.json['endtime']}, expected 1756135500"

@freezegun.freeze_time("2025-8-27 11:05:00")
def test_legacy_api_todaycourses(client, token):
    """
    Tests the legacy API for today's courses
    """
    response = client.get("/api/v1/currentcourses/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert 'courses' in response.json, "No courses found in response"
    assert len(response.json['courses']) == 5, f"Expected 5 courses, got {len(response.json['courses'])}"
    assert {"name": "Class 5", "room": "352", "lunch": None, "verified": False, "canvasid": None, "id": "352p1"} in response.json['courses'].values(), "Class 5 not found in courses"

@freezegun.freeze_time("2025-8-27 11:05:00")
def test_legacy_api_currentperiod(client, token):
    """
    Tests the legacy API for current period
    """
    response = client.get("/api/v1/currentperiod/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json.get('currentperiod') == "Access", f"Expected current period to be 'Access', got {response.json.get('currentperiod')}"
    assert response.json.get('nextclass') == 1756296000, f"Expected nextclass to be 1756296000, got {response.json.get('nextclass')}"

def test_api_login(client, token):
    """
    Tests the API login route
    """
    response = client.post("/api/v2/login", json={"username": "pytest", "password": "password123", "type": "api"})
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json.get('token')
    dashresponse = client.get("/dashboard", headers={"Authorization": f"Bearer {response.json.get('token')}"})
    assert dashresponse.status_code == 200, f"Failed to access dashboard with new token: {dashresponse.status_code}"
    assert dashresponse.content_type == 'text/html; charset=utf-8'

def test_api_createtoken(client, token):
    """
    Tests the API token creation route
    """
    response = client.post("/api/v2/createtoken", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    dashresponse = client.get("/dashboard", headers={"Authorization": f"Bearer {response.json}"})
    assert dashresponse.status_code == 200, f"Failed to access dashboard with new token: {dashresponse.status_code}"
    assert dashresponse.content_type == 'text/html; charset=utf-8'

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
        pytest.fail(f"Failed to get 2nd schedule pdf: {response.status_code}")
    if response.content_type != "application/pdf":
        pytest.fail(f"Failed to get 2nd schedule pdf: {response.content_type}")

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
    assert response.status_code == 200, f"Failed to get calendar with token in URL: {response.status_code}"
    assert response.content_type == 'text/calendar; charset=utf-8', f"Failed to get calendar with token in URL: {response.content_type}"
    assert b"BEGIN:VCALENDAR" in response.data, f"Failed to get calendar with token in URL: {response.data}"
    assert b"END:VCALENDAR" in response.data, f"Failed to get calendar with token in URL: {response.data}"
    response = client.post("/api/v2/createscopedtoken", headers={"Authorization": f"Bearer {token}"}, json={"scopes": ["calendar"]})
    assert response.status_code == 200, f"Failed to create scoped token: {response.status_code}"
    assert response.content_type == 'application/json', f"Failed to create scoped token: {response.content_type}"
    assert response.json, f"Failed to create scoped token: {response.json}"
    calendartoken = response.json
    response = client.get(f"/{calendartoken}/calendar.ics")
    assert response.status_code == 200, f"Failed to get calendar with scoped token: {response.status_code} {response.data}"
    assert response.content_type == 'text/calendar; charset=utf-8', f"Failed to get calendar with scoped token: {response.content_type}"
    assert b"BEGIN:VCALENDAR" in response.data, f"Failed to get calendar with scoped token: {response.data}"
    assert b"END:VCALENDAR" in response.data, f"Failed to get calendar with scoped token: {response.data}"

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

def test_admin_logs(client, admintoken):
    """
    Tests the admin logs route
    """
    response = client.get("/admin/logs", headers={"Authorization": f"Bearer {admintoken}"})
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
