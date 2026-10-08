import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "provision_users.py"
spec = importlib.util.spec_from_file_location("provision_users_script", SCRIPT)
provision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provision)


def test_creates_account_with_argon2_hash(db):
    user = provision.provision_user(db, "New@Example.com", "longenough1")
    assert user.email == "new@example.com"
    assert user.password_hash.startswith("$argon2")
    assert "longenough1" not in user.password_hash


def test_short_password_rejected(db):
    with pytest.raises(provision.ProvisioningError):
        provision.provision_user(db, "a@example.com", "1234567")


def test_duplicate_rejected(db):
    provision.provision_user(db, "a@example.com", "12345678")
    with pytest.raises(provision.ProvisioningError):
        provision.provision_user(db, "A@example.com", "87654321")


def test_bad_email_rejected(db):
    with pytest.raises(provision.ProvisioningError):
        provision.provision_user(db, "not-an-email", "12345678")


def test_no_hardcoded_credentials_in_script():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "getpass" in text
    assert "sys.argv[2]" not in text


def test_main_uses_prompt_and_reports_mismatch(monkeypatch, capsys):
    answers = iter(["abcdefgh1", "different1"])
    monkeypatch.setattr(provision.getpass, "getpass", lambda _p: next(answers))
    assert provision.main(["a@example.com"]) == 1
    assert "do not match" in capsys.readouterr().out
