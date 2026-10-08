"""Online Task Management application package (app factory, C2 / C8)."""
import os
from datetime import timedelta
from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# ---------------------------------------------------------------------------
# Security constants (code constants, single place; impl-plan section 15 item 9)
# These must stay defined before any submodule import that reads them.
# ---------------------------------------------------------------------------
LOCKOUT_THRESHOLD = 5  # consecutive failed logins before lockout (A-04)
LOCKOUT_DURATION = timedelta(minutes=15)  # auto-expiring lock (A-04)
SESSION_TIMEOUT = timedelta(minutes=30)  # sliding inactivity timeout (A-06)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = None  # no informational message on redirect


def load_env_file(path):
    """Load KEY=VALUE lines from a local .env file into os.environ.

    Existing environment variables win. Values are never logged.
    """
    path = Path(path)
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def create_app(test_config=None):
    """Application factory."""
    if test_config is None:
        load_env_file(PROJECT_ROOT / ".env")

    app = Flask(__name__, instance_relative_config=True)

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DATABASE_URL=os.environ.get("DATABASE_URL"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_env_flag("SESSION_COOKIE_SECURE", False),
        PERMANENT_SESSION_LIFETIME=SESSION_TIMEOUT,
        SESSION_REFRESH_EACH_REQUEST=True,  # sliding inactivity timeout
        WTF_CSRF_TIME_LIMIT=None,  # CSRF token valid for the session lifetime
    )
    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY is not configured. Set it in the environment or in a "
            "local .env file (see .env.example)."
        )

    os.makedirs(app.instance_path, exist_ok=True)

    from app import models

    models.init_db(app)

    csrf.init_app(app)
    login_manager.init_app(app)

    from app.errors import register_error_handlers
    from app.routes import auth as auth_routes
    from app.routes import tasks as task_routes

    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(task_routes.bp)
    register_error_handlers(app)

    return app
