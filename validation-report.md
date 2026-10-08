# Validation Report: Online Task Management

**Status: APPROVED by the human ("yes i approve the validation result", given directly to the main session; recorded there). The human did not answer questions 2 and 3, so the limitations (L-1 to L-3) are accepted as documented and the stale document wording is left as is.**
**Scope:** local machine only. No commits, pushes, remote actions, Jira or Confluence. No application source was modified during validation; only one test file was added (`tests/test_acceptance_scenarios.py`).

## 1. Validation Summary

- Full suite: **125 passed, 0 failed** (85 existing implementation tests + 40 verification tests added in this phase), `python -m pytest` using the project venv.
- Dependency audit: `pip_audit -r requirements.txt` reported "No known vulnerabilities found".
- Live smoke check: the app started via `run.py` and answered `/login` 200 and `/tasks` 302 redirect to `/login` for an unauthenticated request.
- No defects were found. Limitations exist (section 13), chiefly: no browser-based responsive/accessibility check, the interactive provisioning prompt was not run live, and Code Review (Step 6) was waived.
- **Overall result: PASS WITH LIMITATIONS** (section 14).

**Code Review waiver (recorded as instructed):** Code Review (Step 6) was explicitly WAIVED by the human because `.claude/agents/CodeReview.md` is a copy of the Architecture Agent and has no valid definition. No code-review phase was performed or is claimed. The code reading in this report was done only to support validation (requirement/architecture traceability and security checks) and is not a substitute for a code review.

## 2. Artifacts Reviewed

| Artifact | Result |
|----------|--------|
| `requirements.md` | Read; header says APPROVED |
| `architecture.md` (sections 11-12 authoritative) | Read; header says APPROVED |
| `design-review.md` | Read; APPROVED |
| `impl-plan.md` | Read; header says APPROVED, defaults in its section 15 |
| Source: `app/` (all modules, templates, CSS), `scripts/`, `run.py`, `README.md`, `.env.example`, `.gitignore`, `requirements.txt`, `pytest.ini` | Read |
| Existing tests (85) under `tests/` | Read (names) and executed |

Approval check: the approvals are recorded in the artifact headers (given to the main session per those headers). This agent cannot verify them independently and takes them as stated. Implementation is present and ready for validation.

## 3. Test Environment

- Windows 11, Python 3.13.15 in `.venv`; pytest 9.1.1; Flask 3.1.3; SQLAlchemy 2.1.4; Flask-Login 0.6.3; Flask-WTF 1.3.0; argon2-cffi 25.1.0 (all match `requirements.txt` pins).
- `pip_audit` 2.10.1 is installed in the venv (not listed in `requirements.txt`, consistent with impl-plan OQ-10 "if it can be installed locally").
- Tests use the Flask test client with a per-test temporary SQLite database. No `.env` file exists in the project root (verified), so no real secrets were used.
- Live checks used throwaway `SECRET_KEY` values and a database in the session scratchpad directory.

## 4. Test Execution Summary

| Run | Command | Result |
|-----|---------|--------|
| Existing tests | `python -m pytest -v` | 85 passed |
| Verification suite (new) | `python -m pytest tests/test_acceptance_scenarios.py -v` | first run 39 passed, 1 failed (see note); after correcting the test, all 40 passed |
| Full suite | `python -m pytest` | **125 passed in 14.36 s** |
| Dependency audit | `python -m pip_audit -r requirements.txt` | No known vulnerabilities found |
| Startup without `SECRET_KEY` | `python run.py` | `RuntimeError: SECRET_KEY is not configured...` (clear, no secret) |
| Run helper without `.env` | `python scripts/run_dev.py` | prints "No .env file found. Copy .env.example to .env and set SECRET_KEY first.", exit 1 |
| Live server | `run.py` with env vars, curl | `/login` 200; `/tasks` 302 to `/login` |

Note on the one failure: it was a defect in my new test (it fetched a CSRF token from `/tasks` after the only task had been completed, a page with no form). It was not an application defect; the test was corrected to take the token from `/tasks/new`. The earlier failed result is disclosed here rather than hidden.

The new test file derives each test from an acceptance criterion as a Gherkin-style scenario in its docstring, with requirement IDs ("Traces:").

## 5. Requirements Validation

Evidence key: E = existing test file in `tests/`; V = new test in `tests/test_acceptance_scenarios.py`; code = source inspected.

| Req | Expected | Evidence | Validation | Result |
|-----|----------|----------|------------|--------|
| FR-001.1 | Enter email/password | `login.html`, `auth.py` | V `valid_login_grants_access`; E `test_login_page_has_fields_and_csrf` | PASS |
| FR-001.2 | Valid credentials grant access | `auth_service.authenticate` | V, E `test_valid_login_redirects_to_tasks` | PASS |
| FR-001.3 | Appropriate error on invalid | `GENERIC_LOGIN_ERROR` | V `invalid_credentials_generic_error`, E `test_failure_messages_identical` | PASS |
| FR-001.4 | Protected pages blocked | `@login_required`, unauthorized handler | V 4 parametrized GETs + unauthenticated POST creates nothing | PASS |
| FR-002.1/2.2 | Create with title, optional description, owned by user | `task_service.create_task` | V `create_with_and_without_description` | PASS |
| FR-002.3 | Missing title error | `validate_task_input` | V blank, whitespace, field absent; E | PASS |
| FR-003.1/3.2 | List own tasks with title and status | `tasks.html` | V `empty_state_and_list` | PASS |
| FR-003.3 | No other users' tasks | owner filter | V two-user isolation | PASS |
| FR-003.4 | Empty state | `tasks.html` | V | PASS |
| FR-004.1/4.2 | Edit and persist | `update_task` | V `edit_persists_and_completed_editable` | PASS |
| FR-004.3 | Cannot update others' tasks | `get_task` owner filter | V cross-user edit returns 404 identical to nonexistent; data unchanged | PASS |
| FR-004.4 | Required-field validation on edit | route + C5 | V blank/whitespace/101 chars rejected, data unchanged | PASS |
| FR-005.1-5.3 | Complete, persist, visible | `complete_task`, `tasks.html` | V `complete_persists_visible_no_reopen`; GET on complete returns 405 | PASS |
| FR-006.1/6.2 | Delete own task; gone from list | `delete_task` | V `delete_confirmation_then_hard_delete` | PASS |
| FR-006.3 | Cannot delete others' | owner filter | V cross-user delete 404, row intact | PASS |
| FR-007.1/7.2 | Search own by title | `list_tasks` | V `search_http` (case-insensitive, partial, title only) | PASS |
| FR-007.3 | Own tasks only | owner filter | V, E `test_search_never_returns_other_users` | PASS |
| FR-007.4 | No-match message | `tasks.html` | V | PASS |
| NFR-1 | Data protected from unauthorised access | login gate, owner filter, cookie flags | V, E (see section 9) | PASS |
| NFR-2 | Input validated | `validation.py` | V boundary tests via HTTP, E unit boundaries; XSS/SQL-injection payloads | PASS |
| NFR-3 | No hard-coded secrets | env-based `SECRET_KEY`; `.env.example` placeholder | V source scan test, startup failure test, manual inspection | PASS |
| NFR-4 | Safe error messages | `errors.py` | V no traceback/path in 404/400/405 bodies; E generic 500 and log tests | PASS |
| OQ-1 | Pre-provisioned accounts; argon2 hashes | `provision_users.py`, `auth_service` | V hash check `$argon2`; E provisioning tests | PASS (interactive prompt: see limitation L-2) |
| OQ-2 | 8-char min, lockout 5, session 30 min | constants in `app/__init__.py` | V lockout via HTTP incl. same message and expiry; E time-controlled sliding timeout | PASS |
| OQ-3, OQ-12 | Out of scope (logout, reset, etc.) | no logout/reset/registration routes | E `test_no_logout_route`; route list in README | PASS (absent as required) |
| OQ-4 | Title/description rules, duplicates allowed | `validation.py` | V 100/101 and 1000/1001, duplicates | PASS |
| OQ-5 | One-way completion; completed tasks editable | `complete_task` | V; no reopen route (reopen/uncomplete URLs return 404/405) | PASS |
| OQ-6 | Hard delete with confirmation | `confirm_delete.html` | V | PASS |
| OQ-7 | Case-insensitive partial title search, no status filter | `list_tasks` | V, E (non-ASCII, wildcards) | PASS |
| OQ-8 | Newest first; about 1000 tasks | order_by | V ordering; E `test_thousand_tasks_under_two_seconds` | PASS |
| OQ-9 | Foreign task returns not found | `TaskNotFoundError` | V byte-identical 404 body for foreign vs nonexistent | PASS |
| OQ-10 | Timestamps stored | `models.py` | E `test_timestamps_and_duplicate_titles` | PASS |
| OQ-11 | Responsive, accessible, under 2 s | viewport meta, labels, skip link, focus styles, fluid CSS | Static inspection only; 2 s tested at service level | PARTIAL (no browser/WCAG tool run; see L-1) |
| OQ-13 | Jira waived | none created | n/a | PASS (nothing created) |

## 6. Acceptance Criteria Validation

The acceptance criteria are FR-001.1 to FR-007.4 (requirements.md states them as the criteria) and the per-task acceptance criteria in impl-plan.md. The FR-level results are in section 5; the task-level results are in section 8. All FR-level criteria: PASS (no new criteria were created).

## 7. Architecture and Folder Structure Validation

| Check | Result |
|-------|--------|
| C1 templates/static, C2 `__init__` and `routes/`, C3 `auth_service`, C4 `task_service`, C5 `validation`, C6 `errors`, C7 `models`, C8 `.env.example`, `provision_users.py`, env loading | All present with the designed responsibilities. PASS |
| Task operations scoped to user id only in the Task Service | Confirmed in `task_service.py`; routes call `get_task`/services with `current_user.id`. PASS |
| Approved integrations (no external dependencies) | None added. PASS |
| Tree matches section 9 plus A-10 and impl-plan resolutions | Present: `run.py`, `scripts/run_dev.py`, `tests/conftest.py`, `instance/` (git-ignored, empty at validation), `tests/routes/`, `tests/services/`, `tests/scripts/` (approved by impl-plan OQ-4). Not created, as intended: `docs/`, `run_dev.sh`. PASS |
| Files not named in the tree | Templates (`base`, `login`, `tasks`, `task_form`, `confirm_delete`, `error`), `app/static/style.css`, `tests/routes/test_session_security.py`; names left to the implementer by impl-plan OQ-2. This phase added `tests/test_acceptance_scenarios.py`. Not deviations. |
| `.gitkeep` (impl-plan OQ-6) | Not present; directories are non-empty, so not needed. Noted only. |
| Git hygiene | `git status --short --ignored` shows `.venv/`, caches, `__pycache__` ignored; `.env` absent. PASS |

Minor observation (not a deviation): the lockout counter is reset to 0 at the moment the lock is applied as well as on success; this is consistent with A-04 (lock for 15 minutes, counter reset on success). No unauthorised architectural change found.

## 8. Implementation Plan Validation

| Task | Status | Evidence |
|------|--------|----------|
| TASK-001 skeleton and hygiene | COMPLETED | Tree check; `.gitignore` test; no real secrets in `.env.example` |
| TASK-002 config, factory, security plumbing | COMPLETED | Missing SECRET_KEY test and live run; cookie flags, CSRF, sliding timeout tests pass |
| TASK-003 data models | COMPLETED | `test_models.py`: columns, indexes, unique email, FK, cascade, timestamps |
| TASK-004 validation | COMPLETED | Boundary tests |
| TASK-005 error handling and log hygiene | COMPLETED | `test_errors.py`; V no internals in responses |
| TASK-006 provisioning script | PARTIALLY COMPLETED (see L-2) | Unit tests pass (hash, short password, duplicate, bad email, getpass use); live interactive run not possible non-interactively |
| TASK-007 auth service | COMPLETED | Lockout 4 vs 5, expiry, reset, identical failures, dummy hash |
| TASK-008 task service | COMPLETED | Two-user isolation, search wildcards and non-ASCII, one-way completion, 1000-task timing |
| TASK-009 auth routes and login page | COMPLETED | Route tests; open-redirect check |
| TASK-010 task routes | COMPLETED | Route tests per story, negative cases |
| TASK-011 templates and static | PARTIALLY COMPLETED | Escaping verified by test; responsive/accessibility only statically inspected (L-1) |
| TASK-012 run helpers and README | COMPLETED | Run helper messages and live server verified; README walkthrough partly verified (L-2, section 10) |
| TASK-013 end-to-end security and acceptance validation | COMPLETED (this report) with L-1, L-2 | Full suite, pip-audit, secret scan |

## 9. Security Validation

| Control | Evidence | Result |
|---------|----------|--------|
| Authentication, argon2 hashes only | V hash starts with `$argon2` and not plaintext; E | PASS |
| Generic failure message for unknown, wrong password, locked | V HTTP lockout test (same message for all); E | PASS |
| Lockout 5 failures / 15 min, auto expiry | V (HTTP), E (time-controlled) | PASS |
| Timing equalisation for unknown email | E dummy-hash test; V timing test (medians within factor of 3). Loose tolerance only; this is not proof of constant time | PASS (limited) |
| Authorization / ownership isolation | V cross-user view, edit, complete, delete, search; foreign 404 identical to nonexistent | PASS |
| Session cookie HttpOnly, SameSite=Lax | V, E; Secure flag configurable (E) and false by default for local HTTP | PASS |
| Session fixation | E `test_session_cleared_on_login`; V cookie value changes on login | PASS |
| Sliding 30 min timeout | E time-controlled test | PASS |
| CSRF on all state changes including login | V login without token returns 400; E every state-changing route without token rejected | PASS |
| GET cannot change state | V GET on complete returns 405; delete GET shows confirmation only | PASS |
| Input validation / injection | V SQL-injection payloads in login and search; hostile search strings; 5000-char query | PASS |
| XSS output escaping | V `<script>` in title, description and search escaped; no `|safe` in templates (inspected) | PASS |
| Open redirect | V `next` parameter ignored | PASS |
| Error handling / information exposure | V and E | PASS |
| Log hygiene (no passwords, session or CSRF tokens) | E log capture tests | PASS |
| Secrets | V source scan for credential-like literals (none found); `.env` absent and git-ignored; `.env.example` placeholder only | PASS |
| Dependency security | `pip_audit` against `requirements.txt`: no known vulnerabilities | PASS (point-in-time, depends on the audit database at run time) |
| Transport security | Not implemented by design (local only); README documents it | NOT APPLICABLE locally |

Residual risks accepted in the approved artifacts (not defects): no logout (F-12), lockout can be used against a known email (R-3), no audit logging. This report does not claim the system is secure; it reports only that the listed checks passed.

## 10. Output Document Content Quality Check

| Document | Result | Evidence |
|----------|--------|----------|
| `requirements.md` | PASS | Complete, no placeholders; status APPROVED |
| `architecture.md` | PASS (with note) | Complete. Sections 7-9 contain stale "Proposed" labels and the `docs/` and `run_dev.sh` entries, superseded by sections 11-12 as the artifact itself and the human state; implementation follows 11-12 |
| `design-review.md` | PASS | Complete; approved |
| `impl-plan.md` | PASS (with note) | Complete. Section 18 still says "Not ready until the human approves", while its header records approval. Minor internal inconsistency in a status line only |
| `README.md` | PASS with NOT VERIFIED items | Content matches the code: routes, constants (5/15 min/30 min), `.env` handling, localhost binding, debug off. Verified by execution: `run.py`/`scripts/run_dev.py` behaviour, server start, `/login` and `/tasks`. NOT VERIFIED: `python -m venv`/`pip install` steps (not re-run), `Copy-Item`, the interactive provisioning prompt run live, logging in through a browser |
| `.env.example` | PASS | Placeholder values only (`replace-with-a-long-random-value`); `SESSION_COOKIE_SECURE=false` documented |
| `.gitignore` | PASS | Excludes `.env`, `instance/`, DB files, venv, caches |
| `requirements.txt` | PASS | Versions pinned and match the installed set |
| Terminology consistency | PASS | Generic message text, routes and limits in README match code and tests |
| Secrets in output | PASS | None found in docs, config examples, or sources (automated scan plus inspection) |

## 11. Defects and Failures

**No application defects were found.** No requirement or acceptance criterion failed.

Test-side note: one of my new tests failed on first run because of an error in the test (CSRF token fetched from a page without a form); corrected, not an application defect.

Observations (non-blocking, no action required unless the human wishes):
- OBS-1: `architecture.md` sections 7-9 and the `impl-plan.md` section 18 status line still carry stale wording (see section 10).
- OBS-2: `pip_audit` is installed in the venv but not recorded in `requirements.txt`.
- OBS-3: `instance/` exists but was empty at validation time (tests use temporary databases; live checks used the scratchpad).

## 12. Traceability Matrix

| Requirement | Task | Source | Test / Validation | Result |
|-------------|------|--------|-------------------|--------|
| FR-001.1-1.4 | 004, 007, 009, 011 | `routes/auth.py`, `services/auth_service.py`, `login.html` | test_auth_routes, test_auth_service, V US-001 tests | PASS |
| FR-002.1-2.3 | 003, 004, 008, 010, 011 | `task_service.create_task`, `validation.py`, `task_form.html` | test_task_routes, V create tests | PASS |
| FR-003.1-3.4 | 008, 010, 011 | `list_tasks`, `tasks.html` | test_task_service, V list/isolation | PASS |
| FR-004.1-4.4 | 004, 008, 010, 011 | `update_task`, `routes/tasks.edit` | V edit, validation, cross-user | PASS |
| FR-005.1-5.3 | 008, 010, 011 | `complete_task` | test_task_service, V complete | PASS |
| FR-006.1-6.3 | 008, 010, 011 | `delete_task`, `confirm_delete.html` | V delete, cross-user | PASS |
| FR-007.1-7.4 | 008, 010, 011 | `list_tasks` | V and E search tests | PASS |
| NFR-1 | 002, 007, 008 | owner filter, cookie config | isolation, cookie, session tests | PASS |
| NFR-2 | 004 | `validation.py` | boundary and hostile-input tests | PASS |
| NFR-3 | 001, 002, 006, 012 | `.env.example`, `.gitignore`, `create_app` | scan tests, startup failure | PASS |
| NFR-4 | 005 | `errors.py` | test_errors, V | PASS |
| OQ-1, OQ-2 | 003, 006, 007, 002 | models, provisioning, auth_service, config | lockout/timeout/provisioning tests | PASS (L-2) |
| OQ-4 to OQ-10 | 003, 004, 008 | validation, task_service, models | rules tests | PASS |
| OQ-11 | 003, 011, 013 | CSS, templates, indexes | 2 s service test; static inspection | PARTIAL |

## 13. Limitations

- L-1: Responsive layout and WCAG 2.1 AA behaviour were NOT TESTED in a browser or with an accessibility tool. Only static inspection was done (viewport meta tag, `label for` associations, skip link, focus outline, `role="alert"`, wrapping CSS; the stylesheet has no media queries and relies on fluid layout). Colour contrast was not measured. The 2-second target was verified only at the service level (1000 tasks), not end-to-end in a browser.
- L-2: `scripts/provision_users.py` was attempted with piped input but the Windows hidden `getpass` prompt reads from the console and hung; that attempt was stopped. The interactive prompt is therefore NOT VERIFIED live; it is covered by unit tests (validation, hashing, duplicate rejection, getpass use). Related README steps (`python -m venv`, `pip install`) were not re-run.
- L-3: The timing-equalisation test is statistical with a loose tolerance and does not prove constant time.
- L-4: Code Review was waived by the human and is not part of this validation.
- L-5: Human approvals recorded in artifact headers could not be independently verified by this agent.
- L-6: `pip_audit` results are point-in-time and depend on network access to the vulnerability database; HTTPS and deployment hardening are out of scope (local only).
- L-7: Concurrency, load beyond 1000 tasks, and browsers other than a live curl check were not tested.

## 14. Overall Result

**PASS WITH LIMITATIONS.** All functional requirements, NFRs, and security checks that could be validated passed (125/125 tests, no known vulnerable dependencies, no defects). OQ-11 (responsiveness/accessibility) is PARTIAL and the interactive provisioning prompt is not verified live; neither is known to fail.

## 15. Recommendations

1. Perform a manual browser check at narrow and desktop widths, plus an accessibility pass (keyboard-only, contrast), to close L-1.
2. Run the README walkthrough once on a fresh clone (venv, `.env`, provisioning prompt in a real terminal, login) to close L-2.
3. Optionally tidy stale wording in `architecture.md` sections 7-9 and `impl-plan.md` section 18 (documents only; the human decides).
4. Optionally record `pip-audit` as a development tool note in the README.
5. If a valid Code Review agent definition becomes available, consider performing the waived Step 6.

## 16. Human Approval

Validation is complete. Please review the validation report and the identified failures, limitations, or recommendations. Do you approve the validation result?

- [ ] Human has reviewed this validation report.
- [ ] Human approves the validation result.

Status: **APPROVED** (see header).
