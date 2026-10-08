"""Login routes (C2/C3)."""
from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user

from app import login_manager
from app.models import User, get_session
from app.services import auth_service
from app.validation import validate_login_input

bp = Blueprint("auth", __name__)

GENERIC_LOGIN_ERROR = "Invalid email or password."


@login_manager.user_loader
def load_user(user_id):
    try:
        return get_session().get(User, int(user_id))
    except (TypeError, ValueError):
        return None


@bp.route("/")
def index():
    return redirect(url_for("tasks.list_view"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("tasks.list_view"))

    if request.method == "GET":
        return render_template("login.html", email="", error=None)

    clean, errors = validate_login_input(
        request.form.get("email"), request.form.get("password")
    )
    if errors:
        return render_template(
            "login.html", email=clean["email"], error=None, field_errors=errors
        )

    user = auth_service.authenticate(get_session(), clean["email"], clean["password"])
    if user is None:
        # Same message for unknown email, wrong password and locked account.
        return render_template("login.html", email=clean["email"], error=GENERIC_LOGIN_ERROR)

    session.clear()  # avoid session fixation
    login_user(user, remember=False)
    session.permanent = True  # enables the sliding 30 minute timeout
    # The post-login target is fixed; a client-supplied "next" is ignored.
    return redirect(url_for("tasks.list_view"))
