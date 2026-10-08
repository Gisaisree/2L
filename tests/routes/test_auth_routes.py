import pytest

from app.models import User

GENERIC = "Invalid email or password."
PROTECTED_GET = ["/tasks", "/tasks/new", "/tasks/1/edit", "/tasks/1/delete"]


def test_login_page_has_fields_and_csrf(client):
    html = client.get("/login").get_data(as_text=True)
    assert 'name="email"' in html and 'name="password"' in html
    assert 'name="csrf_token"' in html


def test_valid_login_redirects_to_tasks(client, make_user, login):
    make_user()
    resp = login()
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/tasks")
    assert client.get("/tasks").status_code == 200


def test_login_ignores_next_param(client, make_user, csrf):
    make_user()
    token = csrf(client)
    resp = client.post(
        "/login?next=https://evil.example/",
        data={"email": "alice@example.com", "password": "correct-horse-battery", "csrf_token": token},
    )
    assert resp.headers["Location"].endswith("/tasks")


def test_failure_messages_identical(client, make_user, login, db):
    make_user()
    unknown = login("nobody@example.com", "whatever").get_data(as_text=True)
    wrong = login("alice@example.com", "wrong-password").get_data(as_text=True)
    assert GENERIC in unknown and GENERIC in wrong
    for _ in range(5):
        login("alice@example.com", "wrong-password")
    locked = login("alice@example.com", "correct-horse-battery")
    assert locked.status_code == 200
    assert GENERIC in locked.get_data(as_text=True)
    assert client.get("/tasks").status_code == 302


def test_missing_fields(client, csrf):
    token = csrf(client)
    resp = client.post("/login", data={"email": "", "password": "", "csrf_token": token})
    html = resp.get_data(as_text=True)
    assert "Email is required." in html and "Password is required." in html


@pytest.mark.parametrize("url", PROTECTED_GET)
def test_unauthenticated_get_redirects_to_login(client, url):
    resp = client.get(url)
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]


@pytest.mark.parametrize("url", ["/tasks/new", "/tasks/1/edit", "/tasks/1/complete", "/tasks/1/delete"])
def test_unauthenticated_post_not_allowed(client, csrf, url):
    token = csrf(client)
    resp = client.post(url, data={"csrf_token": token, "title": "x"})
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]


def test_root_redirects(client):
    assert client.get("/").status_code == 302


def test_no_logout_route(client):
    assert client.get("/logout").status_code == 404


def test_login_response_has_no_password_echo(client, make_user, login):
    make_user()
    html = login("alice@example.com", "my-secret-guess").get_data(as_text=True)
    assert "my-secret-guess" not in html
