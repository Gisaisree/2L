import re

import pytest

from app.models import Task
from tests.conftest import get_csrf


@pytest.fixture
def alice(client, make_user, login):
    user = make_user("alice@example.com")
    login("alice@example.com")
    return user


def post(client, url, **data):
    data["csrf_token"] = get_csrf(client, "/tasks/new")
    return client.post(url, data=data)


def test_empty_state(client, alice):
    assert "You have no tasks yet" in client.get("/tasks").get_data(as_text=True)


def test_create_and_view(client, alice):
    resp = post(client, "/tasks/new", title="  Buy milk  ", description="2 litres")
    assert resp.status_code == 302
    html = client.get("/tasks").get_data(as_text=True)
    assert "Buy milk" in html and "2 litres" in html and "Status: Active" in html


def test_create_requires_title(client, alice):
    resp = post(client, "/tasks/new", title="   ", description="x")
    assert resp.status_code == 200
    assert "Title is required." in resp.get_data(as_text=True)


def test_create_over_length(client, alice, db):
    resp = post(client, "/tasks/new", title="a" * 101)
    assert "at most 100" in resp.get_data(as_text=True)
    resp = post(client, "/tasks/new", title="ok", description="d" * 1001)
    assert "at most 1000" in resp.get_data(as_text=True)
    assert db.query(Task).count() == 0


def _task_id(db, title):
    return db.query(Task).filter(Task.title == title).one().id


def test_edit(client, alice, db):
    post(client, "/tasks/new", title="old", description="")
    tid = _task_id(db, "old")
    assert "old" in client.get(f"/tasks/{tid}/edit").get_data(as_text=True)
    post(client, f"/tasks/{tid}/edit", title="new", description="desc")
    db.expire_all()
    assert db.get(Task, tid).title == "new"
    bad = post(client, f"/tasks/{tid}/edit", title="", description="")
    assert "Title is required." in bad.get_data(as_text=True)


def test_complete_and_noop(client, alice, db):
    post(client, "/tasks/new", title="t")
    tid = _task_id(db, "t")
    post(client, f"/tasks/{tid}/complete")
    html = client.get("/tasks").get_data(as_text=True)
    assert "Status: Completed" in html
    assert "Mark completed" not in html  # hidden for completed tasks
    resp = post(client, f"/tasks/{tid}/complete")
    assert "already completed" in client.get(resp.headers["Location"]).get_data(as_text=True)


def test_delete_requires_confirmation_then_removes(client, alice, db):
    post(client, "/tasks/new", title="gone")
    tid = _task_id(db, "gone")
    page = client.get(f"/tasks/{tid}/delete")
    assert page.status_code == 200 and "Permanently delete" in page.get_data(as_text=True)
    assert db.query(Task).count() == 1  # GET did not delete
    post(client, f"/tasks/{tid}/delete")
    assert db.query(Task).count() == 0
    assert "gone" not in client.get("/tasks").get_data(as_text=True)


def test_search_and_no_match_message(client, alice):
    post(client, "/tasks/new", title="Buy Milk")
    post(client, "/tasks/new", title="Walk dog")
    html = client.get("/tasks?q=milk").get_data(as_text=True)
    assert "Buy Milk" in html and "Walk dog" not in html
    assert "No tasks match your search." in client.get("/tasks?q=zzz").get_data(as_text=True)


def test_other_users_tasks_are_not_found(app, client, alice, make_user, db):
    bob = make_user("bob@example.com")
    foreign = Task(owner_id=bob.id, title="bobs-secret")
    db.add(foreign)
    db.commit()
    tid = foreign.id
    assert "bobs-secret" not in client.get("/tasks").get_data(as_text=True)
    assert "bobs-secret" not in client.get("/tasks?q=bobs").get_data(as_text=True)
    assert client.get(f"/tasks/{tid}/edit").status_code == 404
    assert client.get(f"/tasks/{tid}/delete").status_code == 404
    assert post(client, f"/tasks/{tid}/edit", title="hacked").status_code == 404
    assert post(client, f"/tasks/{tid}/complete").status_code == 404
    assert post(client, f"/tasks/{tid}/delete").status_code == 404
    missing = post(client, "/tasks/99999/complete")
    assert missing.status_code == 404
    assert missing.get_data() == post(client, f"/tasks/{tid}/complete").get_data()
    db.expire_all()
    task = db.get(Task, tid)
    assert task.title == "bobs-secret" and task.completed is False


def test_xss_escaped(client, alice):
    payload = "<script>alert(1)</script>"
    post(client, "/tasks/new", title=payload, description="<img src=x onerror=alert(2)>")
    html = client.get("/tasks").get_data(as_text=True)
    assert payload not in html and "&lt;script&gt;" in html
    assert "<img src=x" not in html


def test_missing_csrf_rejected_for_every_state_change(client, alice, db):
    post(client, "/tasks/new", title="t")
    tid = _task_id(db, "t")
    for url in ["/tasks/new", f"/tasks/{tid}/edit", f"/tasks/{tid}/complete", f"/tasks/{tid}/delete"]:
        resp = client.post(url, data={"title": "x"})
        assert resp.status_code == 400
    assert db.query(Task).count() == 1
    db.expire_all()
    assert db.get(Task, tid).completed is False


def test_forms_contain_csrf_token(client, alice, db):
    post(client, "/tasks/new", title="t")
    tid = _task_id(db, "t")
    for url in ["/tasks/new", f"/tasks/{tid}/edit", f"/tasks/{tid}/delete", "/tasks"]:
        html = client.get(url).get_data(as_text=True)
        assert re.search(r'name="csrf_token"', html), url
