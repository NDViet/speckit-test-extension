---
description: "Test prep — runs as the after_implement hook. Writes FEATURE_DIR/test-plan.md (test strategy, traceability matrix, entry/exit criteria, risks), scaffolds the higher-layer tests (integration / E2E / regression / perf / a11y) as failing stubs labelled with the spec item ID, and seeds checklists/test.md so the workflow has the test artefacts in place before /speckit-analyze runs. Mandatory; idempotent (refreshes test-plan.md in place; never overwrites existing test code)."
argument-hint: "[--scope smoke|regression|full] [--also-checklist] [--story US1]"
---

# Test Prep — built-in step of `/speckit-implement`

**Runs automatically as the mandatory `after_implement` hook of `/speckit-implement`.**
Quality is part of the workflow, not a separate role: this step bundles what would otherwise
be three separate manual commands (`test-plan`, `test-generate`, seeding `checklists/test.md`)
into a single mandatory step that runs immediately after implementation finishes, so the
higher-layer test artefacts are in place before anyone runs `/speckit-analyze`.

When `/speckit-analyze` is invoked next (anytime in the workflow, by anyone), `qaprep`'s
artefacts already exist for it to sweep into its consistency check, and the `after_analyze`
hook (`speckit.test.qareview`) produces the consistency + quality verdict.

**Mandatory.** The `after_implement` hook fires this with no flags; default is `--write`
behaviour (artefacts are produced). `--dry-run` previews; never used by the hook itself.

**Write scope:**
- `FEATURE_DIR/test-plan.md` — created if absent, refreshed in place if present (idempotent).
- `tests/integration/`, `tests/e2e/`, `tests/regression/`, `tests/perf/`, `tests/a11y/` — **scaffold only**: creates failing stub files for items missing them; **never overwrites existing tests**.
- `FEATURE_DIR/checklists/test.md` — created if absent, refreshed otherwise.

Never modifies `spec.md`, `plan.md`, `tasks.md`, source code, or unit tests written by the
developer.

> ⚠️ Unit/contract tests are planned earlier in the workflow (by `speckit.test.planaudit`),
> verified before implementation (by `speckit.test.tasksaudit`), and written by
> `/speckit-implement` itself. This step does **not** generate unit tests; it scaffolds the
> higher layers (integration / E2E / regression / perf / a11y).

## User Input

```text
$ARGUMENTS
```

The user (or hook) may specify:
- _(no flags)_ — default; produces all three artefacts
- `--dry-run` — preview only; modify nothing
- `--scope smoke|regression|full` — sizing for test-plan.md (default: full)
- `--story US1` — limit scaffolding to one user story
- `--no-checklist` — skip checklists/test.md
- `--advisory` — produce artefacts but mark the policy banner "QA layers waived" (rare)

## Prerequisites

1. Resolve the feature directory. From repo root:
   `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`
   Parse `FEATURE_DIR` and `AVAILABLE_DOCS`.
2. Read `FEATURE_DIR/spec.md` fully — User Stories, Acceptance Scenarios (`US{n}-AS{m}`),
   Functional Requirements (`FR-###`), Success Criteria (`SC-###`), Edge Cases, Assumptions.
3. Read `FEATURE_DIR/plan.md` fully — tech stack, integration points, external services,
   the `## Testing Strategy` section (written by `planaudit`).
4. Read `FEATURE_DIR/tasks.md` — what shipped, `[US#]` labels, test tasks present.
5. Read `.specify/memory/constitution.md` — QA layers mandated, frameworks, thresholds.
6. Scan `tests/` to see what test files actually exist.

## Outline

The command runs three sub-phases in order. Each is idempotent.

### Phase A — Write `FEATURE_DIR/test-plan.md`

Produce a complete QA test plan. If the file exists, refresh it in place; do not overwrite
manual edits inside `<!-- MANUAL-EDITS START -->` / `<!-- MANUAL-EDITS END -->` markers.

**Sections (always in this order):**

1. **Header table** — feature name, owner, status, links to spec/plan/tasks, constitution
   version, framework, scope, audience.
2. **Item Traceability Matrix** — every `US{n}-AS{m}` and `FR-###` (gated) and every
   buildable `SC-###` (perf / security / availability) — rows; columns: priority, unit/contract
   task ID(s), integration test, E2E test, regression note, perf/a11y plan, status.
3. **Test Strategy** — pyramid summary (what unit/contract covers per `planaudit`, what QA
   layers add on top), environments (dev/staging/prod-like), data fixtures, masking.
4. **Entry & Exit Criteria** — entry: PR open + unit/contract green + this plan present;
   exit: zero P1 gaps + zero criticals in `qareview` + checklist green.
5. **Risk Register** — derived from `### Edge Cases` and `## Assumptions` (out-of-scope often
   maps to a deferred-risk row).
6. **Test Environment & Data** — tools, accounts, seed data, teardown.
7. **Open Questions** — every `[NEEDS CLARIFICATION]` left in spec.md.

**Idempotency rule:** when refreshing, regenerate sections 1, 2, 3, 6, 7 from spec/plan/tasks
state; preserve sections 4 and 5 if a QA-edited block exists, else regenerate.

### Phase B — Scaffold the higher-layer tests

For every gated item missing a QA-layer test, create a **failing** stub file labelled with the
spec item ID. Stubs are written first (TDD-style); QA fills them out after.

| Layer | When to scaffold |
|-------|------------------|
| `tests/integration/` | every P1 Acceptance Scenario (`US{n}-AS{m}`) without an integration test |
| `tests/e2e/` | each user story (top-level) without an E2E happy-path test |
| `tests/regression/` | any FR tied to a Risk-Register row marked "high blast radius" |
| `tests/perf/` | every buildable `SC-###` with a performance criterion |
| `tests/a11y/` | every user story marked `User-facing UI` in spec.md |

**File naming:** `tests/<layer>/<short-name>.<layer>.test.<ext>`, with `<short-name>` taken
from the spec item slug (e.g. `filter-persistence`). Framework selected from `plan.md`'s
Testing Strategy (Vitest, Playwright, k6, Pytest, etc.).

**Stub body:** Arrange/Act/Assert skeleton mapping Given/When/Then; header comment naming the
item ID and a TODO list of edge cases. The stub MUST fail when run (a single
`expect.fail("not implemented")` or equivalent), so the missing coverage is visible in CI.

**Never overwrites.** If a file at that path already exists, skip it and record "kept".

### Phase C — Seed `FEATURE_DIR/checklists/test.md`

A markdown checklist QA toggles during sign-off. `/speckit-implement` (when re-run, or in
future features) checks these before allowing implementation; here we seed it so it gates the
merge in `qareview`.

```markdown
# Test Checklist: <feature>

> Source: speckit.test.qaprep (after_implement hook). Tick these as the workflow progresses.

## Coverage
- [ ] Every P1 Acceptance Scenario has a unit/contract test (verified by tasksaudit)
- [ ] Every P1 Acceptance Scenario has an integration test
- [ ] Every user story has an E2E happy-path test
- [ ] Every buildable SC-### has a perf test
- [ ] Every user-facing UI story has an a11y test

## Quality
- [ ] No stub-by-description tasks remain in tasks.md
- [ ] All integration/E2E tests pass locally
- [ ] Risk Register reviewed; mitigations linked

## Sign-off
- [ ] /speckit-analyze produced zero CRITICAL findings
- [ ] qareview produced zero Blocker findings
- [ ] Test plan peer-reviewed
```

When refreshing, **never uncheck** items QA has ticked; only add new rows for newly-applicable
gated items.

### Phase D — Report

```
SPECTEST QAPREP:
  test-plan.md: <created|refreshed> (12 items in matrix, 3 risks, 1 open question)
  scaffolds:    integration +4, e2e +2, perf +1, a11y +1 (kept: 3)  (no overwrites)
  checklist:    <created|refreshed> (15 items, 4 ticked)
  → /speckit-analyze will run qareview and produce the consistency + quality verdict (pre-merge when run last).
```

## Rules

- **Mandatory hook, default writes** — `after_implement` fires with no flags; `--dry-run` is
  the only way to preview without writing.
- **Idempotent** — re-running refreshes `test-plan.md` and `checklists/test.md` in place
  (preserving QA-edited blocks and ticked items); only adds missing scaffolds; never
  duplicates.
- **Never overwrites existing tests** — scaffolding skips any file that already exists.
- **Higher layers only** — integration/E2E/regression/perf/a11y. Unit/contract was planned
  by `planaudit` and written by `/speckit-implement` itself.
- **Stubs are failing-on-purpose** — every scaffolded file fails on first run so missing
  coverage is visible in CI.
- **Spec is authority** — every test stub traces to a concrete `US{n}-AS{m}`, `FR-###`, or
  `SC-###`. Never invent behaviour.
- **Constitution may escalate** — extra mandatory layers add scaffolds; cannot silently
  remove QA layers (that requires `--advisory`).
- **Reports first, blocks never** — this command produces artefacts; it does not block the
  pipeline. The blocking gate is the `after_analyze` → `qareview` hook (formal pre-merge gate
  when `/speckit-analyze` is run as the final step).
