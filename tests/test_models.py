import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.models import Task, User


def test_schema_columns_and_indexes(app):
    insp = inspect(app.extensions["db_engine"])
    assert {c["name"] for c in insp.get_columns("users")} == {
        "id", "email", "password_hash", "failed_attempts", "locked_until"
    }
    assert {c["name"] for c in insp.get_columns("tasks")} == {
        "id", "owner_id", "title", "description", "completed", "created_at", "updated_at"
    }
    index_cols = {tuple(i["column_names"]) for i in insp.get_indexes("tasks")}
    assert ("owner_id",) in index_cols
    assert ("owner_id", "title") in index_cols


def test_duplicate_email_rejected(db):
    db.add(User(email="a@b.co", password_hash="x"))
    db.commit()
    db.add(User(email="a@b.co", password_hash="y"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_task_requires_existing_owner(db):
    db.add(Task(owner_id=999, title="t"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_timestamps_and_duplicate_titles(db, make_user):
    user = make_user()
    t1 = Task(owner_id=user.id, title="same")
    t2 = Task(owner_id=user.id, title="same")
    db.add_all([t1, t2])
    db.commit()
    assert t1.created_at is not None and t1.updated_at is not None
    assert t1.completed is False
    before = t1.updated_at
    t1.title = "changed"
    db.commit()
    assert t1.updated_at >= before
    assert t1.created_at <= t1.updated_at


def test_deleting_user_cascades_tasks(db, make_user):
    user = make_user()
    db.add(Task(owner_id=user.id, title="t"))
    db.commit()
    db.delete(user)
    db.commit()
    assert db.query(Task).count() == 0
