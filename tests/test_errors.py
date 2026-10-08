import logging

import pytest

from app import create_app
from app.models import Task


def test_404_is_generic(client):
    resp = client.get("/no/such/page")
    html = resp.get_data(as_text=True)
    assert resp.status_code == 404
    assert "not found" in html and "Traceback" not in html


def test_405_is_generic(client):
    assert client.get("/tasks/1/complete").status_code in (302, 405)


def test_unexpected_error_is_generic_and_logged(app, client, make_user, login, caplog, monkeypatch):
    make_user()
    login()

    def boom(*_a, **_k):
        raise RuntimeError("internal-detail-xyz")

    monkeypatch.setattr("app.routes.tasks.task_service.list_tasks", boom)
    with caplog.at_level(logging.ERROR):
        resp = client.get("/tasks")
    html = resp.get_data(as_text=True)
    assert resp.status_code == 500
    assert "internal-detail-xyz" not in html and "Traceback" not in html
    assert "Something went wrong" in html
    assert "RuntimeError" in caplog.text  # details stay in the server log


def test_csrf_failure_generic_and_token_not_logged(client, caplog):
    with caplog.at_level(logging.DEBUG):
        resp = client.post("/login", data={"email": "a@b.co", "password": "secret-pw-123"})
    assert resp.status_code == 400
    assert "CSRF" not in resp.get_data(as_text=True)
    assert "secret-pw-123" not in caplog.text


def test_logs_do_not_contain_credentials_or_tokens(client, make_user, csrf, caplog):
    make_user()
    with caplog.at_level(logging.DEBUG):
        token = csrf(client)
        client.post(
            "/login",
            data={"email": "alice@example.com", "password": "very-secret-pw-1", "csrf_token": token},
        )
        client.post("/login", data={"email": "alice@example.com", "password": "bad-pw-2", "csrf_token": token})
    assert "very-secret-pw-1" not in caplog.text
    assert "bad-pw-2" not in caplog.text
    assert token not in caplog.text


def test_db_error_does_not_log_parameters(app, make_user, db, caplog):
    from sqlalchemy.exc import IntegrityError

    make_user("dup@example.com")
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(IntegrityError) as info:
            make_user("dup@example.com", "another-password-1")
    db.rollback()
    assert "another-password-1" not in str(info.value)
    assert "$argon2" not in str(info.value)


def test_missing_secret_key_fails_clearly(monkeypatch, tmp_path):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError) as info:
        create_app({"TESTING": True, "SECRET_KEY": None,
                    "DATABASE_URL": f"sqlite:///{(tmp_path / 'x.db').as_posix()}"})
    assert "SECRET_KEY" in str(info.value)
