# Pull Request Description (LOCAL DRAFT)

**NOT SUBMITTED. No Pull Request exists. No branch, commit, push or remote was used or created. This file is a local draft only.**

Title (proposed): Online Task Management - initial local release candidate

## Summary

Adds the Online Task Management application, a small server-rendered Flask app where pre-provisioned users log in and create, view, edit, complete, delete and search their own tasks. It implements the approved requirements (FR-001 to FR-007, NFR-1 to NFR-4) per the approved architecture and implementation plan, for local use only.

## Changes Made

- `app/` (`__init__.py`, `models.py`, `validation.py`, `errors.py`, `routes/`, `services/`, `templates/`, `static/`): application code, with the ownership filter in the task service.
- `run.py`, `scripts/run_dev.py`: local run entry points.
- `scripts/provision_users.py`: operator script to create accounts (no self-registration).
- `tests/`: 125 tests including `test_acceptance_scenarios.py` (requirement-traced scenarios).
- `requirements.txt`, `pytest.ini`: pinned dependencies and test configuration.
- `.env.example`, `.gitignore`: placeholder configuration and exclusion of secrets, database and caches.
- `README.md`: setup, run, test, routes and behaviour notes.
- `requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`, `validation-report.md`: approved SDLC artifacts.
- `release-report.md`, `CHANGELOG.md`, `pr-description.md`, `reviewer-checklist.md`: release documentation.
- Not part of the product (workflow material, per A-11): `.claude/`, `skills/`, `inputs/`.

## Test Evidence

Actual output from this release phase (fresh venv, `pip install -r requirements.txt`, clean copy of the project, no `.env`, Python 3.13.15):

```text
python -m pytest
........................................................................ [ 57%]
.....................................................                    [100%]
125 passed in 13.86s
```

From `validation-report.md` (not re-run in this phase): `pip_audit -r requirements.txt` reported "No known vulnerabilities found"; live smoke check returned `/login` 200 and `/tasks` 302 to `/login` when unauthenticated. No CI exists.

## Known Limitations

- NOT TESTED: responsive layout and WCAG behaviour in a browser (L-1).
- NOT VERIFIED: interactive provisioning prompt run live; README venv/pip steps were only re-verified by the clean-install run above (L-2).
- Timing-equalisation test is loose, not proof of constant time (L-3).
- Code Review was WAIVED by the human and not performed (L-4).
- Out of scope by design: logout, registration, password reset, audit logging, HTTPS, deployment.
- Version number and rollback procedure: Not specified in the approved project artifacts.

## Reviewer Checklist

- [ ] Correctness reviewed
- [ ] Security reviewed
- [ ] Error handling reviewed
- [ ] Test coverage reviewed
- [ ] Code clarity reviewed
- [ ] DRY principle reviewed
- [ ] Dependency safety reviewed
