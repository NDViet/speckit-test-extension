---
description: "Test prep — mandatory after_tasks hook. Writes FEATURE_DIR/test-plan.md (traceability matrix, entry/exit, risks), scaffolds higher-layer tests (integration / E2E / regression / perf / a11y) as failing stubs labelled with the spec item ID, and seeds FEATURE_DIR/checklists/test.md. Idempotent; never overwrites existing tests."
argument-hint: "[--dry-run] [--scope smoke|regression|full] [--story US1] [--no-checklist] [--advisory]"
---

# Test Prep — `after_tasks` hook

Runs immediately after `/speckit-tasks` so higher-layer artefacts exist before `/speckit-analyze` (optional) and `/speckit-implement`.

**Scope:** integration / E2E / regression / perf / a11y. Unit/contract is `planaudit` + `/speckit-implement` territory.
**Writes:** `test-plan.md`, scaffold stubs under `tests/{integration,e2e,regression,perf,a11y}/`, `checklists/test.md`. Never edits `spec.md`, `plan.md`, `tasks.md`, source, or existing tests.
**Hook default:** write. `--dry-run` previews.

## User Input

```text
$ARGUMENTS
```

Flags: `--dry-run`, `--scope smoke|regression|full` (default full), `--story US1`, `--no-checklist`, `--advisory` (banner "QA layers waived").

## Prerequisites

1. `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` → parse `FEATURE_DIR`, `AVAILABLE_DOCS`.
2. Read `spec.md` (items, Edge Cases, Assumptions), `plan.md` (incl. `## Testing Strategy` from planaudit), `tasks.md`, `.specify/memory/constitution.md`. Scan `tests/`.

## Outline

### Phase A — Write `FEATURE_DIR/test-plan.md`

Refresh in place; preserve content between `<!-- MANUAL-EDITS START -->` / `<!-- MANUAL-EDITS END -->`.

Sections in order:

1. **Header** — feature, owner, status, links, constitution version, framework, scope.
2. **Item Traceability Matrix** — rows: every `US{n}-AS{m}`, gated `FR-###`, buildable `SC-###`. Columns: priority, unit/contract task ID(s), integration test, E2E, regression note, perf/a11y plan, status.
3. **Test Strategy** — pyramid summary (unit/contract from planaudit + QA layers), environments, data fixtures, masking.
4. **Entry & Exit Criteria** — entry: PR open + unit/contract green + this plan present. Exit: zero P1 gaps + zero `qareview` Blockers + checklist green.
5. **Risk Register** — derived from `### Edge Cases` and `## Assumptions`.
6. **Test Environment & Data** — tools, accounts, seed, teardown.
7. **Open Questions** — every `[NEEDS CLARIFICATION]` in spec.md.

Idempotency: regenerate §1, 2, 3, 6, 7; preserve §4, 5 if QA-edited.

### Phase B — Scaffold higher-layer stubs

For every gated item missing a QA-layer test, create a **failing** stub labelled with the item ID.

| Layer | Trigger |
|---|---|
| `tests/integration/` | every P1 `US{n}-AS{m}` without one |
| `tests/e2e/` | each user story without an E2E happy path |
| `tests/regression/` | FR tied to a high-blast-radius Risk row |
| `tests/perf/` | every buildable `SC-###` with a perf criterion |
| `tests/a11y/` | every `User-facing UI` story |

- **Path:** `tests/<layer>/<slug>.<layer>.test.<ext>`; `<slug>` from spec item.
- **Framework:** from plan.md Testing Strategy.
- **Body:** A/A/A skeleton mapping G/W/T; header comment names the item ID; TODO list of edge cases.
- **Must fail on first run** (`expect.fail("not implemented")` or equivalent).
- **Never overwrites.** Existing file → skip, record "kept".

### Phase C — Seed `FEATURE_DIR/checklists/test.md`

```markdown
# Test Checklist: <feature>

> Source: speckit.test.qaprep (after_tasks).

## Coverage
- [ ] Every P1 AS has a unit/contract test (verified by tasksaudit)
- [ ] Every P1 AS has an integration test
- [ ] Every user story has an E2E happy-path test
- [ ] Every buildable SC-### has a perf test
- [ ] Every user-facing UI story has an a11y test

## Quality
- [ ] No stub-by-description tasks remain in tasks.md
- [ ] All integration/E2E tests pass locally
- [ ] Risk Register reviewed; mitigations linked

## Sign-off
- [ ] /speckit-analyze produced zero CRITICAL findings (if run)
- [ ] qareview produced zero Blocker findings
- [ ] Test plan peer-reviewed
```

Refresh rule: **never uncheck** QA-ticked rows; add new rows for newly gated items.

### Phase D — Report

```
SPECTEST QAPREP:
  test-plan.md: <created|refreshed> (12 items, 3 risks, 1 open question)
  scaffolds:    integration +4, e2e +2, perf +1, a11y +1 (kept: 3)
  checklist:    <created|refreshed> (15 items, 4 ticked)
  → review.md will be refreshed by qareview on after_analyze (advisory) and after_implement (formal).
```

## Rules

- **Idempotent** — refresh test-plan.md and checklist preserving QA edits and ticks; add missing scaffolds; never duplicate.
- **Never overwrites existing tests.**
- **Higher layers only** — unit/contract is out of scope here.
- **Stubs fail on purpose** — missing coverage is visible in CI.
- **Spec is authority** — every stub traces to a `US{n}-AS{m}`, `FR-###`, or `SC-###`.
- **Constitution may add layers, never silently remove them** (`--advisory` required to waive).
- **Reports, never blocks** — gating is `tasksaudit` (pre-implement) and `qareview` (pre-merge).
