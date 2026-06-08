# speckit-test-extension -- Quality Built-In

A [Spec Kit](https://github.com/github/spec-kit) extension that bakes quality and testing
into the core SDD workflow as a built-in step at every lifecycle event. Hooks attach to
`/speckit-plan`, `/speckit-tasks`, `/speckit-analyze` (optional), and `/speckit-implement`
so quality work happens automatically and in the right order.

It is anchored on the **stock Spec Kit artefacts** (no custom spec format required) and
defers to your project `constitution.md` to decide how strict the gates are.

---

## Problem

Spec Kit's core workflow produces a rich `spec.md` (prioritized user stories with Acceptance
Scenarios, Functional Requirements, Success Criteria) and a `tasks.md` breakdown -- but the
testing layer is not enforced by the core commands themselves:

- Nothing in `/speckit-plan` decides how each spec item will be tested
- Nothing in `/speckit-tasks` guarantees a test task per testable spec item
- Tests get written from memory, not from spec -- traceability breaks
- There is no requirement-level measure of "which spec items are actually tested" before merge
- Pre-merge sign-off is ad-hoc and leaves no tracked record

This extension closes those gaps by hooking quality work into the core workflow at every
lifecycle event.

---

## Testable items -- the unit of traceability

Everything keys off the **stock `spec.md`**:

| Item | Where in spec.md | ID scheme |
|------|------------------|-----------|
| **Acceptance Scenario** | `### User Story N (Priority: Px)` -> `**Acceptance Scenarios**` (Given/When/Then) | `US{n}-AS{m}` (priority inherited from the story) |
| **Functional Requirement** | `### Functional Requirements` | `FR-###` |
| **Success Criterion** | `## Success Criteria` -> Measurable Outcomes | `SC-###` (only the *buildable* ones -- perf/security/availability -- are gated; business KPIs are not) |

Every generated test labels itself with the item ID, so the chain
`spec item -> plan.md Testing Strategy -> tasks.md test task -> test file -> review.md`
is checkable end to end.

---

## Commands (4 total -- all hook-driven)

No standalone invocation in the happy path. Each command fires automatically as a hook on a
core Spec Kit command.

The core Spec Kit workflow is
`/speckit-plan` -> `/speckit-tasks` -> `/speckit-analyze` (optional) -> `/speckit-implement`.
Because `/speckit-analyze` is skippable, every mandatory quality gate anchors to one of the
non-skippable commands (`/speckit-plan`, `/speckit-tasks`, `/speckit-implement`).

| Command | Hook | Mode | What it does |
|---------|------|------|--------------|
| `speckit.test.planaudit` | `after_plan` | mandatory | Appends a `## Testing Strategy` section to `plan.md` mapping every P1 Acceptance Scenario / Functional Requirement to concrete unit/contract test cases (TDD, fail-first) with test framework, file paths, and mocking boundaries inferred from `plan.md`. Idempotent. |
| `speckit.test.qaprep` | `after_tasks` | mandatory | Writes `FEATURE_DIR/test-plan.md` (traceability matrix, entry/exit criteria, risks), scaffolds the higher-layer tests (integration / E2E / regression / perf / a11y) as failing stubs labelled with spec item IDs, and seeds `FEATURE_DIR/checklists/test.md`. Runs early so artefacts exist before `/speckit-analyze` (if invoked) and `/speckit-implement`. Idempotent; never overwrites existing tests. |
| `speckit.test.tasksaudit` | `before_implement` | mandatory gate | Audit-only gate; BLOCKS `/speckit-implement` if any P1 spec item lacks a unit/contract test task in `tasks.md`. With `planaudit` in place, this should normally find zero gaps. |
| `speckit.test.qareview` | `after_analyze` (advisory) + `after_implement` (mandatory) | both | Reads workflow artefacts, computes requirement-level coverage (Strong/Medium/Weak/Stub/Missing), runs stub scan + traceability + constitution + checklist checks, emits a `Gate PASS or BLOCKED` verdict to chat **and** writes `FEATURE_DIR/review.md` (overwritten each run). The `after_analyze` firing is advisory (pre-implementation read of consistency and readiness); the `after_implement` firing is the **formal pre-merge gate** that includes real test results. |

> Command files are named `speckit.test.*.md`; Spec Kit surfaces them with dots -> hyphens,
> so they appear as `/speckit-test-*` in chat. You rarely invoke them manually -- the hooks
> handle it.

---

## The unified Quality-Built-In workflow

Follows the standard Spec Kit order. `/speckit-analyze` is optional and never gates implementation.

```
/speckit-constitution                  defines whether/which tests are mandatory
/speckit-specify  ->  /speckit-clarify  spec items: US{n}-AS{m}, FR-###, SC-###

/speckit-plan
   |
   +-- after_plan       *mandatory  ->  planaudit
                                        writes ## Testing Strategy to plan.md

/speckit-tasks
   |
   +-- after_tasks      *mandatory  ->  qaprep
                                        writes test-plan.md + scaffolds higher-layer tests
                                        + seeds checklists/test.md
                                        (so artefacts exist before analyze and implement)

/speckit-analyze                       (OPTIONAL in Spec Kit; skippable)
   |
   +-- after_analyze     advisory   ->  qareview
                                        refreshes review.md with a pre-impl read of
                                        consistency and readiness; NEVER gates implement

/speckit-implement
   |
   +-- before_implement *mandatory  ->  tasksaudit (gate, audit-only)
   |                                    BLOCKS if any P1 unit/contract task missing in tasks.md
   |
   +-- after_implement  *mandatory  ->  qareview
                                        refreshes review.md with the FORMAL pre-merge
                                        Gate PASS or BLOCKED verdict, including real test results
```

In one line:

```
/speckit-plan -> /speckit-tasks -> [/speckit-analyze] -> /speckit-implement
   planaudit       qaprep            qareview              tasksaudit (gate)
                                     (advisory)            + qareview (formal)
```

---

## Artefacts produced

| Path | Produced by | When | Lifecycle |
|------|-------------|------|-----------|
| `FEATURE_DIR/plan.md` (## Testing Strategy section) | `planaudit` | after `/speckit-plan` | Refreshed in place each run |
| `FEATURE_DIR/tasks.md` (test tasks) | `/speckit-tasks` (materializes Testing Strategy) | after `/speckit-tasks` | Edited additively |
| `FEATURE_DIR/test-plan.md` | `qaprep` | after `/speckit-tasks` | Refreshed in place; manual edits preserved between markers |
| `tests/integration/`, `tests/e2e/`, `tests/regression/`, `tests/perf/`, `tests/a11y/` stubs | `qaprep` | after `/speckit-tasks` | Created if absent; **never overwrites** existing files |
| `FEATURE_DIR/checklists/test.md` | `qaprep` | after `/speckit-tasks` | Refreshed; ticked rows preserved |
| `FEATURE_DIR/review.md` | `qareview` | after `/speckit-analyze` (advisory) and after `/speckit-implement` (formal) | **Overwritten** each run; `git log review.md` shows verdict evolution |

---

## The pre-merge gate

The formal pre-merge gate is whatever `qareview` writes to `FEATURE_DIR/review.md` **on the
`after_implement` run** -- the run that completes after `/speckit-implement` finishes, when
real test results are available. The file has a metadata header (feature path, timestamp,
verdict, mode) followed by the Blocker / Major / Minor tables and a single line:

```
SPECTEST QAREVIEW: 12 items, 7 Strong, 3 Blockers, 2 Majors, 1 Minor -- FAIL
```

CI can grep that line; the PR description can link to `review.md`. To refresh the formal
verdict after fixing a blocker, re-run `/speckit-implement` (the `after_implement` hook
will fire `qareview` again).

If the developer also runs `/speckit-analyze` before implementing, `review.md` gets an
earlier advisory verdict (consistency + readiness, no test results) -- useful as a sanity
check but never the formal gate.

---

## Worked example

A feature `specs/001-connect-hotel-filter/`.

**`spec.md`** (stock Spec Kit excerpt):

```markdown
### User Story 1 - Filter hotels by star rating (Priority: P1)

**Acceptance Scenarios**:
1. **Given** the hotel list is loaded, **When** the agent selects 3-star, **Then** only 3-star hotels show and the count updates.
2. **Given** 3-star is selected, **When** the agent adds 4-star, **Then** 3- and 4-star hotels show simultaneously.

### Functional Requirements
- **FR-001**: System MUST persist active filters across pagination.
- **FR-002**: System MUST update the result count to reflect the filtered set.

## Success Criteria
- **SC-001**: Filtered results render in under 500ms for 1000 hotels.
```

### After `/speckit-plan` (planaudit auto-runs)

`plan.md` gains a `## Testing Strategy` section:

```markdown
## Testing Strategy

> Generated at plan-time by speckit.test.planaudit (after_plan hook).

**Policy:** TDD mandatory (unit + contract, fail-first).
**Test framework:** Vitest
**Test root:** tests/

### Unit / Contract Test Cases -- User Story 1 (P1)

| Item    | Layer | Case                                                | Test file                                  |
|---------|-------|-----------------------------------------------------|--------------------------------------------|
| US1-AS1 | unit  | star-rating selection filters list + updates count  | tests/unit/star-filter.test.ts             |
| US1-AS2 | unit  | adding 4-star to 3-star selection shows both        | tests/unit/star-filter-multi.test.ts       |
| FR-001  | unit  | filter persists across pagination                   | tests/unit/filter-persistence.test.ts      |
| FR-002  | unit  | result-count reflects filtered set                  | tests/unit/result-count.test.ts            |
```

### After `/speckit-tasks` (qaprep auto-runs)

`/speckit-tasks` materializes the Testing Strategy cases into `tasks.md` as real test tasks.
Then `qaprep` fires on `after_tasks` and writes:

- `FEATURE_DIR/test-plan.md` with the full traceability matrix, risks, entry/exit criteria
- Failing-stub test files: `tests/integration/filter-persistence.integration.test.ts`,
  `tests/perf/search-latency.perf.test.ts` (for SC-001),
  `tests/a11y/star-filter.a11y.test.ts`
- `FEATURE_DIR/checklists/test.md` seeded with gated rows

All higher-layer artefacts are now in place **before** `/speckit-analyze` or `/speckit-implement` runs.

### `/speckit-analyze` -- OPTIONAL (qareview advisory)

If the developer chooses to analyze, the `after_analyze` hook fires `qareview` in advisory
mode. It reads spec/plan/tasks/test-plan/checklist artefacts and writes an early read of
consistency + readiness to `FEATURE_DIR/review.md`:

```
SPECTEST QAREVIEW: 4 items, 4 planned, 0 stubs run yet, 0 Blockers -- ADVISORY PASS
```

This run cannot include real test results (nothing has been implemented yet). It never
gates implementation.

### Before `/speckit-implement` (tasksaudit gate)

Mandatory audit-only gate. `PASS` (proceed) or `BLOCKED` with the exact task lines to add.

### After `/speckit-implement` (qareview formal verdict)

Implementation writes the unit tests first (they fail), implements until green, then runs
the qaprep-scaffolded integration / E2E / perf / a11y tests. Then `qareview` fires on
`after_implement` with real test results in hand and refreshes `FEATURE_DIR/review.md`
with the **formal pre-merge verdict**:

```markdown
# Consistency + Quality Verdict -- 001-connect-hotel-filter

| Field   | Value                          |
|---------|--------------------------------|
| Run at  | 2026-06-08T14:32:11Z           |
| Verdict | **Gate: BLOCKED**              |

### Blockers
| ID | Where  | Issue                                                |
|----|--------|------------------------------------------------------|
| B1 | SC-001 | Perf test is still the qaprep failing stub          |

SPECTEST QAREVIEW: 4 items, 3 Strong, 1 Blocker -- FAIL
```

To clear the blocker: implement the stubbed perf test, then **re-run `/speckit-implement`**
(its `after_implement` hook fires `qareview` again with the new test results;
`review.md` refreshes to `Gate: PASS`).

---

## Installation

```bash
# From a Spec Kit project root, after `specify init`
specify extension add --from https://github.com/NDViet/speckit-test-extension/archive/refs/heads/master.zip
```

Or from a local folder (offline / development):

```bash
specify extension add --dev /path/to/speckit-test-extension
```

Requires Spec Kit >= 0.8.0.

---

## Hooks

Registered in `extension.yml`, dispatched via `.specify/extensions.yml`:

| Event | Command | Mode | Behaviour |
|-------|---------|------|-----------|
| `after_plan` | `planaudit` | **mandatory** | Appends Testing Strategy section to `plan.md` |
| `after_tasks` | `qaprep` | **mandatory** | Writes `test-plan.md`, scaffolds higher-layer tests as failing stubs, seeds `checklists/test.md` |
| `before_implement` | `tasksaudit` | **mandatory** | Gate (audit-only); BLOCKS if any P1 unit/contract task missing in `tasks.md` |
| `after_analyze` | `qareview` | advisory | Refreshes `review.md` with a pre-implementation read of consistency and readiness; never gates implement |
| `after_implement` | `qareview` | **mandatory** | Refreshes `review.md` with the **formal pre-merge** `Gate PASS or BLOCKED` verdict, including real test results |

---

## Key conventions

| Convention | Detail |
|------------|--------|
| **Feature directory** | Resolved via `.specify/scripts/powershell/check-prerequisites.ps1 -Json` (`FEATURE_DIR`) |
| **Testable items** | `US{n}-AS{m}`, `FR-###`, buildable `SC-###` -- drawn from stock `spec.md` |
| **Test tasks** | Identified by a `### Tests for User Story N` subsection **or** a test path -- not by `[P]` |
| **`[P]` marker** | Means *parallelizable* (Spec Kit semantics); never used to identify tests |
| **`[US#]` label** | Maps a task to its user story |
| **Tests mandatory?** | Unit/contract (TDD) tests are mandatory by default. `constitution.md` can escalate which layers block; `--advisory` is an explicit opt-out |
| **Verdict file** | `FEATURE_DIR/review.md` -- written by `qareview` on `after_analyze` (advisory) and `after_implement` (formal). Overwritten each run |
| **Test plan** | `FEATURE_DIR/test-plan.md` (written by `qaprep` on `after_tasks`) |
| **Checklist** | `FEATURE_DIR/checklists/test.md` (seeded by `qaprep` on `after_tasks`) |
| **Stub detection** | `.skip` / `.todo` / `xit` / `xdescribe`, `@pytest.mark.skip`, `throw new Error('TODO')`, `raise NotImplementedError`, `expect(true).toBe(true)`, bare `toBeTruthy()` / `assert True`, empty bodies, unmodified qaprep stubs |
| **Confidence rating** | Strong (test cites item ID), Medium (keyword match), Weak (file maps to story only), Stub (0%) |
| **Out of scope** | Read from `spec.md` -> `## Assumptions` (Spec Kit has no `## Out of scope` heading) |

---

## License

MIT
