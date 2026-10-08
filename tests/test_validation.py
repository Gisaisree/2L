import pytest

from app.validation import (
    validate_login_input,
    validate_new_account,
    validate_task_input,
)


@pytest.mark.parametrize("title", [None, "", "   ", "\t\n", 123, ["a"]])
def test_title_missing_or_blank_rejected(title):
    _clean, errors = validate_task_input(title, "")
    assert "title" in errors


def test_title_boundaries():
    assert validate_task_input("a", "")[1] == {}
    assert validate_task_input("a" * 100, "")[1] == {}
    assert "title" in validate_task_input("a" * 101, "")[1]


def test_title_is_trimmed_before_length_check():
    clean, errors = validate_task_input("  " + "a" * 100 + "  ", "")
    assert errors == {}
    assert clean["title"] == "a" * 100


def test_description_boundaries():
    assert validate_task_input("t", None)[1] == {}
    assert validate_task_input("t", "")[1] == {}
    assert validate_task_input("t", "d" * 1000)[1] == {}
    assert "description" in validate_task_input("t", "d" * 1001)[1]
    assert "description" in validate_task_input("t", 5)[1]


def test_login_requires_both_fields():
    _c, errors = validate_login_input("", "")
    assert set(errors) == {"email", "password"}
    _c, errors = validate_login_input(None, None)
    assert set(errors) == {"email", "password"}
    clean, errors = validate_login_input("  A@B.com ", "pw")
    assert errors == {} and clean["email"] == "a@b.com"


def test_new_account_password_minimum():
    assert "password" in validate_new_account("a@b.co", "1234567")[1]
    assert validate_new_account("a@b.co", "12345678")[1] == {}


@pytest.mark.parametrize("email", ["", "nope", "a@b", "a b@c.com", None])
def test_new_account_bad_email(email):
    assert "email" in validate_new_account(email, "12345678")[1]
