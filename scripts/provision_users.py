"""Create a pre-provisioned user account (OQ-1).

Usage:  python scripts/provision_users.py user@example.com

The password is read from a hidden prompt; it is never taken from an argument,
stored in source, echoed or logged.
"""
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services import auth_service  # noqa: E402
from app.validation import validate_new_account  # noqa: E402


class ProvisioningError(Exception):
    """Raised with a safe, user-facing message."""


def provision_user(session, email, password):
    """Validate and create an account. Returns the new User."""
    clean, errors = validate_new_account(email, password)
    if errors:
        raise ProvisioningError("; ".join(errors.values()))
    if auth_service.find_user_by_email(session, clean["email"]) is not None:
        raise ProvisioningError("An account with that email already exists.")
    return auth_service.create_user(session, clean["email"], clean["password"])


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("Usage: python scripts/provision_users.py <email>")
        return 2
    email = argv[0]

    password = getpass.getpass("Password (min 8 characters): ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        return 1

    from app import create_app

    app = create_app()
    session = app.extensions["session_factory"]()
    try:
        provision_user(session, email, password)
    except ProvisioningError as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        session.close()
    print("Account created.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
