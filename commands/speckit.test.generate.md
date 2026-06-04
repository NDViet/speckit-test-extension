---
description: "Generate test scaffolds from spec.md testable items (Acceptance Scenarios, FR-###, SC-###), labelled with the item ID for traceability, in the framework declared by constitution.md / plan.md."
argument-hint: "[US1-AS2 | FR-001 | SC-001] [unit|integration|e2e] [--dir tests/]"
---

# Generate Test Scaffolds from Specification Items

**QA lane — the QA engineer's second step on the opened PR** (after `/speckit-test-plan`):
`test-plan → test-generate → test-coverage → test-gaps → test-review`. QA uses it to scaffold
the **QA-owned layers** (integration, E2E, regression, performance, accessibility) and any
spec item still missing a test. The developer's **unit/contract** tests were already written
during `/speckit-implement` (driven by the `tasksaudit` gate), so this is not a developer step.

Read the feature's `spec.md` and generate ready-to-fill test scaffolds for its testable
items. Scaffolds are:
- Organised **by spec item** (`US{n}-AS{m}`, `FR-###`, `SC-###`), not by implementation file
- Labelled with the item ID in every `describe`/`it`/`def test_` for traceability
- Written in the framework from `constitution.md` / `plan.md` (auto-detected as fallback)
- Scaffold-only — Arrange/Act/Assert hints and a failing placeholder, **no** assertion logic
- Never overwriting an existing test file

The placeholder body fails by design (`throw`/`raise`) until QA fills in the assertions —
asserted **against the implemented feature** on the PR (these QA-layer tests are written after
implementation, so they verify behaviour rather than drive TDD red-green).

## User Input

```text
$ARGUMENTS
```

The user may specify:
- A single item to scaffold (e.g., `US1-AS2`, `FR-001`, `SC-001`)
- A test level (`unit`, `integration`, `e2e`)
- An output directory override (e.g., `--dir tests/`)
- A framework override if none is declared (e.g., `jest`, `vitest`, `playwright`, `pytest`)

## Prerequisites

1. Resolve the feature directory:
   `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`
   Parse `FEATURE_DIR` and `AVAILABLE_DOCS`. Fall back to `specs/*/spec.md` if unavailable.
   If no spec.md exists, stop: "Cannot generate tests without spec.md — run /speckit-specify first."
2. Read `FEATURE_DIR/spec.md` completely. Extract:
   - User Stories with priorities and their **Acceptance Scenarios** (Given/When/Then)
   - Functional Requirements (`FR-###`) and buildable Success Criteria (`SC-###`)
   - `### Edge Cases` (negative/boundary candidates)
   - Out-of-scope statements from `## Assumptions` (do not scaffold these)
   - The actor/persona named in the user stories
3. Read `FEATURE_DIR/plan.md` — tech stack, project structure, test layout.
4. Read `FEATURE_DIR/tasks.md` if present — map existing test tasks (and their `[US#]`/paths) so
   scaffolds land where the tasks expect them.
5. Read `.specify/memory/constitution.md` — test framework, location convention, any test principles.
6. Detect existing test files to avoid overwriting.

## Outline

### Step 1 — Extract the Testable Items

Build the inventory using the standard ID scheme:

```
US1-AS1 (P1): Given hotel list loaded, When 3-star selected, Then only 3-star hotels show
US1-AS2 (P1): Given 3-star selected, When 4-star added, Then 3+4-star hotels show
FR-001  (P1): System MUST persist active filters across pagination
FR-002  (P1): System MUST update the result count to the filtered set
SC-001  (P1): Filtered results render in < 500ms for 1000 hotels
```

For each item, derive:
- **Level** — Acceptance Scenario (user journey) → integration/E2E; FR (capability) → unit/integration; SC (measurable) → perf/load or specialised test.
- **Boundaries** — numbers, ranges, limits in the text.
- **Negative paths** — "rejects", "invalid", "must not", "error".
- **Given/When/Then** — for Acceptance Scenarios, map Given→Arrange, When→Act, Then→Assert directly.
- **Accessibility** — "keyboard", "ARIA", "screen reader" → an a11y case using the team's tool (jest-axe/axe-core).

### Step 2 — Determine Framework and Location

From `constitution.md` / `plan.md`. Fall back to auto-detection:
`package.json` → jest/vitest/playwright; `pyproject.toml` → pytest; `go.mod` → go test;
else mirror the existing test-file naming pattern. Announce the chosen framework.

### Step 3 — Plan the Test-File Layout

Map each item to a file, grouping related items sensibly and matching paths already named in tasks.md:

```
tests/
├── integration/
│   └── star-rating-filter.test.ts      ← US1-AS1, US1-AS2
├── unit/
│   ├── filter-persistence.test.ts      ← FR-001
│   └── result-count.test.ts            ← FR-002
└── perf/
    └── filter.perf.ts                  ← SC-001
```

### Step 4 — Generate Scaffolds

Each file opens with a traceability header and uses the item ID in every label.

**TypeScript / Jest (Acceptance Scenarios — Given/When/Then maps to AAA):**
```typescript
/**
 * Source: specs/001-connect-hotel-filter/spec.md → User Story 1 (P1)
 * Items:  US1-AS1, US1-AS2
 * Tasks:  tasks.md T010 [US1]
 * Actor:  Travel agent
 * NOTE: Placeholder fails until QA fills the assertions; verifies the implemented feature on the PR.
 */
describe('Star rating filter — User Story 1', () => {
  describe('happy path', () => {
    it('US1-AS1: selecting a single rating shows only matching hotels', () => {
      // Given (Arrange): hotel list loaded with mixed ratings
      // When  (Act):     agent selects the 3-star checkbox
      // Then  (Assert):  only 3-star hotels are visible; count badge updates
      throw new Error('TODO: implement US1-AS1');
    });

    it('US1-AS2: selecting multiple ratings shows all matching hotels', () => {
      // Given: 3-star already selected
      // When:  agent adds 4-star
      // Then:  3-star and 4-star hotels are visible simultaneously
      throw new Error('TODO: implement US1-AS2');
    });
  });

  describe('boundary', () => {
    it('US1-AS2: selecting all five ratings restores the full list', () => {
      throw new Error('TODO: implement boundary case');
    });
    it('US1-AS1: deselecting the last active rating shows the full list', () => {
      throw new Error('TODO: implement boundary case');
    });
  });

  describe('edge cases', () => {
    it('US1-AS1: a rating with zero matches shows the empty state, no crash', () => {
      throw new Error('TODO: implement edge case');
    });
  });
});
```

**TypeScript / Jest (Functional Requirement):**
```typescript
/**
 * Source: specs/001-connect-hotel-filter/spec.md → Functional Requirements
 * Item:   FR-001 — System MUST persist active filters across pagination
 * Task:   tasks.md T015 [US1]
 */
describe('FR-001 — filters persist across pagination', () => {
  it('FR-001: active filter is retained when navigating to page 2', () => {
    // Arrange: 3-star filter applied on page 1
    // Act:     navigate to page 2
    // Assert:  3-star filter still active; only 3-star hotels listed
    throw new Error('TODO: implement FR-001');
  });
});
```

**Python / pytest (Functional Requirement):**
```python
"""
Source: specs/001-connect-hotel-filter/spec.md → Functional Requirements
Item:   FR-002 — System MUST update the result count to the filtered set
Task:   tasks.md T016 [US1]
NOTE: Placeholder fails until QA fills the assertions; verifies the implemented feature.
"""
import pytest

class TestFR002ResultCount:
    """FR-002: result count reflects the filtered set"""

    def test_fr_002_count_matches_filtered_results(self):
        # Arrange: hotel list with mixed ratings
        # Act: apply 3-star filter
        # Assert: result count equals the number of 3-star hotels
        raise NotImplementedError("TODO: implement FR-002")

    def test_fr_002_count_returns_to_total_when_cleared(self):
        raise NotImplementedError("TODO: implement FR-002 boundary")
```

**Performance scaffold (Success Criterion):**
```typescript
/**
 * Item: SC-001 — Filtered results render in < 500ms for 1000 hotels
 * Task: tasks.md T017 [US1]
 */
describe('SC-001 — render performance', () => {
  it('SC-001: 1000-hotel filtered render completes under 500ms', () => {
    // Arrange: seed 1000 hotels
    // Act:     apply filter, measure render time
    // Assert:  elapsed < 500ms (assert against the SC threshold)
    throw new Error('TODO: implement SC-001 perf budget');
  });
});
```

### Step 5 — Output Summary

```markdown
## Generated Test Scaffolds

| Item | Task | Test File | Cases | Level |
|------|------|-----------|-------|-------|
| US1-AS1 | T010 [US1] | tests/integration/star-rating-filter.test.ts | 4 | Integration |
| US1-AS2 | T010 [US1] | tests/integration/star-rating-filter.test.ts | 3 | Integration |
| FR-001 | T015 [US1] | tests/unit/filter-persistence.test.ts | 1 | Unit |
| FR-002 | T016 [US1] | tests/unit/result-count.test.ts | 2 | Unit |
| SC-001 | T017 [US1] | tests/perf/filter.perf.ts | 1 | Perf |

Traceability chain: spec item → tasks.md test task → test label → CI

### Next Steps
1. Replace each `throw new Error('TODO')` / `raise NotImplementedError` with real assertions.
2. Confirm the tests FAIL first (TDD), then implement to green.
3. Run `/speckit-test-coverage` to verify Strong coverage per item.
```

## Rules

- **Spec-anchored** — every suite maps to one or more `US{n}-AS{m}` / `FR-###` / `SC-###`; never scaffold a test without a spec anchor.
- **ID in every label** — each `describe`/`it`/`def test_` label includes the item ID.
- **Scaffold only** — generate failing placeholders and AAA hints; never write assertion logic.
- **Placeholders fail until filled** — scaffold bodies `throw`/`raise` so an unfilled test fails; QA replaces them with assertions that verify the implemented feature on the PR.
- **Traceability header** — every file starts with source spec path, item ID(s), task ID, actor.
- **Framework-native** — use the constitution/plan framework; if none, auto-detect and announce it — never silently emit a generic format.
- **Never overwrite** — if the target file exists, skip it and report it as already present.
- **Cover levels appropriately** — scenarios → integration/E2E; FR → unit/integration; buildable SC → perf/specialised. Include at least one boundary and one edge case per behavioural item.
- **Accessibility** — items mentioning keyboard/ARIA/screen reader get an a11y case with the team's tool.
- **Out-of-scope excluded** — never scaffold anything the spec's `## Assumptions` mark out of scope.
- **Match task paths** — when tasks.md names a test path for an item, scaffold at that path.
