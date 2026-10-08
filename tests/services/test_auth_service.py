from datetime import timedelta
from unittest import mock

from app import LOCKOUT_DURATION, LOCKOUT_THRESHOLD
from app.models import utcnow
from app.services import auth_service

PW = "correct-horse-battery"


def test_password_stored_as_argon2_hash(make_user):
    user = make_user()
    assert user.password_hash.startswith("$argon2")
    assert PW not in user.password_hash


def test_valid_login(db, make_user):
    make_user()
    assert auth_service.authenticate(db, "Alice@Example.com", PW) is not None


def test_failures_unknown_wrong_all_none(db, make_user):
    make_user()
    assert auth_service.authenticate(db, "nobody@example.com", PW) is None
    assert auth_service.authenticate(db, "alice@example.com", "wrong") is None


def test_unknown_email_performs_hash_check(db):
    with mock.patch.object(auth_service, "_verify", wraps=auth_service._verify) as spy:
        auth_service.authenticate(db, "nobody@example.com", "x")
    assert spy.call_count == 1


def test_four_failures_do_not_lock(db, make_user):
    make_user()
    for _ in range(LOCKOUT_THRESHOLD - 1):
        assert auth_service.authenticate(db, "alice@example.com", "bad") is None
    assert auth_service.authenticate(db, "alice@example.com", PW) is not None


def test_five_failures_lock_even_for_correct_password(db, make_user):
    user = make_user()
    now = utcnow()
    for _ in range(LOCKOUT_THRESHOLD):
        auth_service.authenticate(db, "alice@example.com", "bad", now=now)
    assert user.locked_until == now + LOCKOUT_DURATION
    assert auth_service.authenticate(db, "alice@example.com", PW, now=now) is None


def test_lock_expires_after_15_minutes(db, make_user):
    make_user()
    now = utcnow()
    for _ in range(LOCKOUT_THRESHOLD):
        auth_service.authenticate(db, "alice@example.com", "bad", now=now)
    almost = now + LOCKOUT_DURATION - timedelta(seconds=1)
    assert auth_service.authenticate(db, "alice@example.com", PW, now=almost) is None
    later = now + LOCKOUT_DURATION
    assert auth_service.authenticate(db, "alice@example.com", PW, now=later) is not None


def test_success_resets_counter(db, make_user):
    user = make_user()
    for _ in range(LOCKOUT_THRESHOLD - 1):
        auth_service.authenticate(db, "alice@example.com", "bad")
    auth_service.authenticate(db, "alice@example.com", PW)
    assert user.failed_attempts == 0
    for _ in range(LOCKOUT_THRESHOLD - 1):
        auth_service.authenticate(db, "alice@example.com", "bad")
    assert auth_service.authenticate(db, "alice@example.com", PW) is not None


def test_no_counting_while_locked(db, make_user):
    user = make_user()
    now = utcnow()
    for _ in range(LOCKOUT_THRESHOLD):
        auth_service.authenticate(db, "alice@example.com", "bad", now=now)
    locked_until = user.locked_until
    auth_service.authenticate(db, "alice@example.com", "bad", now=now)
    assert user.locked_until == locked_until
    assert user.failed_attempts == 0
