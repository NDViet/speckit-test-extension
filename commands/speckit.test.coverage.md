---
description: "Map every spec.md AC-N to existing test files and calculate AC-level coverage. Rates mappings Strong/Medium/Weak. Read-only."
---

# AC-Level Coverage Report

Analyze existing test files and map them back to the Acceptance Criteria in spec.md.
This measures **AC-level coverage** — what percentage of spec ACs have at least one
real (non-stub) test that demonstrably asserts the AC's behaviour.

This is different from code line/branch coverage. A feature can have 100% line coverage
and 0% AC coverage if the tests were written without reference to the spec.

Read-only — never modifies any files.

## User Input

```text
$ARGUMENTS
```

Consider user input before proceeding. The user may specify:
- A specific AC to report on (e.g., "AC-3")
- Output format (e.g., "summary only", "full map", "json")
- Coverage threshold override (e.g., "minimum 90%")
- Test directory override

## Prerequisites

1. Confirm you are inside a git repository.
2. Locate `specs/NNN-*/spec.md`. Ask if ambiguous.
3. Read `spec.md` fully. Extract every `AC-N:` entry.
4. Read `tasks.md`. Build the expected AC → T00x [P] → test file mapping.
5. Locate test files by searching: `**/*.test.*`, `**/*.spec.*`, `**/test_*`, `tests/`, `__tests__/`
6. Read test file contents to extract describe/it labels, test names, and comments.
7. Read `testplan-NNN-*.md` if present — use it to cross-reference the AC traceability matrix.

## Outline

### Step 1 — Build AC Inventory

From spec.md, extract all ACs:

```
AC-1: Multi-select — agent can select multiple star ratings simultaneously
AC-2: Filter persists across pagination
AC-3: Result count updates to reflect filtered set
AC-4: Accessible via keyboard, ARIA labels present
```

### Step 2 — Discover and Index Test Files

For each test file found:
- Extract all `describe()`, `it()`, `test()`, `def test_`, `func Test` labels
- Look for AC reference patterns: `AC-1`, `AC-2`, etc. in labels or comments
- Note if test throws `new Error('TODO')`, `raise NotImplementedError`, `.todo`, `.skip` → mark as **stub**

### Step 3 — Map ACs to Test Coverage

For each AC-N, determine coverage status and confidence:

**Confidence ratings:**
- **Strong** — test label explicitly contains `AC-N` (e.g., `"AC-1: multi-select..."`)
- **Medium** — test label/comment contains keywords from AC text (e.g., "multi-select", "star rating")
- **Weak** — test file name maps to the implementation file referenced in plan.md, but no explicit AC mention
- **Stub** — test exists but body is `TODO`/`NotImplementedError`/`.skip` — does not count as coverage

### Step 4 — Calculate Coverage Metrics

```markdown
## AC Coverage Summary

| Category | Total | Covered | Stub Only | No Tests | Coverage |
|----------|-------|---------|-----------|----------|----------|
| Acceptance Criteria | 4 | 3 | 0 | 1 | 75.0% |

Coverage threshold (from constitution.md): 100% P1 ACs must pass CI
Status: ⚠️ Below threshold — AC-4 has no test coverage
```

### Step 5 — Detailed AC Coverage Map

```markdown
## Detailed AC Coverage Map

| AC | Description | Test File | Test Label | Confidence | Type | Status |
|----|-------------|-----------|------------|------------|------|--------|
| AC-1 | Multi-select | tests/unit/StarRatingFilter.test.ts | "AC-1: selecting multiple..." | Strong | Unit | ✅ Covered |
| AC-2 | Persists across pagination | tests/integration/StarRatingFilter.pagination.test.ts | "AC-2: filter retained on page 2" | Strong | Integration | ✅ Covered |
| AC-3 | Result count updates | tests/unit/StarRatingFilter.test.ts | "result count badge updates" | Medium | Unit | ⚠️ Covered (Medium confidence — add AC-3 to label) |
| AC-4 | Keyboard accessible | — | — | — | — | ❌ No tests |
```

### Step 6 — Coverage by Test Type

```markdown
## Coverage by Test Type

| AC | Unit | Integration | E2E | Manual (test plan) |
|----|------|-------------|-----|--------------------|
| AC-1 | ✅ Strong | ❌ | ❌ | ✅ TC-001, TC-002 |
| AC-2 | ❌ | ✅ Strong | ❌ | ✅ TC-003 |
| AC-3 | ⚠️ Medium | ❌ | ❌ | ✅ TC-004 |
| AC-4 | ❌ | ❌ | ❌ | ❌ |
```

### Step 7 — Traceability Chain Completeness

Check the full chain for each AC:

```markdown
## Traceability Chain

| AC | tasks.md T[P] | Test File | CI Status | Chain |
|----|---------------|-----------|-----------|-------|
| AC-1 | T001 ✅ | ✅ exists | ✅ green | ✅ Complete |
| AC-2 | T002 ✅ | ✅ exists | ✅ green | ✅ Complete |
| AC-3 | T003 ✅ | ✅ exists (Medium) | ✅ green | ⚠️ Weak label |
| AC-4 | T004 ✅ | ❌ missing | ❌ | ❌ Broken |
```

### Step 8 — Recommendations

```markdown
## Recommendations

1. **AC-4 (❌ No tests)** — test file expected at `tests/e2e/StarRatingFilter.a11y.test.ts`
   per tasks.md T004. Run `/speckit.test.generate AC-4` to scaffold it.

2. **AC-3 (⚠️ Medium confidence)** — test label `"result count badge updates"` should be
   renamed to `"AC-3: result count updates to reflect filtered set"` for Strong confidence.
```

### Step 9 — CI-Friendly Summary

```
SPECTEST COVERAGE: 4 ACs — 3 covered (75%), 1 no tests (AC-4), 0 stubs — BELOW THRESHOLD
```
or
```
SPECTEST COVERAGE: 4 ACs — 4 covered (100%), 0 stubs — PASS
```

## Rules

- **Read-only** — never modify any files; only analyse and report
- **AC-centric** — measure coverage per AC-N, not per code line or branch
- **Stub tests do not count** — a test file with only `TODO` / `NotImplementedError` / `.skip` bodies counts as 0% coverage for that AC
- **Confidence matters** — report the confidence rating; a Weak mapping is not the same as a Strong one; do not inflate scores
- **Traceability chain** — always check the full chain: AC → T00x [P] in tasks.md → test file → CI; a broken link at any point is reported
- **Constitution threshold** — if constitution.md declares a minimum coverage threshold, compare and report pass/fail explicitly
- **Test plan cross-reference** — if `testplan-NNN-*.md` exists, cross-reference the manual test cases in the AC traceability matrix
- **No false positives** — a test file name alone (without AC label or keyword match) does not count as Strong or Medium coverage
