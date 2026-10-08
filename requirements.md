# Requirements Specification: Online Task Management

**Status: APPROVED by the human (approval given directly to the main session; finalized there because the Requirements Analyst agent could not verify a relayed approval)**
**Source:** inputs/sample-user-stories.docx
**Jira:** waived by the human; no Jira or Confluence items created.

## 1. Business Objective
A simple web-based task management application where users can create, view, update, complete and delete their own tasks.

## 2. Actors
- Primary: authenticated user (task owner).
- Unauthenticated visitor (can only log in).
- Other actors/stakeholders (e.g. administrators): not identified in source (see OQ-1).

## 3. Scope
In scope: login, create, view, update, complete, delete, search of own tasks.
Out of scope (confirmed, OQ-12): user registration, password reset, logout, task sharing, due dates, priorities, categories, administrator functions.

## 4. Functional Requirements

### Epic: Online Task Management

### US-001 User Login
As a user, I want to log in with email and password so that I can access my tasks.
- FR-001.1 User can enter email and password.
- FR-001.2 Valid credentials grant access.
- FR-001.3 Invalid credentials show an appropriate error message.
- FR-001.4 Unauthenticated users cannot access protected task pages.

Acceptance criteria: as listed in FR-001.1 to FR-001.4.

### US-002 Create Task
- FR-002.1 User can create a task with a title and an optional description.
- FR-002.2 A valid task is saved and associated with the logged-in user.
- FR-002.3 If the title is missing, a required-field validation error is shown.

### US-003 View My Tasks
- FR-003.1 User sees a list of their own tasks.
- FR-003.2 Each task shows its title and completion status.
- FR-003.3 User cannot view other users' tasks.
- FR-003.4 An empty state is shown when the user has no tasks.

### US-004 Update Task
- FR-004.1 User can edit the title and description of a task.
- FR-004.2 Changes are persisted.
- FR-004.3 User cannot update other users' tasks.
- FR-004.4 Required fields are validated.

### US-005 Complete Task
- FR-005.1 User can mark an active task as completed.
- FR-005.2 Completion is persisted.
- FR-005.3 Completed status is visible when tasks are viewed.

### US-006 Delete Task
- FR-006.1 User can delete their own task.
- FR-006.2 A deleted task no longer appears in the list.
- FR-006.3 User cannot delete other users' tasks.

### US-007 Task Search
- FR-007.1 User can search their own tasks by title.
- FR-007.2 Matching tasks are displayed.
- FR-007.3 Search is limited to the user's own tasks.
- FR-007.4 A message is shown when no tasks match.

## 5. Non-Functional Requirements (from source)
- NFR-1 Authenticated task data must be protected from unauthorized access.
- NFR-2 User input must be validated.
- NFR-3 No hard-coded secrets or credentials.
- NFR-4 Error messages must be clear and must not expose sensitive implementation details.

No performance, availability, browser support, accessibility or data retention requirements are stated in the source.

## 6. Dependencies, Assumptions, Constraints
- Assumptions are the industry-standard defaults listed in section 7, chosen on the human's instruction ("use the default standards").
- Dependency: user accounts are pre-provisioned (see OQ-1).

## 7. Resolved Questions / Assumptions
The human delegated OQ-1 to OQ-12 to industry-standard defaults. Owner: human/product owner (may revise). Affected phases: Requirements, Architecture, Implementation, Testing.

| ID | Resolution (assumed default) | Status |
|----|------------------------------|--------|
| OQ-1 | Accounts are pre-provisioned; no self-registration. Passwords stored only as salted hashes (e.g. bcrypt/argon2). | Resolved (default) |
| OQ-2 | Minimum 8-character passwords; temporary lockout after 5 failed attempts; session expires after 30 minutes of inactivity. | Resolved (default) |
| OQ-3 | Logout, password reset and "remember me" are out of scope. | Resolved (default) |
| OQ-4 | Title required, trimmed, whitespace-only rejected, max 100 chars; description optional, max 1000 chars; duplicate titles allowed. | Resolved (default) |
| OQ-5 | Completion is one-way per the source; completed tasks cannot be reopened. Completed tasks may still be edited. | Resolved (default) |
| OQ-6 | Hard (permanent) delete, with a confirmation step in the UI. | Resolved (default) |
| OQ-7 | Search is case-insensitive, partial match, on title only; no status filter. | Resolved (default) |
| OQ-8 | List ordered newest first; no pagination required; up to about 1000 tasks per user. | Resolved (default) |
| OQ-9 | Access to another user's task returns "not found" (does not reveal existence). | Resolved (default) |
| OQ-10 | Created and updated timestamps are stored; displaying them is optional. | Resolved (default) |
| OQ-11 | Modern evergreen desktop browsers; responsive layout; baseline accessibility (WCAG 2.1 AA where practical); interactive operations under 2 seconds; no formal availability or retention target. | Resolved (default) |
| OQ-12 | Out-of-scope list in section 3 confirmed as drafted. | Resolved (confirmed) |
| OQ-13 | Jira waived by the human. No Jira or Confluence items are created. | Resolved (waived) |

## 8. Jira
Waived by the human. Nothing created.
