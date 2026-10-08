# Implementation Plan: Online Task Management

**Status: APPROVED by the human ("implementation plan is approved and use defaults", given directly to the main session; status recorded there). Defaults for the open questions are in section 15.** Local machine only; no remote URLs, repositories, pushes, PRs, Jira or Confluence.
**Local machine only.** No remote repositories, URLs, pull requests, Jira, Confluence, pushes or commits are part of this plan.

Legend: **Confirmed** = from approved artifacts. **Proposal** = planner suggestion. **Assumption** = unconfirmed. **TBD** = needs human decision.

## 1. Overview

Plan to build a small server-rendered Flask web application in which authenticated users log in and create, view, update, complete (one-way), delete and search their own tasks. Tasks are ordered by dependency, each traced to requirements (FR/NFR/OQ), architecture components (C1-C8) and design-review findings (F-01..F-13, via architecture amendments A-01..A-13). No application code is written in Phase 4.

## 2. Input Artifacts

| Artifact | State | Notes |
|----------|-------|-------|
| `requirements.md` | APPROVED | FR-001..FR-007, NFR-1..NFR-4, OQ-1..OQ-13 |
| `architecture.md` | APPROVED; section 11 resolved; section 12 applies design-review changes | Sections 7 and 8 status labels and sections 9 folder tree are partly superseded by sections 11 and 12 (see Open Question 1) |
| `design-review.md` | APPROVED | Result: ready with minor changes; 0 critical/high; all findings addressed via architecture section 12 |

Repository inspection: git status shows only untracked `.claude/`, `inputs/`, `skills/`, `requirements.md`, `architecture.md`, `design-review.md`. No application source, tests or config exist. The workflow directories are not part of the product (A-11).

Precedence applied where the architecture conflicts with itself: section 11/12 (later, resolved) override section 7-9 text. Specifically: `docs/` is not used (docs stay at root); `scripts/run_dev.sh` is replaced by `scripts/run_dev.py`; `run.py`, `instance/` and `tests/conftest.py` are added (A-10).

## 3. Scope

Confirmed in scope: login (US-001), create (US-002), view (US-003), update (US-004), complete (US-005), delete (US-006), search (US-007); NFR-1..NFR-4; pre-provisioning script for accounts (OQ-1); lockout (15 min, A-04); sliding 30-minute inactivity timeout (A-06); CSRF protection (A-02); session cookie attributes (A-03); log hygiene (A-13); minimal data model (A-07).

## 4. Out of Scope

User registration, password reset, logout, remember-me, task sharing, due dates, priorities, categories, administrator functions, audit logging, pagination, task reopening, hosting/deployment, HTTPS setup (required only if ever deployed beyond local), Confluence/Jira, commits and pushes, moving documents into `docs/`.

## 5. Implementation Strategy

1. Create the exact approved skeleton first, then foundation (config, app factory, CSRF, sessions).
2. Build the data layer and cross-cutting layers (validation, errors) in parallel.
3. Build services (auth, task) over the data layer; the ownership filter lives only in the Task Service.
4. Build routes and templates on top of services.
5. Add run helpers and README; run the full validation pass.
6. Tests are written alongside each task in Phase 5 under `tests/` (mirroring `app/`); this plan only defines validation approach.

Proposal (not specified in artifacts): Phase 5 follows the sequence in section 6 with a validation step (pytest) after each task.

## 6. Implementation Sequence

```text
TASK-001 Project skeleton and repo hygiene
   |
TASK-002 Configuration, app factory, security plumbing (C8, C2)
   |--------------------------+---------------------+
TASK-003 Data models (C7)   TASK-004 Validation (C5)  TASK-005 Error handling and logging (C6)
   |                          |                         |
   +--> TASK-006 Provisioning script (C8) <-- needs 003 + 004
   +--> TASK-007 Auth service (C3)  <-- needs 003 + 004
   +--> TASK-008 Task service (C4)  <-- needs 003 + 004
TASK-007 --> TASK-009 Auth routes + login page (C2, C3, C1)
TASK-008 + TASK-009 --> TASK-010 Task routes (C2)
TASK-002 --> TASK-011 Base templates/static (C1) --> completed with 009/010 pages
TASK-009 + TASK-010 + TASK-011 --> TASK-012 Run helpers and README
All --> TASK-013 End-to-end security and acceptance validation
```

## 7. Implementation Tasks

Design Review IDs below refer to findings F-xx and the architecture amendment that applied them (A-xx).

### TASK-001 Project skeleton and repository hygiene
- Objective: Create the approved project tree exactly (empty or stub files only) and the support files.
- Requirement IDs: NFR-3 (git-ignore secrets); structural support for all.
- Architecture Component: Project Folder Structure (architecture section 9 plus A-10); C8.
- Design Review IDs: F-10, F-11 (A-10, A-11).
- Dependencies: none.
- Expected Changes (exact paths): `app/__init__.py`, `app/routes/auth.py`, `app/routes/tasks.py`, `app/services/auth_service.py`, `app/services/task_service.py`, `app/validation.py`, `app/errors.py`, `app/models.py`, `app/templates/`, `app/static/`, `tests/conftest.py`, `tests/routes/`, `tests/services/`, `tests/test_validation.py`, `tests/test_errors.py`, `tests/test_models.py`, `scripts/provision_users.py`, `scripts/run_dev.py`, `run.py`, `requirements.txt`, `pytest.ini`, `.env.example`, `.gitignore`, `README.md`. `instance/` is created at runtime and git-ignored. Empty directories may need placeholder handling (TBD, Open Question 6). Reconcile note: root-level docs stay at root; `docs/` and `scripts/run_dev.sh` are not created.
- Security Considerations: `.gitignore` excludes `.env`, `instance/`, local database, venv, caches, build output. `.env.example` placeholders only.
- Validation: directory listing compared to the approved tree; confirm ignored files do not appear in `git status`.
- Acceptance Criteria: every path above exists; no path outside the approved tree is created; no real secret in any file.

### TASK-002 Configuration, app factory and security plumbing
- Objective: App factory in `app/__init__.py` loading settings from environment/local `.env`; register blueprints, error handlers, Flask-Login, Flask-WTF CSRF; set session cookie attributes and 30-minute sliding inactivity timeout; define SQLite location under `instance/`.
- Requirement IDs: NFR-3, NFR-1, OQ-2, FR-001.4.
- Architecture Component: C8, C2 (and C3 session configuration).
- Design Review IDs: F-02, F-03, F-06 (A-02, A-03, A-06).
- Dependencies: TASK-001.
- Expected Changes: `app/__init__.py`, `.env.example` (placeholders for SECRET_KEY and database settings), `requirements.txt` (Flask, SQLAlchemy, Flask-Login, Flask-WTF, argon2-cffi, pytest; versions TBD, Open Question 7).
- Security Considerations: SECRET_KEY from environment only, app refuses to start without it; cookie HttpOnly, SameSite=Lax, Secure when HTTPS; CSRF enabled globally for state-changing requests; no secrets logged.
- Validation: unit tests of factory (missing SECRET_KEY fails); test client confirms cookie attributes; POST without CSRF token rejected; session expires after 30 minutes inactivity and is refreshed by activity (time-controlled test).
- Acceptance Criteria: app starts with test config; missing SECRET_KEY raises a clear non-sensitive error; CSRF failure returns a safe response; timeout behaviour is sliding.

### TASK-003 Data models and data access
- Objective: Implement `users(id, email unique, password_hash, failed_attempts, locked_until)` and `tasks(id, owner_id FK, title, description, completed, created_at, updated_at)` with indexes on `tasks.owner_id` and `(owner_id, title)`; table creation approach.
- Requirement IDs: FR-002.2, FR-004.2, FR-005.2, OQ-1, OQ-10, OQ-11 (performance).
- Architecture Component: C7.
- Design Review IDs: F-07, F-09 (A-07, A-09).
- Dependencies: TASK-002.
- Expected Changes: `app/models.py`; `tests/test_models.py`.
- Security Considerations: hashes only; parameterised access through SQLAlchemy; no raw string-built SQL; foreign key and unique email enforced.
- Validation: unit tests for constraints, timestamps (created/updated), cascade/ownership; index existence.
- Acceptance Criteria: schema matches A-07 exactly; created_at set on insert and updated_at on update; duplicate task titles allowed (OQ-4); duplicate email rejected. Data types, lengths and migration tool: Not specified in the approved project artifacts (see Open Question 5).

### TASK-004 Validation layer
- Objective: Server-side validation of login and task input.
- Requirement IDs: NFR-2, FR-002.3, FR-004.4, OQ-4.
- Architecture Component: C5.
- Design Review IDs: F-07 (A-07).
- Dependencies: TASK-001 (can run in parallel with TASK-003 and TASK-005).
- Expected Changes: `app/validation.py`; `tests/test_validation.py`.
- Security Considerations: reject by default; title trimmed, 1-100 chars, whitespace-only rejected; description optional, max 1000; email and password presence checked for login; no input echoed unsafely.
- Validation: unit tests with boundary values (0, 1, 100, 101 chars; 1000, 1001; whitespace-only; None; non-string).
- Acceptance Criteria: all OQ-4 rules enforced; each failure yields a clear, field-level message without internals.

### TASK-005 Central error handling and log hygiene
- Objective: Map errors (validation, not found, CSRF failure, unauthorized, unexpected) to safe messages; details only in server log.
- Requirement IDs: NFR-4, FR-001.3, OQ-9.
- Architecture Component: C6.
- Design Review IDs: F-13 (A-13).
- Dependencies: TASK-002 (handler registration); can run in parallel with TASK-003/004.
- Expected Changes: `app/errors.py`; `tests/test_errors.py`.
- Security Considerations: no stack traces in responses; logs never include passwords, session tokens or CSRF tokens; foreign-task access returns the same not-found as a missing task.
- Validation: tests forcing exceptions confirm generic response; log capture confirms no secrets.
- Acceptance Criteria: 404/500/CSRF responses are generic; logs contain no credential or token values.

### TASK-006 Account provisioning script
- Objective: Operator script to create pre-provisioned accounts with no hard-coded credentials.
- Requirement IDs: OQ-1, OQ-2 (8-char minimum), NFR-3.
- Architecture Component: C8 (A3).
- Design Review IDs: F-07 (A-07).
- Dependencies: TASK-003, TASK-004.
- Expected Changes: `scripts/provision_users.py`. Its test location is Not in the approved folder structure - needs human decision (Open Question 4).
- Security Considerations: password supplied at run time (mechanism TBD, Open Question 8), never stored in source, never echoed or logged; argon2 hash; minimum 8 characters enforced; duplicate email rejected.
- Validation: run against a temporary test database; verify hash stored, short password rejected.
- Acceptance Criteria: account with valid email and 8+ character password is created with an argon2 hash; shorter passwords rejected; no credentials in repository.

### TASK-007 Authentication and session service
- Objective: Verify credentials, enforce lockout (5 consecutive failures -> 15 minutes, auto-expiring, reset on success), same generic response for unknown email, wrong password and locked account, dummy hash check for unknown email.
- Requirement IDs: FR-001.1-4, OQ-1, OQ-2, NFR-1, NFR-4.
- Architecture Component: C3.
- Design Review IDs: F-04, F-05, F-06 (A-04, A-05, A-06).
- Dependencies: TASK-003, TASK-004.
- Expected Changes: `app/services/auth_service.py`; tests under `tests/services/`.
- Security Considerations: argon2-cffi; comparable timing for unknown email; counters reset on success; lock expires by time; no information that reveals account existence or lock status.
- Validation: unit tests for lockout thresholds (4 vs 5 failures), expiry at 15 minutes (time-controlled), reset on success, identical messages across three failure paths.
- Acceptance Criteria: valid credentials authenticate; invalid and locked responses indistinguishable; locked user can log in after expiry.

### TASK-008 Task service
- Objective: Create, list (newest first), update, complete (one-way), delete (hard), and search (title, case-insensitive, partial, wildcard-escaped, lower-cased comparison) all scoped by current user id.
- Requirement IDs: FR-002.2, FR-003.1-4, FR-004.1-4, FR-005.1-3, FR-006.1-3, FR-007.1-4, OQ-4..OQ-10, NFR-1.
- Architecture Component: C4.
- Design Review IDs: F-07, F-09 (A-07, A-09).
- Dependencies: TASK-003, TASK-004.
- Expected Changes: `app/services/task_service.py`; tests under `tests/services/`.
- Security Considerations: every query includes owner id; foreign or nonexistent id returns not-found identically; LIKE wildcards (`%`, `_`, escape char) escaped; parameterised queries only.
- Validation: unit/integration tests with two users: no cross-user list, search, update, complete, delete; search with `%`, `_`, uppercase, non-ASCII; completed task can be edited but not reopened; ordering; about 1000 tasks per user response check against 2 s target.
- Acceptance Criteria: all listed FR behaviours hold; foreign task operations return not-found; search never returns another user's tasks; behaviour when completing an already completed task: TBD (Open Question 3).

### TASK-009 Authentication routes and login page
- Objective: Login route(s), login template, redirect of unauthenticated requests to login, login error display.
- Requirement IDs: FR-001.1-4, NFR-4.
- Architecture Component: C2, C1, C3.
- Design Review IDs: F-02, F-08 (A-02, A-08).
- Dependencies: TASK-007, TASK-005, TASK-011 (base template) - may start when base template exists.
- Expected Changes: `app/routes/auth.py`; a login template under `app/templates/` (file name Not in the approved folder structure - needs human decision, Open Question 2); route paths TBD (Open Question 2); `tests/routes/`.
- Security Considerations: CSRF token on form; generic failure message; no credentials in logs or URLs; protected pages redirect when unauthenticated.
- Validation: route tests for success, invalid credentials, locked account, missing fields, unauthenticated access to every task route.
- Acceptance Criteria: FR-001.1-4 satisfied; failure message identical for all failure causes.

### TASK-010 Task routes
- Objective: HTTP handlers for list/empty state/search, create, edit, complete, delete (with confirmation step).
- Requirement IDs: FR-002 to FR-007, OQ-6, OQ-9.
- Architecture Component: C2 (calling C3, C4, C5, C6).
- Design Review IDs: F-02, F-08 (A-02, A-08).
- Dependencies: TASK-008, TASK-009 (login/session in place), TASK-011.
- Expected Changes: `app/routes/tasks.py`; `tests/routes/`. Route paths and template names: see Open Question 2.
- Security Considerations: login required on every route; CSRF on every state-changing request (create, update, complete, delete); use POST for state changes; foreign ids return not-found.
- Validation: route tests per user story, including negative cases (other user's id, missing CSRF token, missing title, over-length input).
- Acceptance Criteria: FR-002.3, FR-003.3-4, FR-004.3-4, FR-005.1-3, FR-006.1-3, FR-007.3-4 verified through the HTTP layer.

### TASK-011 Templates and static assets (UI)
- Objective: Server-rendered, responsive, accessible UI: base layout, login, task list with title and status, empty state, create/edit forms with validation messages, complete action, delete confirmation, search box and no-match message.
- Requirement IDs: FR-001.1/1.3, FR-002.1, FR-003.1-2/3.4, FR-004.1, FR-005.1/5.3, FR-006.1-2, FR-007.1-2/7.4, OQ-6, OQ-11.
- Architecture Component: C1.
- Design Review IDs: F-08, F-09 (A-08, A-09).
- Dependencies: TASK-002 (base layout may start then); page content completes with TASK-009 and TASK-010.
- Expected Changes: files within `app/templates/` and `app/static/` (individual file names not in approved structure, Open Question 2).
- Security Considerations: template auto-escaping on (no `|safe` of user content); CSRF token in every form; no secrets or user-sensitive data in client code; minimal JS.
- Validation: rendered-HTML tests (escaping of `<script>` in title/description), manual check of responsive layout and keyboard/label accessibility (WCAG 2.1 AA where practical).
- Acceptance Criteria: all screens above exist; user-supplied content rendered escaped; labels and focus order sensible; layout usable at narrow and desktop widths.

### TASK-012 Run helpers and README
- Objective: Entry point and local run helpers; setup and run instructions.
- Requirement IDs: NFR-3 (documented env setup); supports OQ-1 provisioning instructions.
- Architecture Component: C8, C2.
- Design Review IDs: F-10 (A-10).
- Dependencies: TASK-002, TASK-006, TASK-009, TASK-010.
- Expected Changes: `run.py`, `scripts/run_dev.py`, `README.md`.
- Security Considerations: README uses placeholders only; documents that HTTPS is required beyond local use; debug mode off by default (Proposal).
- Validation: fresh-environment walkthrough on Windows: install, copy `.env.example` to `.env`, provision account, start, log in.
- Acceptance Criteria: documented steps work on the local Windows machine; no real credentials in documentation.

### TASK-013 End-to-end security and acceptance validation
- Objective: Run the full suite and security/negative checks against all acceptance criteria.
- Requirement IDs: all FR, NFR-1..NFR-4, OQ-2, OQ-4..OQ-11.
- Architecture Component: all.
- Design Review IDs: F-02..F-07, F-13.
- Dependencies: TASK-001..TASK-012.
- Expected Changes: tests only under approved `tests/` paths; no new application paths.
- Security Considerations: verify CSRF, cookie flags, lockout, timing-equalised unknown email, ownership isolation, escaping, log hygiene, secret scan of repo.
- Validation: full pytest; manual walkthrough of every US; dependency check (pip audit or equivalent, tool TBD); secret grep.
- Acceptance Criteria: all section 16 requirements show passing validation; no open critical defects; response under 2 s for list/search with about 1000 tasks.

## 8. Task Dependencies

| Task | Depends on |
|------|-----------|
| TASK-001 | none |
| TASK-002 | TASK-001 |
| TASK-003 | TASK-002 |
| TASK-004 | TASK-001 |
| TASK-005 | TASK-002 |
| TASK-006 | TASK-003, TASK-004 |
| TASK-007 | TASK-003, TASK-004 |
| TASK-008 | TASK-003, TASK-004 |
| TASK-009 | TASK-007, TASK-005, base template from TASK-011 |
| TASK-010 | TASK-008, TASK-009, TASK-011 |
| TASK-011 | TASK-002 (full completion with TASK-009/010) |
| TASK-012 | TASK-002, TASK-006, TASK-009, TASK-010 |
| TASK-013 | TASK-001..TASK-012 |

## 9. Parallel Work and Blocked Tasks

Parallel after TASK-002: TASK-003, TASK-004, TASK-005, and base layout of TASK-011. After TASK-003 and TASK-004: TASK-006, TASK-007, TASK-008 in parallel.

Blocked tasks:
- TASK-002 blocked by TASK-001.
- TASK-003 and TASK-005 blocked by TASK-002.
- TASK-006, TASK-007, TASK-008 blocked by TASK-003 and TASK-004.
- TASK-009 blocked by TASK-007 (and TASK-005; base template from TASK-011).
- TASK-010 blocked by TASK-008 and TASK-009.
- TASK-012 blocked by TASK-006, TASK-009, TASK-010.
- TASK-013 blocked by all other tasks.
- Human-decision blockers: route paths and template/static file names (Open Question 2) block creation of those files in TASK-009/010/011 unless the human accepts the Proposal; test location for the provisioning script (Open Question 4) blocks its test only.

## 10. File/Directory Impact

All paths are from the approved structure (architecture section 9 with A-10); only the listed files change.

| Path | Tasks |
|------|-------|
| `app/__init__.py` | 002 |
| `app/models.py` | 003 |
| `app/validation.py` | 004 |
| `app/errors.py` | 005 |
| `app/services/auth_service.py` | 007 |
| `app/services/task_service.py` | 008 |
| `app/routes/auth.py` | 009 |
| `app/routes/tasks.py` | 010 |
| `app/templates/`, `app/static/` (file names TBD) | 009, 010, 011 |
| `scripts/provision_users.py` | 006 |
| `scripts/run_dev.py`, `run.py`, `README.md` | 012 |
| `requirements.txt`, `pytest.ini`, `.env.example`, `.gitignore` | 001, 002 |
| `tests/conftest.py`, `tests/test_validation.py`, `tests/test_errors.py`, `tests/test_models.py`, `tests/routes/`, `tests/services/` | 001 then per task |
| `instance/` (runtime, git-ignored) | 002 |
| Root docs (`requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`) | unchanged by Phase 5 |

Not changed: `docs/` (not used), `scripts/run_dev.sh` (replaced by `run_dev.py`), `.claude/`, `inputs/`, `skills/` (workflow files).

## 11. Security Plan

| Concern | Task | Source |
|---------|------|--------|
| Authentication, argon2 hashes, generic failures | 006, 007, 009 | OQ-1, FR-001.3, A-05, A-06 |
| Lockout 5 failures / 15 min auto-expiry | 007 | OQ-2, A-04 |
| Sliding 30-minute session timeout | 002 | OQ-2, A-06 |
| Cookie HttpOnly, SameSite=Lax, Secure on HTTPS | 002 | A-03 |
| CSRF on all state-changing requests | 002, 009, 010, 011 | A-02 |
| Per-user isolation; foreign tasks not found | 008, 010 | NFR-1, OQ-9 |
| Input validation | 004 | NFR-2, OQ-4 |
| Output escaping / injection / SQL | 003, 008, 011 | architecture section 8 |
| Secrets via environment, git-ignored, placeholders | 001, 002 | NFR-3 |
| Safe errors; logs exclude passwords, session and CSRF tokens | 005 | NFR-4, A-13 |
| Search wildcard escaping | 008 | A-07 |
| Dependency security | 013 | General; tool TBD |
| HTTPS | Not implemented (local only); documented in README | architecture section 11 item 6 |

No real credentials appear in this plan. Audit logging is out of scope.

## 12. Validation Strategy

Pytest with Flask test client (unit, integration, route tests) per task; negative and error-path tests for every security row above; time-controlled tests for timeout and lockout; two-user isolation tests; manual responsive/accessibility check; final end-to-end walkthrough (TASK-013). Tests are written in Phase 5, not Phase 4.

## 13. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-1 | Account lockout can be used to lock a known user (design review R-3) | 15-minute auto-expiry accepted |
| R-2 | No logout; sessions last up to 30 minutes of inactivity on shared machines (F-12) | Accepted by human |
| R-3 | SQLite case-insensitive matching is ASCII-only by default | Lower-cased comparison (A-07); test with non-ASCII |
| R-4 | Timing differences between unknown email and wrong password | Dummy hash check; timing test with tolerance |
| R-5 | Unpinned dependency versions cause drift | Pin in `requirements.txt` (Open Question 7) |
| R-6 | Unspecified route/file names cause rework | Resolve Open Question 2 before TASK-009 |
| R-7 | SQLite unsuitable if ever deployed on multiple instances (A1) | Out of scope; revisit if hosting changes |
| R-8 | Architecture amendments were not re-reviewed by the Design Review Agent | Human accepted; flag if conflicts appear during Phase 5 |

## 14. Assumptions

- AS-1 (Assumption) Development and running on the local Windows machine with Python 3 available; version Not specified in the approved project artifacts.
- AS-2 (Assumption) Tables are created by the application/ORM at startup or by a script; no migration tool (Open Question 5).
- AS-3 (Assumption) Lockout and timeout values are code defaults, not environment settings (Open Question 9).
- AS-4 Carried from architecture: A1 single server and store; A2 HTTPS outside local development; A3 accounts created by operator script.

## 15. Open Questions (resolved by human-approved defaults)

Resolutions: (1) Confirmed: architecture sections 11-12 are authoritative. (2) Implementer chooses conventional route and file names inside the approved directories and documents them in README. (3) Completing an already completed task is a no-op with an informational message, and the action is hidden in the UI for completed tasks. (4) Provisioning-script tests go in `tests/scripts/`. (5) `create_all` table creation, no migration tool. (6) Empty directories get a `.gitkeep`. (7) Pin dependencies to the versions installed at implementation time in `requirements.txt`. (8) Operator supplies the password through a hidden interactive prompt (`getpass`), never an argument or a hard-coded value. (9) Lockout threshold/duration and session timeout are code constants in one config module. (10) Use `pip-audit` for the dependency vulnerability check, if it can be installed locally; otherwise report it as skipped.

Original questions:

1. The architecture sections 7-9 still contain stale labels and tree entries (`docs/`, `run_dev.sh`, "Proposed"). This plan applies sections 11 and 12 as authoritative. Confirm.
2. Route URL paths and the names of files inside `app/templates/` and `app/static/` are not in the approved folder structure or artifacts. Approve a Proposal (planner will supply names for approval) or allow the implementer to choose names inside those directories?
3. Behaviour when a user completes an already completed task (error, no-op, or hidden action in UI)? Not specified in the approved project artifacts.
4. Where should tests for `scripts/provision_users.py` live? `tests/scripts/` is Not in the approved folder structure - needs human decision.
5. Schema details (column types, lengths, table-creation method, whether a migration tool is wanted): not specified beyond the minimal model. Accept `create_all`-style creation without migrations?
6. How should empty directories (`app/templates/`, `app/static/`, `tests/routes/`, `tests/services/`) be preserved, if at all? Not specified; no commits are made in this workflow.
7. Python version and dependency version pins: not specified. Pin to the versions installed at Phase 5 time?
8. How does the operator supply the password to `scripts/provision_users.py` (interactive hidden prompt, environment variable, or other)? Not specified.
9. Should the lockout threshold/duration and session timeout be code constants or environment-configurable?
10. Which dependency-vulnerability check tool, if any, should be used in TASK-013? Not specified.

## 16. Requirements Traceability

| Requirement | Component | Tasks | Validation |
|-------------|-----------|-------|-----------|
| FR-001.1-1.3 | C1, C3, C5, C6 | 004, 007, 009, 011 | login route tests |
| FR-001.4 | C2, C3 | 002, 009, 010 | unauthenticated access tests |
| FR-002.1-2.3 | C1, C4, C5, C7 | 003, 004, 008, 010, 011 | create tests |
| FR-003.1-3.4 | C1, C4, C7 | 008, 010, 011 | list/isolation/empty-state tests |
| FR-004.1-4.4 | C1, C4, C5, C7 | 004, 008, 010, 011 | update and ownership tests |
| FR-005.1-5.3 | C1, C4, C7 | 008, 010, 011 | complete tests, no reopen |
| FR-006.1-6.3 | C1, C4, C7 | 008, 010, 011 | delete, confirmation, ownership tests |
| FR-007.1-7.4 | C1, C4, C7 | 008, 010, 011 | search tests, wildcard, non-ASCII |
| NFR-1 | C3, C4, C7 | 002, 007, 008 | isolation, cookie tests |
| NFR-2 | C5 | 004 | boundary tests |
| NFR-3 | C8 | 001, 002, 006, 012 | secret scan, startup test |
| NFR-4 | C6 | 005 | generic-error and log tests |
| OQ-1, OQ-2 | C3, C7, C8 | 003, 006, 007, 002 | provisioning, lockout, timeout tests |
| OQ-3, OQ-12 | none (out of scope) | none | n/a |
| OQ-4..OQ-10 | C4, C5, C7 | 003, 004, 008 | rules tests |
| OQ-11 | C1, C7 | 003, 011, 013 | indexes, responsive, 2 s check |
| OQ-13 | none (waived) | none | n/a |

## 17. Design Review Traceability

| Finding | Addressed in tasks | Note |
|---------|-------------------|------|
| F-01 status labels | plan section 2 | Architecture 11/12 treated as authoritative |
| F-02 CSRF | 002, 009, 010, 011, 013 | Flask-WTF |
| F-03 cookie attributes, SECRET_KEY, HTTPS | 002, 012 | HTTPS documented only |
| F-04 lockout | 007 | 5 failures / 15 min |
| F-05 unknown email | 007 | dummy hash |
| F-06 argon2, Flask-Login, sliding expiry | 002, 006, 007 | |
| F-07 password minimum, wildcard escaping, data model | 003, 006, 008 | |
| F-08 server-side rendering, unauthenticated/error branches | 009, 010, 011, 005 | |
| F-09 traceability | section 16 | |
| F-10 entry point, instance/, conftest, cross-platform helper | 001, 012 | |
| F-11 docs location, workflow dirs | 001 | docs stay at root |
| F-12 no logout | none | Accepted risk |
| F-13 log hygiene | 005, 013 | |

Unresolved critical issues from the design review: none.

## 18. Phase 5 Readiness

Ready. The human approved this plan and the open questions were resolved by default (section 15). Phase 5 (implementation) is complete.

The Phase 4 implementation plan has been created. Please review the tasks, dependencies, implementation order, security considerations, risks, and acceptance criteria. Do you approve the plan or would you like changes?
