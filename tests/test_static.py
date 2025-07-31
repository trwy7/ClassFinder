# pylint: disable=redefined-outer-name
"""
This file tests the static files, like CSS and favicon.
"""
import pytest
from app import app # pylint: disable=wrong-import-position, import-error

app.config['TESTING'] = True

@pytest.fixture
def client():
    """
    Creates a test client
    """
    with app.test_client(False) as cclient:
        yield cclient

def test_index_css(client):
    """
    Tests the index.css file
    """
    response = client.get('/index.css')
    assert response.status_code == 200
    assert response.content_type == 'text/css; charset=utf-8'

def test_favicon(client):
    """
    Tests the favicon
    """
    response = client.get('/favicon.ico')
    assert response.status_code == 200
    assert response.content_type in ('image/vnd.microsoft.icon', 'image/x-icon')

def test_index(client):
    """
    Tests the about file
    """
    response = client.get('/')
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
