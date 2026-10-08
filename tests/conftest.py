import re

import pytest

from app import create_app
from app.services import auth_service

PASSWORD = "correct-horse-battery"


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only-secret-key",
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        }
    )
    yield application
    application.extensions["db_engine"].dispose()


@pytest.fixture
def db(app):
    session = app.extensions["session_factory"]()
    yield session
    session.close()


@pytest.fixture
def make_user(db):
    def _make(email="alice@example.com", password=PASSWORD):
        return auth_service.create_user(db, email, password)

    return _make


@pytest.fixture
def client(app):
    return app.test_client()


def get_csrf(client, url="/login"):
    html = client.get(url).get_data(as_text=True)
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "no csrf token found"
    return match.group(1)


@pytest.fixture
def csrf():
    return get_csrf


@pytest.fixture
def login(client):
    def _login(email="alice@example.com", password=PASSWORD):
        token = get_csrf(client)
        return client.post(
            "/login",
            data={"email": email, "password": password, "csrf_token": token},
        )

    return _login
