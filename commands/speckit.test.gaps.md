---
description: "Find AC-N entries in spec.md with no matching test tasks or test files. Severity-classified. CI-friendly. Read-only."
---

# Find Untested Acceptance Criteria

Scan for ACs in spec.md that have no matching `T00x [P]` test task in tasks.md
**and/or** no matching test file in the codebase.

Designed for:
- Post-`/speckit.implement` audit (triggered automatically via after_implement hook)
- Pre-merge spot-check
- CI pipeline gap gate

Read-only — never creates or modifies files.

## User Input

```text
$ARGUMENTS
```

Consider user input before proceeding. The user may specify:
- Severity filter (e.g., "critical only", "all gaps")
- Scope (e.g., "tasks-only" — only check tasks.md gaps; "files-only" — only check test file gaps)
- Output format (e.g., "json", "checklist", "markdown")
- Phase filter (e.g., "Phase 2 only" — only flag gaps for completed phases)

## Prerequisites

1. Confirm you are inside a git repository.
2. Locate `specs/NNN-*/spec.md`. Ask if ambiguous.
3. Read `spec.md` fully. Extract all `AC-N` entries and `## Out of scope` exclusions.
4. Read `tasks.md` fully. Extract all `T00x [P]` test tasks and their AC references.
5. Locate test files (`**/*.test.*`, `**/*.spec.*`, `**/test_*`, `tests/`, `__tests__/`).
6. Parse test file labels/comments for `AC-N` references.
7. If `tasks.md` has phase markers, note which phases are marked complete — only flag gaps for complete phases.

## Outline

### Step 1 — Build Gap List

For each AC-N:

**Gap Type A — Missing test task in tasks.md:**
The AC exists in spec.md but no `T00x [P]` task references it.
Severity: BLOCKER — implementation should not proceed without a test task.

**Gap Type B — Missing test file:**
A `T00x [P]` task exists for the AC but the test file has not been created yet.
Severity: depends on phase — if implementation phase is marked done, this is CRITICAL.

**Gap Type C — Stub test file:**
A test file exists but all test bodies are `TODO`/`NotImplementedError`/`.skip`.
Severity: CRITICAL — a stub test is not coverage; it provides false confidence.

**Gap Type D — Weak coverage:**
Test exists but no `AC-N` label in describe/it — confidence is Medium or Weak.
Severity: WARNING — coverage exists but traceability chain is incomplete.

### Step 2 — Classify Severity

Each gap is classified:

| Severity | Definition | Examples |
|----------|-----------|---------|
| 🔴 Critical | Missing coverage for a P1 AC; security/data-integrity AC; stub test on a P1 AC | No test for AC covering auth, payment, data loss |
| 🟡 Medium | Missing coverage for a user-facing P1 AC that is not security-critical | Filter behaviour, UI state persistence |
| 🔵 Low | Missing test for a P2 AC; weak label confidence on an otherwise covered AC | Cosmetic behaviour, nice-to-have |
| ⚠️ Warning | Automation tag missing; label lacks AC-N reference; Medium/Weak confidence | Easily fixed without new test |

Base severity on:
- AC text: security, auth, payment, data-loss → 🔴 Critical
- UI user-facing flows → 🟡 Medium
- Cosmetic, internal, low-risk → 🔵 Low
- Constitution.md P1 designation if present

### Step 3 — Gap Report

```markdown
## Untested Acceptance Criteria

Feature: specs/001-connect-hotel-filter/
Spec ACs: 4 | Test tasks: 3 | Test files: 2 | Gaps: 2

### ❌ Gaps

| # | AC | Gap Type | Severity | Suggested Fix | Suggested File |
|---|-----|----------|----------|---------------|----------------|
| 1 | AC-4: Keyboard accessible, ARIA labels present | Type A + B: no test task, no test file | 🔴 Critical | Add T006 [P] in tasks.md; scaffold with /speckit.test.generate AC-4 | tests/e2e/StarRatingFilter.a11y.test.ts |
| 2 | AC-3: Result count updates | Type D: test exists, label lacks AC-3 reference | ⚠️ Warning | Rename test label to include "AC-3:" | tests/unit/StarRatingFilter.test.ts:42 |

### ✅ Covered ACs

| AC | Test Task | Test File | Confidence |
|----|-----------|-----------|------------|
| AC-1 | T001 [P] ✅ | tests/unit/StarRatingFilter.test.ts | Strong |
| AC-2 | T002 [P] ✅ | tests/integration/StarRatingFilter.pagination.test.ts | Strong |
```

### Step 4 — Prioritised Action List

```markdown
## Recommended Actions

1. 🔴 **AC-4 — Keyboard + ARIA (Critical)**
   - Add to tasks.md: `T006 [P] Add keyboard accessibility E2E test (AC-4) [BOTH]`
   - Run: `/speckit.test.generate AC-4`
   - Implement: axe-core scan + manual keyboard flow test
   - Estimated: 1 test file, 3 test cases

2. ⚠️ **AC-3 — Weak label (Warning)**
   - Edit: `tests/unit/StarRatingFilter.test.ts` line 42
   - Change: `"result count badge updates"` → `"AC-3: result count updates to reflect filtered set"`
   - No new test needed — just a label update for traceability
```

### Step 5 — CI-Friendly Summary

Always output a single final line:

```
SPECTEST GAPS: 1 critical (AC-4 no test), 1 warning (AC-3 weak label) — FAIL
```
or
```
SPECTEST GAPS: 4 ACs, 0 gaps, 0 stubs — PASS
```

## Rules

- **Read-only** — never create or modify test files or tasks.md
- **Phase-aware** — only flag gaps for implementation phases marked complete in tasks.md; do not flag ACs for work not yet started
- **Stub = gap** — a stub test file (all TODO) is treated as no test for gap-counting purposes; always report it separately as a stub gap
- **Out-of-scope is excluded** — ACs listed under `## Out of scope` in spec.md are not flagged as gaps
- **Double-gap reporting** — if an AC has both no test task AND no test file, report both gap types together (Type A + B) rather than two separate rows
- **Severity is based on AC content** — security, auth, payment, data-integrity ACs are always 🔴 Critical regardless of phase
- **Actionable every time** — every gap must include a concrete suggested action, not just "add tests"
- **CI-friendly output** — the final summary line must be parseable by a CI script: starts with `SPECTEST GAPS:`, ends with `PASS` or `FAIL`
