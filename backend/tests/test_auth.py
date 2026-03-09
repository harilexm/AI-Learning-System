import pytest
from app import create_app
from app.extensions import db

@pytest.fixture
def app():
    # Setup
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", # Use in-memory DB for speed
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_register(client):
    response = client.post('/api/auth/register', json={
        "username": "testuser", "email": "test@test.com",
        "password": "testpass123", "firstName": "Test", "lastName": "User"
    })
    assert response.status_code == 201
    assert "registered successfully" in response.get_json()['message']

def test_login(client):
    # Register first, then login
    client.post('/api/auth/register', json={
        "username": "testuser2", "email": "test2@test.com",
        "password": "testpass123", "firstName": "Test", "lastName": "User"
    })
    response = client.post('/api/auth/login', json={"email": "test2@test.com", "password": "testpass123"})
    assert response.status_code == 200
    assert "access_token" in response.get_json()

def test_login_wrong_password(client):
    client.post('/api/auth/register', json={
        "username": "testuser3", "email": "test3@test.com",
        "password": "testpass123", "firstName": "Test", "lastName": "User"
    })
    response = client.post('/api/auth/login', json={"email": "test3@test.com", "password": "wrong"})
    assert response.status_code == 401
    assert "error" in response.get_json()

def test_short_password_rejected(client):
    response = client.post('/api/auth/register', json={
        "username": "short", "email": "short@test.com",
        "password": "abc", "firstName": "Short", "lastName": "Pass"
    })
    assert response.status_code == 400
    assert "at least 8 characters" in response.get_json()['error']
