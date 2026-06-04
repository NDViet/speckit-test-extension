---
description: "Find spec.md testable items (Acceptance Scenarios, FR-###, SC-###) with no matching test task or test file. Severity-classified, phase-aware, CI-friendly. Read-only."
argument-hint: "[--critical-only] [--tasks-only|--files-only] [--story US1] [--json]"
---

# Find Untested Specification Items

**QA lane — run by the QA engineer on the opened PR** (after `/speckit-implement`), as the
fourth QA step: `test-plan → test-generate → test-coverage → test-gaps → test-review`.

Scan for testable items in `spec.md` that have no matching test task in `tasks.md` **and/or**
no matching test file in the codebase. Built for:

- PR inspection after implementation
- Pre-merge spot-check
- A CI gap gate

**Read-only** — never creates or modifies files.

## User Input

```text
$ARGUMENTS
```

The user may specify:
- `--critical-only` — report only Critical gaps
- `--tasks-only` / `--files-only` — restrict to task gaps or file gaps
- `--story US1` — limit to one user story
- `--json` / `--checklist` — output format

## Prerequisites

1. Resolve the feature directory:
   `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`
   Parse `FEATURE_DIR`. Fall back to `specs/*/spec.md` if unavailable.
2. Read `FEATURE_DIR/spec.md` — extract the testable-item inventory and `## Assumptions`
   (out-of-scope statements live here, not under a `## Out of scope` heading).
3. Read `FEATURE_DIR/tasks.md` — extract test tasks (by Tests subsection / test path, **not** by `[P]`),
   their `[US#]` labels, and which phases/stories are marked complete (`[X]`).
4. Read `FEATURE_DIR/plan.md` and `.specify/memory/constitution.md` — risk and priority signals.
5. Locate and parse test files for item IDs (`US{n}-AS{m}`, `FR-###`, `SC-###`) and keywords.

## Outline

### Step 1 — Build the Gap List

For each testable item:

- **Gap A — No test task**: the item exists in spec.md but no test task in tasks.md covers it.
- **Gap B — Test task, no test file**: a test task exists but its test file has not been created.
- **Gap C — Stub test file**: a test file exists but its bodies are all stubs (`.skip`, `.todo`,
  `throw new Error('TODO')`, `raise NotImplementedError`, `expect(true).toBe(true)`, empty).
- **Gap D — Weak traceability**: a real test exists but cites no item ID in its label — confidence Medium/Weak.

If both A and B apply to one item, report them together (`A + B`) on a single row.

### Step 2 — Classify Severity

| Severity | Definition |
|----------|-----------|
| 🔴 Critical | Missing/stub coverage for a P1 item, or any item touching auth, payment, data-integrity, security — regardless of priority |
| 🟡 Medium | Missing coverage for a user-facing P1/P2 item that is not security-critical |
| 🔵 Low | Missing test for a P3 item, or a cosmetic/internal behaviour |
| ⚠️ Warning | Weak traceability (no item ID in label) on an otherwise covered item — a label fix, not a new test |

Base severity on the item's text and its source User Story priority (P1/P2/P3), plus any
risk principle in the constitution.

### Step 3 — Gap Report

```markdown
## Untested Specification Items

Feature: specs/001-connect-hotel-filter/
Items: 5 (2 scenarios, 2 FR, 1 buildable SC) | Test tasks: 4 | Test files: 2 | Gaps: 2

### ❌ Gaps
| # | Item | Gap | Severity | Suggested Action | Suggested File |
|---|------|-----|----------|------------------|----------------|
| 1 | FR-001: persist filters across pagination | B (task T015 exists, no test file) | 🔴 Critical | Scaffold the test: `/speckit-test-generate FR-001` | tests/unit/filter-persistence.test.ts |
| 2 | FR-002: result count updates | D (label has no FR-002) | ⚠️ Warning | Rename label to cite FR-002 | tests/unit/result-count.test.ts:42 |

### ✅ Covered Items
| Item | Test Task | Test File | Confidence |
|------|-----------|-----------|------------|
| US1-AS1 | T010 [US1] ✅ | tests/integration/filter.test.ts | Strong |
| US1-AS2 | T010 [US1] ✅ | tests/integration/filter.test.ts | Strong |
```

### Step 4 — Prioritised Action List

```markdown
## Recommended Actions
1. 🔴 **FR-001 — pagination persistence (Critical)**
   - Test task `T015` exists but its file was never created; scaffold it: `/speckit-test-generate FR-001`
   - Implement: assert the active filter persists onto page 2 (tests/unit/filter-persistence.test.ts)
2. ⚠️ **FR-002 — weak label (Warning)**
   - Edit tests/unit/result-count.test.ts:42 → label `"FR-002: result count updates to filtered set"` (no new test needed).
```

### Step 5 — CI-Friendly Summary

```
SPECTEST GAPS: 1 critical (FR-001 no test), 1 warning (FR-002 weak label) — FAIL
```
or
```
SPECTEST GAPS: 5 items, 0 gaps, 0 stubs — PASS
```

## Rules

- **Read-only** — never create or modify test files or tasks.md.
- **Phase-aware** — only flag file/stub gaps for stories or phases marked complete in tasks.md; do not flag work not yet started.
- **`[P]` is parallelism** — identify test tasks by the Tests subsection or a test path, never by `[P]`.
- **Stub = gap** — a stub test counts as no test; always report it as a stub gap, separately.
- **Out-of-scope excluded** — items the spec's `## Assumptions` mark out of scope are not gaps.
- **Double-gap merged** — report "no task AND no file" as one `A + B` row, not two.
- **Risk overrides priority** — auth/payment/security/data-integrity items are always 🔴 Critical, even if P3.
- **Always actionable** — every gap row carries a concrete action, never just "add tests".
- **CI line** — final summary starts with `SPECTEST GAPS:` and ends with `PASS` or `FAIL`.
