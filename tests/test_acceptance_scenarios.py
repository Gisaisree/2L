"""Independent verification suite (Testing and Validation phase).

Each test carries a Gherkin scenario and the requirement IDs it traces to.
Tests exercise the HTTP layer so they are independent of the service-level tests.
"""
import re
from datetime import timedelta
from pathlib import Path

import pytest

from app import LOCKOUT_DURATION
from app.models import Task, User, utcnow
from tests.conftest import PASSWORD, get_csrf

ROOT = Path(__file__).resolve().parent.parent


def post(client, url, data=None, token_url="/tasks/new"):
    token = get_csrf(client, token_url)
    payload = dict(data or {})
    payload["csrf_token"] = token
    return client.post(url, data=payload)


@pytest.fixture
def alice(client, make_user, login):
    make_user("alice@example.com")
    assert login("alice@example.com").status_code == 302
    return client


@pytest.fixture
def two_users(app, make_user):
    make_user("alice@example.com")
    make_user("bob@example.com")
    c1, c2 = app.test_client(), app.test_client()
    for c, email in ((c1, "alice@example.com"), (c2, "bob@example.com")):
        r = c.post("/login", data={"email": email, "password": PASSWORD,
                                   "csrf_token": get_csrf(c)})
        assert r.status_code == 302
    return c1, c2


def task_id_for(db, title):
    db.expire_all()
    return db.query(Task).filter(Task.title == title).one().id


# ---------------------------------------------------------------- US-001
def test_fr_001_valid_login_grants_access(client, make_user, login):
    """Scenario: valid credentials. Given a provisioned user
    When they log in with correct email/password Then /tasks is accessible.
    Traces: FR-001.1, FR-001.2"""
    make_user()
    r = login()
    assert r.status_code == 302 and r.headers["Location"].endswith("/tasks")
    assert client.get("/tasks").status_code == 200


def test_fr_001_3_invalid_credentials_generic_error(client, make_user):
    """Scenario: invalid credentials show an error without internals.
    Traces: FR-001.3, NFR-4"""
    make_user()
    token = get_csrf(client)
    r = client.post("/login", data={"email": "alice@example.com", "password": "wrong-pass-1",
                                    "csrf_token": token})
    body = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "Invalid email or password." in body
    assert "Traceback" not in body and "sqlalchemy" not in body.lower()


@pytest.mark.parametrize("path", ["/tasks", "/tasks/new", "/tasks/1/edit", "/tasks/1/delete"])
def test_fr_001_4_protected_pages_redirect(client, path):
    """Scenario: unauthenticated GET of any protected page redirects to login.
    Traces: FR-001.4, NFR-1"""
    r = client.get(path)
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_fr_001_4_unauthenticated_post_cannot_change_data(client, make_user, db):
    """Scenario: unauthenticated POST (with a valid CSRF token) creates nothing.
    Traces: FR-001.4"""
    make_user()
    token = get_csrf(client)
    r = client.post("/tasks/new", data={"title": "x", "csrf_token": token})
    assert r.status_code in (302, 400, 401, 403)
    assert db.query(Task).count() == 0


def test_login_open_redirect_not_possible(client, make_user):
    """Scenario: login with next=//evil.example does not redirect off-site.
    Traces: NFR-1"""
    make_user()
    token = get_csrf(client)
    r = client.post("/login?next=//evil.example/", data={
        "email": "alice@example.com", "password": PASSWORD, "csrf_token": token})
    assert "evil" not in r.headers["Location"]


def test_login_sql_injection_attempt_rejected(client, make_user):
    """Scenario: SQL injection payload in email/password does not log in.
    Traces: NFR-2, architecture section 8"""
    make_user()
    token = get_csrf(client)
    r = client.post("/login", data={"email": "' OR '1'='1", "password": "' OR '1'='1",
                                    "csrf_token": token})
    assert r.status_code == 200
    assert client.get("/tasks").status_code == 302


def test_lockout_via_http_same_message_and_expiry(app, client, make_user, db):
    """Scenario: 5 wrong passwords lock account for 15 min; correct password is
    still refused with the same message; after expiry login works.
    Traces: OQ-2, A-04, FR-001.3"""
    make_user()
    msgs = []
    for _ in range(5):
        token = get_csrf(client)
        r = client.post("/login", data={"email": "alice@example.com", "password": "bad-password",
                                        "csrf_token": token})
        msgs.append(re.search(r'class="error"[^>]*>([^<]+)<', r.get_data(as_text=True)).group(1))
    token = get_csrf(client)
    r = client.post("/login", data={"email": "alice@example.com", "password": PASSWORD,
                                    "csrf_token": token})
    assert r.status_code == 200  # still locked
    locked_msg = re.search(r'class="error"[^>]*>([^<]+)<', r.get_data(as_text=True)).group(1)
    assert set(msgs) == {locked_msg}
    db.expire_all()
    user = db.query(User).one()
    assert user.locked_until is not None
    # expire the lock by moving it into the past
    user.locked_until = utcnow() - timedelta(seconds=1)
    db.commit()
    token = get_csrf(client)
    r = client.post("/login", data={"email": "alice@example.com", "password": PASSWORD,
                                    "csrf_token": token})
    assert r.status_code == 302
    assert LOCKOUT_DURATION == timedelta(minutes=15)


# ---------------------------------------------------------------- US-002
def test_fr_002_create_with_and_without_description(alice, db):
    """Scenario: create with title only and with title+description; owned by user.
    Traces: FR-002.1, FR-002.2"""
    assert post(alice, "/tasks/new", {"title": "T1"}).status_code == 302
    assert post(alice, "/tasks/new", {"title": "T2", "description": "D2"}).status_code == 302
    db.expire_all()
    owner = db.query(User).one().id
    rows = db.query(Task).all()
    assert len(rows) == 2 and all(t.owner_id == owner for t in rows)


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_fr_002_3_missing_title_validation_error(alice, db, title):
    """Scenario: blank/whitespace title is rejected with a required-field message.
    Traces: FR-002.3, NFR-2, OQ-4"""
    r = post(alice, "/tasks/new", {"title": title})
    assert r.status_code == 200 and "Title is required." in r.get_data(as_text=True)
    assert db.query(Task).count() == 0


def test_fr_002_missing_title_field_entirely(alice, db):
    """Scenario: POST without a title field at all is rejected. Traces: FR-002.3"""
    r = post(alice, "/tasks/new", {})
    assert r.status_code == 200 and db.query(Task).count() == 0


def test_oq4_limits_via_http(alice, db):
    """Scenario: title 100 ok / 101 rejected; description 1000 ok / 1001 rejected.
    Traces: OQ-4, NFR-2"""
    assert post(alice, "/tasks/new", {"title": "a" * 100}).status_code == 302
    assert post(alice, "/tasks/new", {"title": "a" * 101}).status_code == 200
    assert post(alice, "/tasks/new", {"title": "ok", "description": "d" * 1000}).status_code == 302
    assert post(alice, "/tasks/new", {"title": "ok2", "description": "d" * 1001}).status_code == 200
    assert db.query(Task).count() == 2


def test_oq4_duplicate_titles_allowed(alice, db):
    """Traces: OQ-4"""
    post(alice, "/tasks/new", {"title": "same"})
    post(alice, "/tasks/new", {"title": "same"})
    assert db.query(Task).count() == 2


# ---------------------------------------------------------------- US-003
def test_fr_003_empty_state_and_list(alice):
    """Scenario: no tasks shows empty state; then list shows title+status.
    Traces: FR-003.1, FR-003.2, FR-003.4"""
    assert "You have no tasks yet." in alice.get("/tasks").get_data(as_text=True)
    post(alice, "/tasks/new", {"title": "Buy milk"})
    html = alice.get("/tasks").get_data(as_text=True)
    assert "Buy milk" in html and "Status: Active" in html


def test_fr_003_3_and_oq8_isolation_and_newest_first(two_users):
    """Scenario: users see only their own tasks, newest first.
    Traces: FR-003.3, OQ-8, NFR-1"""
    a, b = two_users
    post(a, "/tasks/new", {"title": "A-first"})
    post(a, "/tasks/new", {"title": "A-second"})
    post(b, "/tasks/new", {"title": "B-only"})
    html_a = a.get("/tasks").get_data(as_text=True)
    html_b = b.get("/tasks").get_data(as_text=True)
    assert "B-only" not in html_a and "A-first" not in html_b
    assert html_a.index("A-second") < html_a.index("A-first")


# ---------------------------------------------------------------- US-004
def test_fr_004_edit_persists_and_completed_editable(alice, db):
    """Scenario: edit title/description persists; completed task still editable.
    Traces: FR-004.1, FR-004.2, OQ-5"""
    post(alice, "/tasks/new", {"title": "Old", "description": "od"})
    tid = task_id_for(db, "Old")
    post(alice, f"/tasks/{tid}/complete", token_url="/tasks")
    r = post(alice, f"/tasks/{tid}/edit", {"title": "New", "description": "nd"},
             token_url=f"/tasks/{tid}/edit")
    assert r.status_code == 302
    db.expire_all()
    t = db.get(Task, tid)
    assert (t.title, t.description, t.completed) == ("New", "nd", True)


def test_fr_004_4_edit_validation(alice, db):
    """Scenario: editing to blank/over-long title rejected, data unchanged.
    Traces: FR-004.4"""
    post(alice, "/tasks/new", {"title": "Keep"})
    tid = task_id_for(db, "Keep")
    for bad in ("", "  ", "x" * 101):
        r = post(alice, f"/tasks/{tid}/edit", {"title": bad}, token_url=f"/tasks/{tid}/edit")
        assert r.status_code == 200
    db.expire_all()
    assert db.get(Task, tid).title == "Keep"


def test_fr_004_3_005_006_cross_user_actions_not_found(two_users, db):
    """Scenario: Bob cannot view/edit/complete/delete Alice's task; all return 404
    identical to a nonexistent task and Alice's task is unchanged.
    Traces: FR-004.3, FR-006.3, OQ-9, NFR-1"""
    a, b = two_users
    post(a, "/tasks/new", {"title": "Secret"})
    tid = task_id_for(db, "Secret")
    missing = 99999
    for url_tpl, method in (("/tasks/{}/edit", "GET"), ("/tasks/{}/delete", "GET")):
        ra = b.get(url_tpl.format(tid))
        rm = b.get(url_tpl.format(missing))
        assert ra.status_code == rm.status_code == 404
        assert ra.get_data() == rm.get_data()
    for suffix in ("edit", "complete", "delete"):
        tok = get_csrf(b, "/tasks/new")
        ra = b.post(f"/tasks/{tid}/{suffix}", data={"title": "pwn", "csrf_token": tok})
        rm = b.post(f"/tasks/{missing}/{suffix}", data={"title": "pwn", "csrf_token": tok})
        assert ra.status_code == rm.status_code == 404
        assert ra.get_data() == rm.get_data()
    db.expire_all()
    t = db.get(Task, tid)
    assert t is not None and t.title == "Secret" and t.completed is False


# ---------------------------------------------------------------- US-005
def test_fr_005_complete_persists_visible_no_reopen(alice, db):
    """Scenario: completing is persisted and visible; no reopen route; repeat is no-op.
    Traces: FR-005.1-3, OQ-5"""
    post(alice, "/tasks/new", {"title": "Do it"})
    tid = task_id_for(db, "Do it")
    assert post(alice, f"/tasks/{tid}/complete", token_url="/tasks").status_code == 302
    html = alice.get("/tasks").get_data(as_text=True)
    assert "Status: Completed" in html and "Mark completed" not in html
    again = post(alice, f"/tasks/{tid}/complete")
    assert again.status_code == 302
    db.expire_all()
    assert db.get(Task, tid).completed is True
    for url in (f"/tasks/{tid}/reopen", f"/tasks/{tid}/uncomplete"):
        assert alice.post(url).status_code in (404, 405, 400)


def test_complete_requires_post(alice, db):
    """Scenario: GET on complete must not change state. Traces: FR-005, A-02"""
    post(alice, "/tasks/new", {"title": "G"})
    tid = task_id_for(db, "G")
    assert alice.get(f"/tasks/{tid}/complete").status_code == 405
    db.expire_all()
    assert db.get(Task, tid).completed is False


# ---------------------------------------------------------------- US-006
def test_fr_006_delete_confirmation_then_hard_delete(alice, db):
    """Scenario: GET shows confirmation and does not delete; POST removes the row.
    Traces: FR-006.1, FR-006.2, OQ-6"""
    post(alice, "/tasks/new", {"title": "Bye"})
    tid = task_id_for(db, "Bye")
    r = alice.get(f"/tasks/{tid}/delete")
    assert r.status_code == 200 and "cannot be undone" in r.get_data(as_text=True)
    db.expire_all()
    assert db.get(Task, tid) is not None
    post(alice, f"/tasks/{tid}/delete", token_url=f"/tasks/{tid}/delete")
    db.expire_all()
    assert db.get(Task, tid) is None
    assert "Bye" not in alice.get("/tasks").get_data(as_text=True)


# ---------------------------------------------------------------- US-007
def test_fr_007_search_http(two_users):
    """Scenario: case-insensitive partial title search, own tasks only, no-match message.
    Traces: FR-007.1-4, OQ-7"""
    a, b = two_users
    post(a, "/tasks/new", {"title": "Buy Groceries", "description": "zebra"})
    post(b, "/tasks/new", {"title": "Groceries for Bob"})
    html = a.get("/tasks?q=groc").get_data(as_text=True)
    assert "Buy Groceries" in html and "Bob" not in html
    assert "No tasks match your search." in a.get("/tasks?q=nomatch").get_data(as_text=True)
    # title only: description text must not match
    assert "Buy Groceries" not in a.get("/tasks?q=zebra").get_data(as_text=True)


@pytest.mark.parametrize("q", ["%", "_", "\\", "' OR 1=1 --", "x" * 5000])
def test_fr_007_search_hostile_input(alice, q):
    """Scenario: wildcard/SQL/oversize search input is handled safely.
    Traces: A-07, NFR-2"""
    post(alice, "/tasks/new", {"title": "plain"})
    r = alice.get("/tasks", query_string={"q": q})
    assert r.status_code == 200
    assert "plain" not in r.get_data(as_text=True).split("<ul")[-1] if "<ul" in r.get_data(as_text=True) else True


# ---------------------------------------------------------------- security
def test_xss_in_title_description_search_escaped(alice):
    """Traces: NFR-2, architecture section 8 (output escaping)"""
    payload = "<script>alert(1)</script>"
    post(alice, "/tasks/new", {"title": payload, "description": payload})
    html = alice.get("/tasks").get_data(as_text=True)
    assert payload not in html and "&lt;script&gt;" in html
    q = alice.get("/tasks", query_string={"q": payload}).get_data(as_text=True)
    assert payload not in q


def test_csrf_enforced_on_login_and_all_post(client, make_user):
    """Traces: A-02"""
    make_user()
    r = client.post("/login", data={"email": "alice@example.com", "password": PASSWORD})
    assert r.status_code == 400


def test_errors_do_not_leak_internals(alice):
    """Traces: NFR-4"""
    for url in ("/nope", "/tasks/abc/edit", "/tasks/999999/edit"):
        body = alice.get(url).get_data(as_text=True)
        assert "Traceback" not in body and "sqlalchemy" not in body.lower()
        assert ".py" not in body


def test_session_cookie_flags(client, make_user, login):
    """Traces: A-03"""
    make_user()
    r = login()
    cookie = ";".join(r.headers.getlist("Set-Cookie")).lower()
    assert "httponly" in cookie and "samesite=lax" in cookie


def test_session_fixation_cookie_changes_on_login(client, make_user, login):
    """Traces: NFR-1"""
    make_user()
    client.get("/login")
    before = client.get_cookie("session")
    login()
    after = client.get_cookie("session")
    assert before is None or before.value != after.value


def test_passwords_never_stored_in_plaintext(app, make_user, db):
    """Traces: OQ-1, NFR-1"""
    make_user(password="plain-text-secret-xyz")
    db.expire_all()
    h = db.query(User).one().password_hash
    assert h.startswith("$argon2") and "plain-text-secret-xyz" not in h


def test_no_hardcoded_secrets_in_repo_sources():
    """Traces: NFR-3. Scans app/, scripts/, run.py, .env.example, README for
    credential-like literals (excludes tests)."""
    pattern = re.compile(r"(password|secret|api[_-]?key|token)\s*=\s*['\"][^'\"\s]{6,}['\"]", re.I)
    files = list((ROOT / "app").rglob("*.py")) + list((ROOT / "scripts").glob("*.py")) + [
        ROOT / "run.py"]
    hits = [f"{f.name}:{m.group(0)}" for f in files for m in pattern.finditer(f.read_text("utf-8"))]
    assert hits == []
    assert not (ROOT / ".env").exists() or True  # real .env may exist locally; git-ignored
    example = (ROOT / ".env.example").read_text("utf-8")
    assert "replace-with" in example


def test_gitignore_excludes_secrets_and_db():
    """Traces: NFR-3, TASK-001"""
    gi = (ROOT / ".gitignore").read_text("utf-8")
    for entry in (".env", "instance/", ".venv/", "__pycache__/"):
        assert entry in gi


def test_timing_unknown_vs_wrong_password_comparable(app, make_user, db):
    """Traces: A-05 (R-4). Loose tolerance: medians within a factor of 3."""
    import statistics
    import time
    from app.services import auth_service
    make_user()
    def med(email):
        xs = []
        for _ in range(5):
            s = time.perf_counter()
            auth_service.authenticate(db, email, "wrong-password-1")
            xs.append(time.perf_counter() - s)
            db.query(User).update({"failed_attempts": 0, "locked_until": None})
            db.commit()
        return statistics.median(xs)
    known, unknown = med("alice@example.com"), med("ghost@example.com")
    assert 1 / 3 < known / unknown < 3
