---
description: "Audit tasks.md to verify every AC-N in spec.md has a T00x [P] test task. QA gate before /speckit.implement."
---

# Test Task Audit — QA Gate Before Implementation

Audit `tasks.md` against `spec.md` Acceptance Criteria before `/speckit.implement` runs.
This is the **QA gate at Step 3** of the team's SDD process.

The command verifies:
1. Every `AC-N` in spec.md has at least one `T00x [P]` test task in tasks.md
2. Each test task is specific (not a stub or placeholder)
3. Each test task carries an automation tag: `[MANUAL]`, `[AUTO]`, or `[BOTH]`
4. No test task uses forbidden patterns that indicate stubs

It is **non-destructive** — it never modifies any files.
It outputs a pass/fail gate report suitable for copy-paste into a PR comment.

## User Input

```text
$ARGUMENTS
```

Consider user input before proceeding. The user may specify:
- `--strict` — fail on any missing automation tag (default: warn)
- `--ac AC-2` — audit only a specific AC
- `--fix-suggestions` — include suggested task text for each gap found

## Prerequisites

1. Confirm you are inside a git repository.
2. Locate `specs/NNN-*/spec.md`. If multiple feature folders exist, ask the user which one.
3. Read `spec.md` fully. Extract every `AC-N:` line from `## Acceptance Criteria`.
4. Read `tasks.md` fully. Extract every task line.
5. Read `.specify/memory/constitution.md` — confirm the QA non-negotiables are present.

## Outline

### Step 1 — Extract AC Inventory from spec.md

Parse `## Acceptance Criteria`. Build a list:

```
AC-1: Multi-select — agent can select multiple star ratings simultaneously
AC-2: Filter persists across pagination
AC-3: Result count updates to reflect filtered set
AC-4: Accessible via keyboard, ARIA labels present
```

Total ACs: 4

### Step 2 — Extract Test Task Inventory from tasks.md

Find all tasks marked `[P]` (pre-implementation / test tasks). A valid test task line looks like:

```
T001 [P] Add StarRatingFilter unit test (AC-1)
T002 [P] Add pagination persistence integration test (AC-2) [AUTO]
T003 [P] Add result count unit test (AC-3) [AUTO]
T004 [P] Add keyboard accessibility E2E test (AC-4) [BOTH]
```

Also detect **stub-test tasks** — tasks whose description suggests empty or placeholder tests:
- Text contains: "placeholder", "stub", "TODO", "add test" with no AC reference
- Text matches: `T00x [P] Add tests` with nothing more specific

### Step 3 — Map ACs to Test Tasks

For each AC-N, determine:

| Check | Result |
|-------|--------|
| At least one `T00x [P]` task references this AC | ✅ / ❌ |
| Test task description is specific (names the behaviour being tested) | ✅ / ⚠️ |
| Test task carries `[MANUAL]`, `[AUTO]`, or `[BOTH]` tag | ✅ / ⚠️ |
| No test task for this AC is a stub | ✅ / ❌ |

### Step 4 — Generate Audit Report

**Full pass example:**
```markdown
## Test Task Audit — PASSED ✅

Feature: specs/001-connect-hotel-filter/
Spec ACs: 4 | Test tasks found: 5 | Gaps: 0 | Stubs: 0

| AC | Test Task(s) | Automation Tag | Status |
|----|-------------|----------------|--------|
| AC-1 | T001 [P] Add StarRatingFilter unit test (AC-1) | [AUTO] | ✅ |
| AC-2 | T002 [P] Add pagination persistence test (AC-2) | [AUTO] | ✅ |
| AC-3 | T003 [P] Add result count unit test (AC-3) | [AUTO] | ✅ |
| AC-4 | T004 [P] Add keyboard a11y E2E test (AC-4) | [BOTH] | ✅ |

All ACs have specific, tagged test tasks. Safe to run /speckit.implement.
```

**Failure example:**
```markdown
## Test Task Audit — FAILED ❌

Feature: specs/001-connect-hotel-filter/
Spec ACs: 4 | Test tasks found: 2 | Gaps: 2 | Stubs: 1

### ❌ Blockers — Must Fix Before /speckit.implement

| AC | Issue | Suggested Fix |
|----|-------|---------------|
| AC-2 | No test task found | Add: `T005 [P] Add pagination persistence integration test (AC-2) [AUTO]` |
| AC-4 | No test task found | Add: `T006 [P] Add keyboard + ARIA accessibility test (AC-4) [BOTH]` |

### ⚠️ Warnings — Should Fix

| Task | Issue |
|------|-------|
| T003 [P] Add tests | Stub task — description does not reference an AC or specific behaviour |
| T001 [P] Add StarRatingFilter unit test (AC-1) | Missing automation tag — add [AUTO], [MANUAL], or [BOTH] |

### How to Fix
1. Edit tasks.md in place — add the missing test tasks above.
2. Do NOT re-run /speckit.tasks (it regenerates from scratch).
3. Re-run /speckit.test.tasksaudit to confirm.

Gate: BLOCKED. /speckit.implement should not run until blockers are resolved.
```

### Step 5 — CI-Friendly One-Line Summary

Always output a final line suitable for CI output or PR comment:

```
SPECTEST AUDIT: 2 blockers (AC-2 no test task, AC-4 no test task), 2 warnings — FAIL
```
or
```
SPECTEST AUDIT: 4 ACs, 4 test tasks, 0 gaps, 0 stubs — PASS
```

## Rules

- **Read-only** — never modify spec.md, tasks.md, or any other file
- **Blocker vs Warning distinction**: Missing AC→test-task mapping = BLOCKER (fails the gate). Missing automation tag or vague description = WARNING (audit continues)
- **Stub detection is strict**: a test task whose description is `"Add tests"`, `"Write tests"`, `"Add placeholder test"`, or has no AC reference is a blocker
- **Constitution enforcement**: if `constitution.md` does not contain the QA non-negotiables, warn the user to add them before the next repo SDD onboarding
- **No false passes**: an AC with only a stub test task is treated the same as an AC with no test task — both are blockers
- **Suggest, not prescribe**: when suggesting task text, use the actual AC wording and the appropriate test type (unit/integration/E2E/BOTH) based on what the AC describes
- **Accessibility ACs**: any AC containing "keyboard", "ARIA", or "accessible" must have a test task tagged `[BOTH]` (automated axe-core + manual keyboard flow)
