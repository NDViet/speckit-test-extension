---
description: "Map every spec.md testable item (Acceptance Scenarios, FR-###, SC-###) to existing test files and rate coverage Strong/Medium/Weak. Read-only."
argument-hint: "[--item FR-001] [--summary] [--json] [--min 90]"
---

# Requirement-Level Coverage Report

**QA lane — the QA engineer's third step on the opened PR** (after `/speckit-test-generate`):
`test-plan → test-generate → test-coverage → test-gaps → test-review`.

Analyse the existing test files and map them back to the feature's **testable items** in
`spec.md`. This measures **specification coverage** — what fraction of the spec's Acceptance
Scenarios, Functional Requirements, and buildable Success Criteria have a real (non-stub)
test that demonstrably asserts the described behaviour.

This is different from line/branch coverage. A feature can have 100% line coverage and 0%
specification coverage if the tests were written without reference to the spec.

**Read-only** — never modifies any files.

## User Input

```text
$ARGUMENTS
```

The user may specify:
- `--item FR-001` (or `US1-AS2`, `SC-001`) — report on a single item
- `--summary` — summary table only
- `--json` — machine-readable output
- `--min 90` — coverage threshold override (else use the constitution's)
- A test directory override

## Prerequisites

1. Resolve the feature directory:
   `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`
   Parse `FEATURE_DIR`. Fall back to `specs/*/spec.md` if the script is unavailable.
2. Read `FEATURE_DIR/spec.md` fully — extract the testable-item inventory (see Step 1).
3. Read `FEATURE_DIR/tasks.md` — build the expected item → test-task → test-file chain.
4. Read `FEATURE_DIR/plan.md` — map implementation files to stories for Weak-confidence inference.
5. Discover test files: `**/*.test.*`, `**/*.spec.*`, `**/test_*`, `tests/`, `__tests__/`, `**/*_test.go`.
6. Read test-file contents — extract `describe`/`it`/`test`/`def test_`/`func Test` labels and comments.
7. Read `FEATURE_DIR/test-plan.md` and `FEATURE_DIR/checklists/*.md` if present — cross-reference.

## Outline

### Step 1 — Build the Testable-Item Inventory

From spec.md, using the standard ID scheme:
- Acceptance Scenarios per User Story → `US{n}-AS{m}` (carry the story priority P1/P2/P3)
- Functional Requirements → `FR-###`
- Success Criteria needing buildable tests → `SC-###`

```
US1-AS1 (P1): single star rating filters the list
US1-AS2 (P1): multiple star ratings filter simultaneously
FR-001  (P1): filters persist across pagination
FR-002  (P1): result count updates to the filtered set
SC-001  (P1): filtered render < 500ms for 1000 hotels
```

### Step 2 — Index Test Files

For each test file: extract every test label, the AC/FR/SC IDs and keywords mentioned, and
flag **stubs** — bodies that are `throw new Error('TODO')`, `raise NotImplementedError`,
`.todo`, `.skip`, `xit`/`xdescribe`/`it.skip`, `@pytest.mark.skip`, `expect(true).toBe(true)`,
bare `toBeTruthy()`/`assert True` with no setup, or empty bodies. A stub does not count as coverage.

### Step 3 — Map Items to Coverage with a Confidence Rating

- **Strong** — a test label/comment cites the exact item ID (e.g., `"US1-AS1: ..."`, `"FR-001 ..."`).
- **Medium** — the label/comment matches distinctive keywords from the item text (e.g., "persist across pagination") but names no ID.
- **Weak** — the test file maps to the story's implementation file (per plan.md) but mentions neither ID nor keywords.
- **Stub** — a test exists but its body is a stub → counts as **0%** for that item.

### Step 4 — Coverage Summary

```markdown
## Specification Coverage Summary

| Category | Total | Covered | Stub Only | No Tests | Coverage |
|----------|-------|---------|-----------|----------|----------|
| Acceptance Scenarios | 2 | 2 | 0 | 0 | 100% |
| Functional Requirements | 2 | 1 | 0 | 1 | 50% |
| Success Criteria (buildable) | 1 | 0 | 1 | 0 | 0% |
| **All testable items** | **5** | **3** | **1** | **1** | **60%** |

Threshold (constitution.md): all P1 items covered (Strong) before merge
Status: ⚠️ Below threshold — FR-001 has no test, SC-001 is stub-only
```

### Step 5 — Detailed Coverage Map

```markdown
## Detailed Coverage Map

| Item | Pri | Description | Test File | Test Label | Confidence | Status |
|------|-----|-------------|-----------|------------|------------|--------|
| US1-AS1 | P1 | single rating filters | tests/integration/filter.test.ts | "US1-AS1: 3-star filters list" | Strong | ✅ |
| US1-AS2 | P1 | multi rating filters | tests/integration/filter.test.ts | "US1-AS2: 3+4-star simultaneously" | Strong | ✅ |
| FR-001 | P1 | persist across pagination | — | — | — | ❌ No tests |
| FR-002 | P1 | result count updates | tests/unit/result-count.test.ts | "result badge updates" | Medium | ⚠️ Add FR-002 to label |
| SC-001 | P1 | render < 500ms | tests/perf/filter.perf.ts | "perf budget" (.skip) | Stub | ❌ Stub only |
```

### Step 6 — Coverage by Test Type

```markdown
| Item | Unit | Integration | E2E/Perf | Manual (test-plan) |
|------|------|-------------|----------|--------------------|
| US1-AS1 | ❌ | ✅ Strong | ❌ | ✅ TC-001 |
| FR-001 | ❌ | ❌ | ❌ | ❌ |
| SC-001 | ❌ | ❌ | ⚠️ Stub | ❌ |
```

### Step 7 — Traceability Chain Completeness

```markdown
| Item | tasks.md test task | Test File | CI | Chain |
|------|--------------------|-----------|----|-------|
| US1-AS1 | T010 [US1] ✅ | ✅ | ✅ | ✅ Complete |
| FR-001 | T015 [US1] ✅ | ❌ missing | ❌ | ❌ Broken (no file) |
| FR-002 | T016 [US1] ✅ | ✅ (Medium) | ✅ | ⚠️ Weak label |
| SC-001 | T017 [US1] ✅ | ⚠️ stub | ❌ | ❌ Broken (stub) |
```

### Step 8 — Recommendations

```markdown
1. **FR-001 (❌ No tests)** — expected at tests/unit/filter-persistence.test.ts per tasks.md T015.
   Run `/speckit-test-generate FR-001` to scaffold it.
2. **SC-001 (❌ Stub)** — remove `.skip` and implement the < 500ms assertion in tests/perf/filter.perf.ts.
3. **FR-002 (⚠️ Medium)** — rename "result badge updates" → "FR-002: result count updates to filtered set".
```

### Step 9 — CI-Friendly Summary

```
SPECTEST COVERAGE: 5 items — 3 covered (60%), 1 no tests (FR-001), 1 stub (SC-001) — BELOW THRESHOLD
```
or
```
SPECTEST COVERAGE: 5 items — 5 covered (100% Strong), 0 stubs — PASS
```

## Rules

- **Read-only** — analyse and report only.
- **Spec-centric** — measure coverage per testable item (`US{n}-AS{m}` / `FR-###` / `SC-###`), never per code line or branch.
- **Stubs are 0%** — a stub test never counts as coverage; always report stubs separately.
- **Report confidence honestly** — do not inflate Weak/Medium to Strong; a filename match alone is at most Weak.
- **Buildable SC only** — include Success Criteria that need test infrastructure; exclude post-launch business KPIs.
- **Whole chain** — check spec item → tasks.md test task → test file → CI; report a break at any link.
- **Constitution threshold** — if the constitution sets a coverage gate, compare and report pass/fail explicitly; otherwise default to "all P1 items Strong-covered".
- **Cross-reference artefacts** — if `test-plan.md` or `checklists/test.md` exist, fold their manual cases into the map.
