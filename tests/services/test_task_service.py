import time

import pytest

from app.services import task_service as ts
from app.services.task_service import TaskNotFoundError


@pytest.fixture
def two_users(make_user):
    return make_user("alice@example.com"), make_user("bob@example.com")


def test_create_and_list_newest_first(db, two_users):
    alice, _ = two_users
    ts.create_task(db, alice.id, "first", "")
    ts.create_task(db, alice.id, "second", "d")
    titles = [t.title for t in ts.list_tasks(db, alice.id)]
    assert titles == ["second", "first"]


def test_no_cross_user_visibility(db, two_users):
    alice, bob = two_users
    task = ts.create_task(db, alice.id, "secret", "")
    assert ts.list_tasks(db, bob.id) == []
    assert ts.list_tasks(db, bob.id, "secret") == []
    for call in (
        lambda: ts.get_task(db, bob.id, task.id),
        lambda: ts.update_task(db, bob.id, task.id, "x", ""),
        lambda: ts.complete_task(db, bob.id, task.id),
        lambda: ts.delete_task(db, bob.id, task.id),
    ):
        with pytest.raises(TaskNotFoundError):
            call()
    assert ts.get_task(db, alice.id, task.id).title == "secret"
    assert ts.get_task(db, alice.id, task.id).completed is False


def test_nonexistent_same_error(db, two_users):
    alice, _ = two_users
    with pytest.raises(TaskNotFoundError):
        ts.get_task(db, alice.id, 12345)


def test_complete_is_one_way_and_idempotent(db, two_users):
    alice, _ = two_users
    task = ts.create_task(db, alice.id, "t", "")
    _t, changed = ts.complete_task(db, alice.id, task.id)
    assert changed is True and task.completed is True
    _t, changed = ts.complete_task(db, alice.id, task.id)
    assert changed is False and task.completed is True
    ts.update_task(db, alice.id, task.id, "edited", "d")  # still editable
    assert task.completed is True and task.title == "edited"


def test_delete_removes(db, two_users):
    alice, _ = two_users
    task = ts.create_task(db, alice.id, "t", "")
    ts.delete_task(db, alice.id, task.id)
    assert ts.list_tasks(db, alice.id) == []


def test_search_case_insensitive_partial_non_ascii(db, two_users):
    alice, _ = two_users
    for title in ["Buy Milk", "milkshake", "ÉCOLE visit", "other"]:
        ts.create_task(db, alice.id, title, "")
    assert {t.title for t in ts.list_tasks(db, alice.id, "MILK")} == {"Buy Milk", "milkshake"}
    assert {t.title for t in ts.list_tasks(db, alice.id, "école")} == {"ÉCOLE visit"}
    assert ts.list_tasks(db, alice.id, "zzz") == []


def test_search_wildcards_are_literal(db, two_users):
    alice, _ = two_users
    for title in ["100% done", "a_b", "axb", "back\\slash", "plain"]:
        ts.create_task(db, alice.id, title, "")
    assert [t.title for t in ts.list_tasks(db, alice.id, "%")] == ["100% done"]
    assert [t.title for t in ts.list_tasks(db, alice.id, "a_b")] == ["a_b"]
    assert [t.title for t in ts.list_tasks(db, alice.id, "\\")] == ["back\\slash"]


def test_search_never_returns_other_users(db, two_users):
    alice, bob = two_users
    ts.create_task(db, bob.id, "shared word", "")
    assert ts.list_tasks(db, alice.id, "shared") == []


def test_thousand_tasks_under_two_seconds(db, two_users):
    alice, _ = two_users
    db.add_all([ts.Task(owner_id=alice.id, title=f"task {i}") for i in range(1000)])
    db.commit()
    start = time.perf_counter()
    assert len(ts.list_tasks(db, alice.id)) == 1000
    assert len(ts.list_tasks(db, alice.id, "task 99")) == 11
    assert time.perf_counter() - start < 2
