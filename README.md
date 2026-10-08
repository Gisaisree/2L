# Online Task Management

A small server-rendered Flask application. Users log in (accounts are pre-provisioned) and create, view, edit, complete (one-way), delete and search their own tasks. Local use only.

Stack: Python 3, Flask, SQLAlchemy + SQLite, Flask-Login, Flask-WTF (CSRF), argon2-cffi, pytest.

## Setup (Windows, PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env
# Edit .env and set SECRET_KEY to a long random value, e.g. from:
python -c "import secrets; print(secrets.token_hex(32))"
```

`.env` is git-ignored. Never commit it.

## Create a user account

There is no self-registration. Create accounts with the operator script (the password is typed at a hidden prompt, minimum 8 characters):

```powershell
python scripts/provision_users.py user@example.com
```

## Run

```powershell
python scripts/run_dev.py     # or: python run.py
```

Open http://127.0.0.1:5000/ and log in. The app binds to localhost only and debug mode is off. The SQLite database is created at `instance/tasks.db` (git-ignored).

## Test

```powershell
python -m pytest
```

## Routes

| Path | Method | Purpose |
|------|--------|---------|
| `/` | GET | Redirects to the task list |
| `/login` | GET, POST | Login form |
| `/tasks` | GET | Own tasks, newest first; `?q=` searches titles |
| `/tasks/new` | GET, POST | Create a task |
| `/tasks/<id>/edit` | GET, POST | Edit title and description |
| `/tasks/<id>/complete` | POST | Mark completed (one-way) |
| `/tasks/<id>/delete` | GET (confirmation), POST | Permanently delete |

## Behaviour notes

- Lockout: 5 consecutive failed logins lock the account for 15 minutes (auto-expiring). The login error is always "Invalid email or password."
- Sessions expire after 30 minutes of inactivity (sliding). There is no logout (out of scope).
- Another user's task is reported as "not found".
- These values are constants in `app/__init__.py`.

## Security notes

- Secrets come from the environment or the local `.env` only. The app refuses to start without `SECRET_KEY`.
- HTTPS is not set up. It is required if the app is ever served beyond the local machine; then set `SESSION_COOKIE_SECURE=true`.
- Logs never contain passwords, session tokens or CSRF tokens.

## Project structure

```text
app/        application package (routes/, services/, templates/, static/, models.py, validation.py, errors.py)
scripts/    provision_users.py, run_dev.py
tests/      pytest suite (routes/, services/, scripts/ and module tests)
run.py      entry point
instance/   local SQLite database (git-ignored)
```

## Further documentation

- `FRD.md` - functional requirements and validation status
- `DESIGN.md` - architecture and design summary (full detail in `architecture.md`)
- `requirements.md`, `design-review.md`, `impl-plan.md`, `validation-report.md`, `release-report.md`, `CHANGELOG.md`

Known limitations: responsive/accessibility behaviour not verified in a browser; the interactive provisioning prompt was not verified live; Code Review was waived. See `validation-report.md`.
