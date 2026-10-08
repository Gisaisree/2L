"""Task routes (C2). All routes require login; state changes use POST + CSRF."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models import get_session
from app.services import task_service
from app.services.task_service import TaskNotFoundError
from app.validation import validate_task_input

bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def _get_or_404(task_id):
    try:
        return task_service.get_task(get_session(), current_user.id, task_id)
    except TaskNotFoundError:
        abort(404)


@bp.route("")
@login_required
def list_view():
    query = request.args.get("q", "").strip()
    tasks = task_service.list_tasks(get_session(), current_user.id, query or None)
    return render_template("tasks.html", tasks=tasks, query=query)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "GET":
        return render_template("task_form.html", task=None, values={}, errors={})
    clean, errors = validate_task_input(
        request.form.get("title"), request.form.get("description")
    )
    if errors:
        values = {
            "title": request.form.get("title", ""),
            "description": request.form.get("description", ""),
        }
        return render_template("task_form.html", task=None, values=values, errors=errors)
    task_service.create_task(
        get_session(), current_user.id, clean["title"], clean["description"]
    )
    flash("Task created.")
    return redirect(url_for("tasks.list_view"))


@bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit(task_id):
    task = _get_or_404(task_id)
    if request.method == "GET":
        values = {"title": task.title, "description": task.description}
        return render_template("task_form.html", task=task, values=values, errors={})
    clean, errors = validate_task_input(
        request.form.get("title"), request.form.get("description")
    )
    if errors:
        values = {
            "title": request.form.get("title", ""),
            "description": request.form.get("description", ""),
        }
        return render_template("task_form.html", task=task, values=values, errors=errors)
    task_service.update_task(
        get_session(), current_user.id, task_id, clean["title"], clean["description"]
    )
    flash("Task updated.")
    return redirect(url_for("tasks.list_view"))


@bp.route("/<int:task_id>/complete", methods=["POST"])
@login_required
def complete(task_id):
    try:
        _task, changed = task_service.complete_task(get_session(), current_user.id, task_id)
    except TaskNotFoundError:
        abort(404)
    flash("Task marked as completed." if changed else "Task is already completed.")
    return redirect(url_for("tasks.list_view"))


@bp.route("/<int:task_id>/delete", methods=["GET", "POST"])
@login_required
def delete(task_id):
    task = _get_or_404(task_id)  # GET shows the confirmation step (OQ-6)
    if request.method == "GET":
        return render_template("confirm_delete.html", task=task)
    task_service.delete_task(get_session(), current_user.id, task_id)
    flash("Task deleted.")
    return redirect(url_for("tasks.list_view"))
