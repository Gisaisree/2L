"""Task operations (C4). Every query is scoped to the owning user id."""
from sqlalchemy import func

from app.models import Task


class TaskNotFoundError(Exception):
    """Task does not exist or belongs to another user (indistinguishable, OQ-9)."""


def _escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def create_task(session, owner_id, title, description=""):
    task = Task(owner_id=owner_id, title=title, description=description or "")
    session.add(task)
    session.commit()
    return task


def list_tasks(session, owner_id, query=None):
    """Own tasks, newest first; optional case-insensitive partial title search."""
    stmt = session.query(Task).filter(Task.owner_id == owner_id)
    if query:
        pattern = "%" + _escape_like(query.strip().lower()) + "%"
        stmt = stmt.filter(func.py_lower(Task.title).like(pattern, escape="\\"))
    return stmt.order_by(Task.created_at.desc(), Task.id.desc()).all()


def get_task(session, owner_id, task_id):
    task = (
        session.query(Task)
        .filter(Task.id == task_id, Task.owner_id == owner_id)
        .one_or_none()
    )
    if task is None:
        raise TaskNotFoundError()
    return task


def update_task(session, owner_id, task_id, title, description):
    task = get_task(session, owner_id, task_id)
    task.title = title
    task.description = description or ""
    session.commit()
    return task


def complete_task(session, owner_id, task_id):
    """Mark completed (one-way). Returns (task, changed)."""
    task = get_task(session, owner_id, task_id)
    if task.completed:
        return task, False
    task.completed = True
    session.commit()
    return task, True


def delete_task(session, owner_id, task_id):
    task = get_task(session, owner_id, task_id)
    session.delete(task)
    session.commit()
