"""Authentication and lockout rules (C3)."""
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app import LOCKOUT_DURATION, LOCKOUT_THRESHOLD
from app.models import User, utcnow

_hasher = PasswordHasher()
# Hash of a random throwaway value, used so unknown emails cost the same time
# as a real verification (A-05). Computed lazily; never matches a real password.
_dummy_hash = None


def hash_password(password):
    return _hasher.hash(password)


def _verify(stored_hash, password):
    try:
        return _hasher.verify(stored_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def _get_dummy_hash():
    global _dummy_hash
    if _dummy_hash is None:
        import secrets

        _dummy_hash = _hasher.hash(secrets.token_urlsafe(32))
    return _dummy_hash


def find_user_by_email(session, email):
    return session.query(User).filter(User.email == email.strip().lower()).one_or_none()


def authenticate(session, email, password, now=None):
    """Return the User on success, otherwise None.

    Unknown email, wrong password and locked account all return None, so
    callers cannot tell them apart (A-04, A-05).
    """
    now = now or utcnow()
    user = find_user_by_email(session, email)

    if user is None:
        _verify(_get_dummy_hash(), password)
        return None

    # Auto-expire an elapsed lock.
    if user.locked_until is not None and user.locked_until <= now:
        user.locked_until = None
        user.failed_attempts = 0

    password_ok = _verify(user.password_hash, password)

    if user.locked_until is not None:
        # Still locked: same outcome as a bad password, no counter change.
        session.commit()
        return None

    if not password_ok:
        user.failed_attempts = (user.failed_attempts or 0) + 1
        if user.failed_attempts >= LOCKOUT_THRESHOLD:
            user.locked_until = now + LOCKOUT_DURATION
            user.failed_attempts = 0
        session.commit()
        return None

    user.failed_attempts = 0
    user.locked_until = None
    session.commit()
    return user


def create_user(session, email, password):
    """Create an account (used by the provisioning script). Caller validates."""
    user = User(email=email.strip().lower(), password_hash=hash_password(password))
    session.add(user)
    session.commit()
    return user
