# Functional Requirements Document: Online Task Management

Derived from the approved `requirements.md` (source: `inputs/sample-user-stories.docx`). No requirements are added here. Verification status is taken from `validation-report.md` (PASS WITH LIMITATIONS, approved by the human).

## 1. Purpose
A simple web-based task management application where users can create, view, update, complete and delete their own tasks.

## 2. Scope
In scope: login, create, view, update, complete, delete and search of the user's own tasks.
Out of scope (confirmed, OQ-12): user registration, password reset, logout, task sharing, due dates, priorities, categories, administrator functions.

## 3. Actors
- Authenticated user (task owner).
- Unauthenticated visitor (can only log in).
- Other actors (for example administrators): none identified in the source.

## 4. Functional Requirements and Expected Behavior

| Story | ID | Requirement | Validation result |
|-------|----|-------------|-------------------|
| US-001 Login | FR-001.1 | User can enter email and password | PASS |
| | FR-001.2 | Valid credentials grant access | PASS |
| | FR-001.3 | Invalid credentials show an appropriate error (always "Invalid email or password.") | PASS |
| | FR-001.4 | Unauthenticated users cannot access protected task pages | PASS |
| US-002 Create | FR-002.1 | Create a task with a title and optional description | PASS |
| | FR-002.2 | Valid task is saved and associated with the logged-in user | PASS |
| | FR-002.3 | Missing title shows a required-field validation error | PASS |
| US-003 View | FR-003.1 | User sees a list of their own tasks | PASS |
| | FR-003.2 | Each task shows title and completion status | PASS |
| | FR-003.3 | User cannot view other users' tasks | PASS |
| | FR-003.4 | Empty state shown when no tasks | PASS |
| US-004 Update | FR-004.1 | Edit title and description | PASS |
| | FR-004.2 | Changes are persisted | PASS |
| | FR-004.3 | Cannot update other users' tasks | PASS |
| | FR-004.4 | Required fields validated | PASS |
| US-005 Complete | FR-005.1 | Mark an active task completed | PASS |
| | FR-005.2 | Completion persisted | PASS |
| | FR-005.3 | Completed status visible in the list | PASS |
| US-006 Delete | FR-006.1 | Delete own task | PASS |
| | FR-006.2 | Deleted task no longer listed | PASS |
| | FR-006.3 | Cannot delete other users' tasks | PASS |
| US-007 Search | FR-007.1 | Search own tasks by title | PASS |
| | FR-007.2 | Matching tasks displayed | PASS |
| | FR-007.3 | Search limited to own tasks | PASS |
| | FR-007.4 | Message shown when nothing matches | PASS |

## 5. Non-Functional Requirements
- NFR-1 Task data protected from unauthorized access (PASS).
- NFR-2 User input validated (PASS).
- NFR-3 No hard-coded secrets or credentials (PASS).
- NFR-4 Clear error messages that expose no sensitive implementation details (PASS).

## 6. Resolved Assumptions (industry-standard defaults chosen by the human; owner may revise)
- OQ-1 Accounts are pre-provisioned; passwords stored only as salted hashes (implemented with argon2).
- OQ-2 Password minimum 8 characters; lockout after 5 failed attempts (15 minutes, auto-expiring per architecture A-04); session expires after 30 minutes of inactivity.
- OQ-3 Logout, password reset, "remember me" out of scope.
- OQ-4 Title required, trimmed, whitespace-only rejected, max 100 characters; description optional, max 1000; duplicate titles allowed.
- OQ-5 Completion is one-way; completed tasks may still be edited.
- OQ-6 Hard delete with a confirmation step.
- OQ-7 Search is case-insensitive, partial match, title only, no status filter.
- OQ-8 Newest first; no pagination; up to about 1000 tasks per user.
- OQ-9 Another user's task is reported as "not found".
- OQ-10 Created/updated timestamps stored; displaying them is optional.
- OQ-11 Evergreen desktop browsers; responsive layout; baseline accessibility (WCAG 2.1 AA where practical); interactive operations under 2 seconds. Validation result: PARTIAL (not checked in a browser; see limitations).
- OQ-12 Out-of-scope list confirmed. OQ-13 Jira waived.

## 7. Dependencies and Constraints
- User accounts must be provisioned by an operator (`scripts/provision_users.py`).
- No external services are required. Hosting is local machine only; HTTPS is not set up and would be required if served beyond the local machine.

## 8. Known Limitations (from `validation-report.md`)
Responsive layout and accessibility not verified in a browser (L-1); interactive provisioning prompt not verified live (L-2); timing-equalisation test is loose (L-3); Code Review waived (L-4).
