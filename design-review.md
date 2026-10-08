# Design Review

**Status: APPROVED by the human ("approved use defaults", given directly to the main session; status and decisions recorded there because the Design Review Agent could not verify a relayed approval).** Section 8 changes were applied to `architecture.md` (its sections 11 and 12). Not published to Confluence or Jira (waived). Local machine only.

## 1. Summary and Overall Result

**Overall result: READY WITH MINOR CHANGES**

The architecture covers all functional requirements (FR-001 to FR-007) and all four NFRs, and it adds no unsupported capabilities. Components, data flow, security approach and folder structure are coherent and fit the approved requirements. Nothing found is a blocker. The result is conditional on:

1. Resolving the carried-forward open items (hosting, lockout duration, HTTPS/CSRF, `docs/` move, Confluence waiver). Two of them (lockout duration, CSRF/HTTPS) affect implementation and should be decided before Phase 4.
2. Fixing a small set of consistency and precision gaps in `architecture.md` (section 8 of this review).

Counts: 0 Critical, 0 High, 4 Medium, 9 Low/Info.

## 2. Artifacts Reviewed

| Artifact | State | Notes |
|----------|-------|-------|
| `C:\Users\GirmajiSaisree\Documents\Claude\requirements.md` | APPROVED (relayed to main session) | Defaults OQ-1 to OQ-13 in its section 7. |
| `C:\Users\GirmajiSaisree\Documents\Claude\architecture.md` | Header says APPROVED; open items in section 11 | Both diagrams (Mermaid) are embedded and were reviewed. No separate diagram file exists. |
| `C:\Users\GirmajiSaisree\Documents\Claude\skills\project-folder-structure\SKILL.md` | Reference | Used for the folder structure check. |

Note: this agent cannot independently verify the human approvals recorded in the headers; they are taken as stated.

## 3. Findings

| ID | Severity | Area | Description | Recommendation |
|----|----------|------|-------------|----------------|
| F-01 | Medium | Consistency / governance | The header of `architecture.md` says the stack, folder structure and session-cookie authentication are approved, but sections 7 ("all Proposed; require explicit human approval"), the Status column (e.g. "Proposed; mechanism TBD until approved") and section 11 items 1-3 still read as pending. | Architecture Agent to update status labels and section 11 so approved items are marked Approved and only items 4-8 remain open. |
| F-02 | Medium | Security | CSRF protection is only "should ... Proposed" (section 8) and no CSRF mechanism (for example Flask-WTF or equivalent) appears in the technology table. The design uses cookie-based sessions with state-changing POST actions, so CSRF is a real risk. | Make CSRF protection a firm design requirement and name the mechanism in section 7. Needs human confirmation (open item 6). |
| F-03 | Medium | Security | HTTPS is "Assumption / TBD" and hosting is TBD. Session cookies and passwords would travel in clear text over plain HTTP. Session cookie attributes (HttpOnly, Secure, SameSite) and session-signing secret (SECRET_KEY) handling are not stated. | State HTTPS as required for any non-local deployment, and list cookie attributes and the signing key as a secret under C8. Hosting decision remains with the human. |
| F-04 | Medium | Requirements coverage | Lockout "temporary, duration TBD" (OQ-2). The design stores lockout state in C7 but cannot define behaviour (duration, reset on success, counter scope, locked-account message) without this value. Lockout on pre-provisioned accounts is also a denial-of-service lever against a known email. | Human to decide the duration (open item 5). Architecture to state whether the lockout is time-based and auto-expiring, and that the locked and invalid-credential messages are not distinguishable in a way that reveals account existence. |
| F-05 | Low | Security | Login behaviour for unknown emails is not stated. Lockout counters, response timing and messages can leak whether an email exists. | Add a note that unknown-email and wrong-password paths return the same generic message and comparable timing. |
| F-06 | Low | Technology | "argon2 or bcrypt" and "Flask-Login or equivalent" leave the choice open. The 30 minute inactivity timeout with a signed cookie requires the expiry to be refreshed on each request, which is not described. | Pick one hashing library and one session approach; describe sliding expiry on each authenticated request. |
| F-07 | Low | Data / design | The 8 character minimum password (OQ-2) has no enforcing component: accounts are created only by `scripts/provision_users.py`. Search needs LIKE wildcard escaping, and SQLite case-insensitive matching is ASCII-only by default. Task data model (fields, owner foreign key, indexes on owner and title) is not defined, relevant to the under-2-second target at about 1000 tasks. | State that provisioning enforces the password minimum, that search escapes wildcards, and outline the minimal data model. Detailed schema can wait for implementation planning. |
| F-08 | Low | Diagram / consistency | The component diagram places C1 in the browser, while section 9 puts C1 (templates and static) in the server `app/` package (server-rendered). Acceptable, but undocumented. The sequence diagram omits the unauthenticated path (redirect to login, FR-001.4) and the C6 error path. | Add a note that C1 is rendered server-side and executed in the browser; add the unauthenticated and error branches to the sequence diagram. |
| F-09 | Low | Traceability | The traceability line maps NFR-1 only to C3 and C4 (C7 and transport are omitted). OQ-11 (performance, accessibility, responsiveness) and OQ-3 are not mapped to any component. FR-001.2 and FR-001.4 are mapped to C3 only in the line below the table, not in the C1/C2 rows. | Extend the traceability line to include C7, transport, and the OQ-11 drivers. |
| F-10 | Low | Folder structure | `scripts/run_dev.sh` is a shell script but the working environment is Windows. No application entry point (for example `wsgi.py` or `run.py`) and no designated location for the SQLite database file (for example `instance/`) are listed. No `tests/conftest.py` for shared fixtures. | Provide a cross-platform run helper (or document both), list an entry point, the database location and `conftest.py`. |
| F-11 | Low | Folder structure | `docs/` is in the proposed tree, but `requirements.md`, `architecture.md` (and this file) are at the repository root. Non-project items (`.claude/`, `inputs/`, `skills/`) also exist at the root and are not in the tree. | Human to confirm the move (open item 7) and whether `inputs/` and `skills/` belong in the repository or are git-ignored. |
| F-12 | Info | Requirements observation | Logout is out of scope while sessions last 30 minutes of inactivity. On shared computers a session cannot be ended manually. This is an approved scope decision, noted as a residual risk, not an architecture defect. | None required; human may revisit OQ-3. |
| F-13 | Info | Security | Audit logging is out of scope; failed-login events are not logged for monitoring. Server log must not include passwords or session tokens (stated only partly). | Optionally log failed attempts without credentials; state that logs exclude secrets. |

## 4. Risks and Gaps

- R-1 Session hijack or credential sniffing if deployed over HTTP (F-03).
- R-2 CSRF on cookie-authenticated task actions if protection is not mandated (F-02).
- R-3 Account lockout can be used to lock out a known user; duration undefined (F-04).
- R-4 No hosting target: deployment assumptions (HTTPS, secrets provisioning, SQLite on shared storage) cannot be validated. SQLite also suits only a single server (A1) and would need revisiting if hosting implies multiple instances.
- R-5 Open tool and library choices (F-06) may cause rework if not fixed before planning.
- R-6 No stated availability, backup or retention targets (consistent with the requirements; none invented).
- Gap: no component owns session cookie configuration explicitly (C3 or C8).

## 5. Security and Consistency Checks

| Check | Result |
|-------|--------|
| Authentication (hashed passwords, generic failures) | Pass; details in F-05, F-06 |
| Authorization / per-user isolation, foreign task returns not found | Pass (C4 filters by user id; OQ-9) |
| Input validation (server-side, title and description limits) | Pass (C5) |
| Secrets (env based, git-ignored, sample file) | Pass; add session signing key (F-03) |
| Error handling (generic messages, details in server log) | Pass (C6) |
| Output escaping / injection | Pass in intent (templates auto-escape, parameterised access) |
| CSRF | Gap (F-02) |
| Transport security | Gap (F-03) |
| Brute force | Partial (F-04) |
| Requirements coverage FR-001 to FR-007, NFR-1 to NFR-4 | Pass; every FR maps to at least one component |
| Unsupported assumptions | A1 to A3 are listed and reasonable; HTTPS (A2) unconfirmed |
| Technology choices approved | Stated approved in header; internal labels stale (F-01) |
| Diagram and document consistency | Mostly consistent; see F-08 |
| External dependencies | None required; consistent with the requirements |

## 6. Folder Structure Review

Reference: `project-folder-structure` skill, Python (Flask) layout.

| Rule | Result |
|------|--------|
| Layout conventional for approved stack | Pass |
| Source (`app/`) and tests (`tests/`) separate; tests mirror source | Pass |
| Dependency and config files at root (`requirements.txt`, `pytest.ini`) | Pass |
| Scripts in `scripts/`; docs in `docs/` with README at root | Pass in tree; actual files not yet moved (F-11) |
| Secrets excluded; `.env.example` provided; `.gitignore` lists `.env`, database, venv, caches | Pass |
| One-line purpose for each directory and key file | Pass |
| Every component maps to a module | Pass: C1 templates/static, C2 `__init__.py` and `routes/`, C3 `auth_service.py`, C4 `task_service.py`, C5 `validation.py`, C6 `errors.py`, C7 `models.py`, C8 `.env.example`, `scripts/provision_users.py` and config loading in `__init__.py` |

Differences between the approved tree and the actual directory (the project skeleton does not exist yet):
- Missing from disk: everything in the proposed tree except the existing root documents.
- Present on disk but not in the tree: `.claude/`, `inputs/`, `skills/`.
- Files in the wrong location versus the target: `requirements.md`, `architecture.md` (root, target `docs/`).
- Suggested additions: entry point, database location, `tests/conftest.py`, cross-platform run helper (F-10). C7 combining models and data access in one file is acceptable for this size.

These differences are reported, not resolved.

## 7. Agreed Design Decisions

Human approved the findings and section 8 changes and delegated open questions to defaults:

1. Hosting: local machine only; no remote URLs (OQ 1 resolved).
2. Lockout: 15 minutes, auto-expiring (OQ 2).
3. CSRF mandatory; HTTPS moot for local only, required if ever deployed beyond local (OQ 3).
4. Documents stay at the repository root (OQ 4).
5. Confluence waived; nothing published (OQ 5).
6. Hashing library: argon2 (OQ 6).
7. `.claude/`, `inputs/`, `skills/` are not part of the application tree; nothing is committed in this workflow (OQ 7).
8. Logout stays out of scope; residual risk accepted (OQ 8, F-12).
9. Findings and section 8 changes accepted and applied (OQ 9).
Stack, folder structure (with additions in architecture.md A-10) and session-cookie authentication remain approved.

## 8. Required Changes to architecture.md

To be sent to the Architecture Agent only after the human agrees. This agent did not edit `architecture.md`.

1. (F-01) Update status labels in section 7 and section 11 to match the approved header.
2. (F-02) Make CSRF protection mandatory and name the mechanism in section 7.
3. (F-03) Require HTTPS for non-local use; add session cookie attributes and the signing key to C3/C8 and the secrets row.
4. (F-04) Record lockout duration once decided; describe auto-expiry and indistinguishable messages.
5. (F-05) Add the unknown-email handling note.
6. (F-06) Select the hashing library and session library; describe sliding inactivity expiry.
7. (F-07) Note password minimum enforcement at provisioning, search wildcard escaping, and a minimal data model with indexes.
8. (F-08) Add the server-side rendering note and the unauthenticated and error branches to the sequence diagram.
9. (F-09) Extend traceability (NFR-1 to C7 and transport; OQ-11 and OQ-3 drivers).
10. (F-10, F-11) Update the folder structure with entry point, database location, `conftest.py`, cross-platform run helper, and the outcome of the `docs/` move and the root-level extra directories.
11. (F-13) State that logs exclude credentials and tokens.

After the update, this review must be refreshed.

## 9. Open Questions

1. Hosting and deployment target: what is it (local only, internal server, cloud)?
2. Lockout duration after 5 failed attempts (for example 15 minutes)?
3. Confirm HTTPS is required for every non-local deployment (A2), and confirm that CSRF protection is mandatory.
4. Move `requirements.md`, `architecture.md` and `design-review.md` into `docs/`, or keep them at the root?
5. Confirm the Confluence waiver applies to this phase (nothing is published).
6. Which hashing library: argon2 or bcrypt?
7. Should `inputs/`, `skills/` and `.claude/` be committed or git-ignored?
8. Does the human want to revisit the scope decision that logout is out of scope (F-12), or accept the residual risk?
9. Does the human accept the findings and the list of required changes in section 8, and authorise sending them to the Architecture Agent?

## 10. Human Approval

- [x] Human has reviewed this design review.
- [x] Human approves the findings and required changes (section 8), applied in `architecture.md` sections 11-12.
- [x] Human approves proceeding to Phase 4 (Implementation Planning).

Status: **APPROVED.** The architecture amendments were not re-reviewed by the Design Review Agent; they were applied directly from section 8.
