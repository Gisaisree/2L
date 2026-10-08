# Architecture and Design Summary: Online Task Management

Summary of the approved `architecture.md` (sections 11-12 are authoritative where they supersede sections 7-9) and `design-review.md`, checked against the implemented tree. Full detail, diagrams (component and sequence, in Mermaid) and traceability remain in `architecture.md`. No wireframes exist in the approved artifacts.

## 1. Approved Stack
Python 3, Flask (server-rendered templates, minimal CSS), SQLAlchemy with SQLite, Flask-Login (signed session cookie), Flask-WTF (CSRF), argon2-cffi, pytest. Pinned in `requirements.txt`. Hosting: local machine only.

## 2. Components (high-level design)

| ID | Component | Implemented in |
|----|-----------|----------------|
| C1 | Web UI | `app/templates/`, `app/static/style.css` |
| C2 | Web application / HTTP layer | `app/__init__.py` (factory), `app/routes/auth.py`, `app/routes/tasks.py` |
| C3 | Authentication and session manager | `app/services/auth_service.py` |
| C4 | Task service (all queries scoped to the current user) | `app/services/task_service.py` |
| C5 | Validation layer | `app/validation.py` |
| C6 | Error handling | `app/errors.py` |
| C7 | Data store (users, tasks) | `app/models.py`, SQLite file under `instance/` (git-ignored) |
| C8 | Configuration and secrets | environment / local `.env`, `.env.example`, `scripts/provision_users.py` |

## 3. Low-Level Design Points (approved amendments A-01 to A-13)
- Data model: `users(id, email unique, password_hash, failed_attempts, locked_until)`; `tasks(id, owner_id FK, title, description, completed, created_at, updated_at)`; indexes on `tasks.owner_id` and `(owner_id, title)`.
- Security constants live in `app/__init__.py`: lockout threshold 5, lockout duration 15 minutes, session timeout 30 minutes (sliding).
- CSRF protection on all state-changing requests including login; GET never changes state.
- Session cookie: HttpOnly, SameSite=Lax, Secure when `SESSION_COOKIE_SECURE=true`.
- Unknown email and wrong password give the same message with a dummy hash check; locked accounts give the same message.
- Foreign task ids return the same "not found" as nonexistent ids.
- Logs never contain passwords, session tokens or CSRF tokens. The app refuses to start without `SECRET_KEY`.
- Search escapes LIKE wildcards and compares lower-cased text.

## 4. Routes
`/` (redirect), `/login`, `/tasks` (`?q=` search), `/tasks/new`, `/tasks/<id>/edit`, `/tasks/<id>/complete` (POST), `/tasks/<id>/delete` (GET confirmation, POST). No logout, registration or reset routes (out of scope).

## 5. Project Structure (checked against the actual tree)
```text
app/            __init__.py, models.py, validation.py, errors.py, routes/, services/, templates/, static/
scripts/        provision_users.py, run_dev.py
tests/          conftest.py, routes/, services/, scripts/, test_*.py (125 tests)
run.py          entry point (127.0.0.1:5000, debug off)
instance/       local SQLite database (git-ignored)
requirements.txt, pytest.ini, .env.example, .gitignore, README.md
```
Workflow artifacts at the repository root: `requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`, `validation-report.md`, `release-report.md`, `CHANGELOG.md`, `pr-description.md`, `reviewer-checklist.md`. The `docs/` folder and `run_dev.sh` from architecture section 9 are intentionally not used (section 11 item 7, A-10). `.claude/`, `inputs/`, `skills/` are workflow files, not part of the product.

## 6. Known Documentation Inconsistencies (not changed here)
`architecture.md` sections 7-9 still carry "Proposed" labels and `docs/`/`run_dev.sh`; the `impl-plan.md` section 18 status line is stale (validation OBS-1). These are earlier-phase documents; the human decides whether to tidy them.
