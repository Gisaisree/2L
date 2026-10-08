# Changelog

Local-only project. No commits, tags or remote releases exist. Version number: Not specified in the approved project artifacts, so the entry is marked Unreleased. Date of preparation: 2026-10-08.

## [Unreleased] - Initial local release candidate (awaiting human approval)

### Added
- Online Task Management Flask application: login with pre-provisioned accounts (argon2 hashes, 5-failure / 15-minute lockout, 30-minute sliding session timeout, CSRF protection).
- Task features per user: create, list (newest first), edit, complete (one-way), delete with confirmation, case-insensitive partial title search.
- Own-task isolation: another user's task is reported as not found.
- Safe error pages and log hygiene (no passwords or tokens logged).
- Operator scripts: `scripts/provision_users.py`, `scripts/run_dev.py`; entry point `run.py`.
- Test suite: 125 tests under `tests/` (85 implementation, 40 acceptance-scenario tests).
- Documentation: `README.md`, `.env.example`, SDLC artifacts (`requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`, `validation-report.md`, `release-report.md`).

### Known limitations
- Responsive/accessibility behaviour not verified in a browser; interactive provisioning prompt not verified live; Code Review waived. See `release-report.md` and `validation-report.md`.
