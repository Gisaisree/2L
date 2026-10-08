"""Server-side input validation (C5). Reject by default."""
import re

TITLE_MAX = 100
DESCRIPTION_MAX = 1000
PASSWORD_MIN = 8
EMAIL_MAX = 254

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_task_input(title, description):
    """Return (clean, errors). `errors` maps field name -> message."""
    errors = {}
    clean = {"title": "", "description": ""}

    if not isinstance(title, str):
        errors["title"] = "Title is required."
    else:
        stripped = title.strip()
        if not stripped:
            errors["title"] = "Title is required."
        elif len(stripped) > TITLE_MAX:
            errors["title"] = f"Title must be at most {TITLE_MAX} characters."
        else:
            clean["title"] = stripped

    if description is None:
        description = ""
    if not isinstance(description, str):
        errors["description"] = "Description must be text."
    elif len(description) > DESCRIPTION_MAX:
        errors["description"] = f"Description must be at most {DESCRIPTION_MAX} characters."
    else:
        clean["description"] = description

    return clean, errors


def validate_login_input(email, password):
    """Return (clean, errors). Only presence is checked for login."""
    errors = {}
    clean = {"email": "", "password": ""}

    if not isinstance(email, str) or not email.strip():
        errors["email"] = "Email is required."
    else:
        clean["email"] = email.strip().lower()

    if not isinstance(password, str) or not password:
        errors["password"] = "Password is required."
    else:
        clean["password"] = password

    return clean, errors


def validate_new_account(email, password):
    """Validation for the provisioning script (A-07: 8 character minimum)."""
    errors = {}
    clean = {"email": "", "password": ""}

    if not isinstance(email, str) or not email.strip():
        errors["email"] = "Email is required."
    else:
        candidate = email.strip().lower()
        if len(candidate) > EMAIL_MAX or not _EMAIL_RE.match(candidate):
            errors["email"] = "Email address is not valid."
        else:
            clean["email"] = candidate

    if not isinstance(password, str) or not password:
        errors["password"] = "Password is required."
    elif len(password) < PASSWORD_MIN:
        errors["password"] = f"Password must be at least {PASSWORD_MIN} characters."
    else:
        clean["password"] = password

    return clean, errors
