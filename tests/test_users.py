import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def apilogin(client):
    response = client.post('/api/v1/login/', json={'username': 'pytest', 'password': 'password'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    global token
    token = response.json['token'] if 'token' in response.json else None
    return token

def test_signup(client):
    response = client.post('/signup/', json={'email': 'test.email@s.stemk12.org'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    global emailid
    emailid = response.json['emailid'] if 'emailid' in response.json else None

def test_signup_invalid_email(client):
    response = client.post('/signup/', json={'email': 'testemail@gmail.com'})
    assert response.status_code == 400

def test_signup_stage_2_fail(client):
    response = client.post('/signup/' + emailid, json={'username': 'pytest', 'password': 'password'})
    assert response.status_code == 400

def test_signup_stage_2(client):
    response = client.post('/signup/' + emailid, json={'username': 'newaccount', 'password': 'password'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'

def test_newaccount_login(client, password='password'):
    response = client.post('/api/v1/login/', json={'username': 'newaccount', 'password': password})
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    global newtoken
    newtoken = response.json['token'] if 'token' in response.json else None

def test_change_password(client):
    response = client.post('/api/v1/change-password/', json={'password': 'password'}, headers={'Authorization': f'newaccount {newtoken}'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'

def test_password_reset(client):
    response = client.post('/reset-password/', json={'email': 'test.email@s.stemk12.org'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    global resettoken
    resettoken = response.json['emailid'] if 'emailid' in response.json else None

def test_password_reset_invalid_email(client):
    response = client.post('/reset-password/', json={'email': 'testemail@gmail.com'})
    assert response.status_code == 400

def test_password_reset_nonexistantemail(client):
    response = client.post('/reset-password/', json={'email': 'test.invalid@s.stemk12.org'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert 'emailid' not in response.json

def test_password_reset_stage_2(client):
    response = client.post('/reset-password/' + resettoken, json={'password': 'password'}, follow_redirects=True)
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    test_newaccount_login(client, 'password')

def test_password_reset_stage_2_fail(client):
    response = client.post('/reset-password/99999999999999999999/', json={'password': 'password'})
    assert response.status_code == 400

def test_delete_account(client):
    response = client.delete('/api/v1/deleteaccount/', headers={'Authorization': f'newaccount {newtoken}'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'