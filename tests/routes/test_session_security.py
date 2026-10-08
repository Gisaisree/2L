import itsdangerous.timed

from app import SESSION_TIMEOUT


class FakeTime:
    def __init__(self):
        self.offset = 0.0
        import time as real

        self._real = real

    def time(self):
        return self._real.time() + self.offset


def test_cookie_attributes(client, make_user, login):
    make_user()
    resp = login()
    cookie = resp.headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Expires=" in cookie  # permanent session


def test_secure_flag_configurable(tmp_path):
    from app import create_app

    app = create_app({
        "TESTING": True, "SECRET_KEY": "k", "SESSION_COOKIE_SECURE": True,
        "DATABASE_URL": f"sqlite:///{(tmp_path / 's.db').as_posix()}",
    })
    c = app.test_client()
    resp = c.get("/login")
    assert "Secure" in resp.headers["Set-Cookie"]
    app.extensions["db_engine"].dispose()


def test_default_timeout_is_30_minutes():
    assert SESSION_TIMEOUT.total_seconds() == 30 * 60


def test_sliding_inactivity_timeout(client, make_user, login, monkeypatch):
    make_user()
    fake = FakeTime()
    monkeypatch.setattr(itsdangerous.timed, "time", fake)
    login()
    assert client.get("/tasks").status_code == 200

    # Active every 20 minutes for an hour: session keeps being refreshed.
    for _ in range(3):
        fake.offset += 20 * 60
        assert client.get("/tasks").status_code == 200

    # Idle for 31 minutes: expired.
    fake.offset += 31 * 60
    resp = client.get("/tasks")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]


def test_session_cleared_on_login(client, make_user, login):
    make_user()
    with client.session_transaction() as s:
        s["planted"] = "x"
    login()
    with client.session_transaction() as s:
        assert "planted" not in s
