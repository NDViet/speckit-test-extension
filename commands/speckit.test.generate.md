---
description: "Generate test scaffolds from spec.md Acceptance Criteria, tagged with AC-N references, following team conventions from constitution.md"
---

# Generate Test Scaffolds from Acceptance Criteria

Read the feature's spec.md and generate ready-to-fill test scaffolds for every
Acceptance Criterion. Tests are:
- Organised **by AC-N**, not by implementation file
- Tagged with `AC-N` in every describe/it label for traceability
- Written in the framework declared in `constitution.md`
- Scaffold-only (TODO placeholders, Arrange-Act-Assert hints) — no assertion logic
- Never overwrite existing test files

## User Input

```text
$ARGUMENTS
```

Consider user input before proceeding. The user may specify:
- A specific AC to generate tests for (e.g., "AC-2 only")
- Test type preference (e.g., "unit only", "e2e only")
- Output directory override (e.g., "src/__tests__/")
- Framework override if constitution.md has none (e.g., "jest", "playwright", "pytest")

## Prerequisites

1. Confirm you are inside a git repository.
2. Locate the feature spec folder. Search for `specs/*/spec.md`. If multiple exist, ask
   the user which feature. If none found, stop:
   > "Cannot generate tests without spec.md — run `/speckit.specify` first."
3. Read `specs/NNN-*/spec.md` completely. Extract:
   - Every `AC-N:` entry under `## Acceptance Criteria`
   - Out-of-scope declarations (do not generate tests for these)
   - Actor name (used in test descriptions)
4. Read `specs/NNN-*/tasks.md` if present — check for existing `T00x [P]` test tasks to
   understand which test files are already expected.
5. Read `.specify/memory/constitution.md` — extract:
   - Test framework and location (co-located vs centralised)
   - Naming conventions
   - Any forbidden patterns
6. Detect existing test files to avoid overwriting.

## Outline

### Step 1 — Extract Acceptance Criteria

Parse `## Acceptance Criteria` from spec.md. Build an AC inventory:

```
AC-1: Multi-select — agent can select multiple star ratings simultaneously
AC-2: Filter persists across pagination
AC-3: Result count updates to reflect filtered set
AC-4: Accessible via keyboard, ARIA labels present
```

For each AC, identify:
- **Type hint** from the AC text: UI behaviour → component/E2E test; data persistence → integration; pure logic → unit
- **Boundary signals**: numbers, ranges, limits stated in the AC
- **Negative paths**: words like "rejects", "invalid", "must not", "error"
- **Accessibility signals**: "keyboard", "ARIA", "screen reader" → accessibility test case

### Step 2 — Determine Test Framework and Location

Read from `constitution.md`. Fall back to auto-detection if not declared:
- `package.json` scripts → jest / vitest / playwright
- `pyproject.toml` → pytest
- `go.mod` → go test
- Existing test files naming pattern

### Step 3 — Plan Test File Structure

Map each AC to a test file. Group related ACs into the same file where sensible:

```
tests/
├── unit/
│   └── StarRatingFilter/
│       └── StarRatingFilter.test.ts      ← AC-1, AC-3
├── integration/
│   └── StarRatingFilter.pagination.test.ts ← AC-2
└── e2e/
    └── StarRatingFilter.a11y.test.ts     ← AC-4
```

### Step 4 — Generate Test Scaffolds

For each AC produce a test file with:

**TypeScript / Jest example (AC-1):**
```typescript
/**
 * AC-1: Multi-select — agent can select multiple star ratings simultaneously
 * Source: specs/001-connect-hotel-filter/spec.md → Acceptance Criteria
 * Task:   tasks.md T001 [P] Add StarRatingFilter unit test (AC-1)
 * Actor:  [Actor from spec.md user story]
 */
describe('StarRatingFilter — AC-1 multi-select', () => {

  describe('happy path', () => {
    it('AC-1: selecting a single star rating shows only matching hotels', () => {
      // Arrange: render StarRatingFilter with hotel list
      // Act:     click 3-star checkbox
      // Assert:  only 3-star hotels visible; count badge updates
      throw new Error('TODO: implement test');
    });

    it('AC-1: selecting multiple star ratings shows all matching hotels', () => {
      // Arrange: render StarRatingFilter with hotel list
      // Act:     click 3-star, then 4-star checkboxes
      // Assert:  3-star and 4-star hotels visible simultaneously
      throw new Error('TODO: implement test');
    });
  });

  describe('boundary', () => {
    it('AC-1: selecting all 5 star ratings shows all hotels', () => {
      // Arrange: render StarRatingFilter
      // Act:     select ratings 1 through 5
      // Assert:  full hotel list restored
      throw new Error('TODO: implement test');
    });

    it('AC-1: deselecting last active filter shows full list', () => {
      // Arrange: 3-star active
      // Act:     deselect 3-star
      // Assert:  full hotel list shown; no filter active state
      throw new Error('TODO: implement test');
    });
  });

  describe('edge cases', () => {
    it('AC-1: selecting a rating with zero matching hotels shows empty state', () => {
      // Arrange: hotel list with no 1-star properties
      // Act:     click 1-star checkbox
      // Assert:  empty-state message shown; no crash
      throw new Error('TODO: implement test');
    });

    it('AC-1: rapid successive selections do not produce inconsistent state', () => {
      // Arrange: render StarRatingFilter
      // Act:     click 3, 4, 5 star checkboxes in rapid succession
      // Assert:  final state matches all three selected
      throw new Error('TODO: implement test');
    });
  });
});
```

**Python / pytest example (AC-1):**
```python
"""
AC-1: Multi-select — agent can select multiple star ratings simultaneously
Source: specs/001-connect-hotel-filter/spec.md → Acceptance Criteria
Task:   tasks.md T001 [P] Add star_rating_filter unit test (AC-1)
Actor:  [Actor from spec.md user story]
"""
import pytest

class TestStarRatingFilterAC1:
    """AC-1 multi-select: agent can select multiple star ratings simultaneously"""

    def test_single_rating_shows_matching_hotels(self):
        # Arrange: hotel list with mixed star ratings
        # Act: apply filter for 3-star
        # Assert: only 3-star hotels in result
        raise NotImplementedError("TODO: implement test")

    def test_multiple_ratings_shows_all_matching(self):
        # Arrange: hotel list
        # Act: apply filter for 3-star and 4-star
        # Assert: 3-star and 4-star hotels returned
        raise NotImplementedError("TODO: implement test")

    def test_zero_match_returns_empty_state(self):
        # Arrange: hotel list with no 1-star properties
        # Act: apply 1-star filter
        # Assert: empty list returned, no exception raised
        raise NotImplementedError("TODO: implement test")
```

### Step 5 — Output Summary

Report what was generated and the AC-to-test-task mapping:

```markdown
## Generated Test Scaffolds

| AC | Task (tasks.md) | Test File | Cases | Type |
|----|-----------------|-----------|-------|------|
| AC-1 | T001 [P] | tests/unit/StarRatingFilter.test.ts | 6 | Unit |
| AC-2 | T002 [P] | tests/integration/StarRatingFilter.pagination.test.ts | 3 | Integration |
| AC-3 | T003 [P] | tests/unit/StarRatingFilter.test.ts | 2 | Unit |
| AC-4 | T004 [P] | tests/e2e/StarRatingFilter.a11y.test.ts | 3 | E2E |

**Total: 14 test cases across 3 files**

### Traceability Chain
spec.md AC-N → tasks.md T00x [P] → test file (describe/it label) → CI result

### Next Steps
1. Fill in each `throw new Error('TODO')` / `raise NotImplementedError` with actual assertions.
2. Run `/speckit.test.coverage` after filling tests to verify AC-level coverage.
3. Add test plan link to PR description before merge.
```

## Rules

- **AC-centric** — every test suite maps to one or more `AC-N` entries from spec.md; never create tests without an AC anchor
- **Labels include AC-N** — every `describe()` / `it()` / `def test_` label must include the AC identifier (e.g., `"AC-1: ..."`)
- **Scaffold only** — generate `throw new Error('TODO')` / `raise NotImplementedError` placeholders; never write assertion logic
- **Traceability header** — every generated test file starts with a comment block: AC, spec source, task ID, actor
- **Framework-native** — use the framework from `constitution.md`; do not fall back to a generic format without telling the user
- **Never overwrite** — if the target test file already exists, skip it and report it as already present
- **Cover all three levels** — unit, integration, and E2E where the AC provides enough context to determine which applies
- **Include boundary + edge cases** — do not only scaffold the happy path; include at minimum one boundary case and one edge case per AC
- **Accessibility ACs** — any AC mentioning keyboard, ARIA, or screen reader gets an accessibility test case using the team's a11y tool (axe-core/jest-axe per constitution.md)
- **Out-of-scope is not tested** — do not generate tests for anything listed under `## Out of scope` in spec.md
