# speckit-test-extension -- Quality Built-In

A [Spec Kit](https://github.com/github/spec-kit) extension that bakes quality and testing
into the core SDD workflow as a built-in step at every lifecycle event, not as a separate
role or PR-time afterthought. Hooks attach to `/speckit-plan`, `/speckit-tasks`,
`/speckit-implement`, and `/speckit-analyze` so the work happens automatically.

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

| Command | Hook | Mode | What it does |
|---------|------|------|--------------|
| `speckit.test.planaudit` | `after_plan` | mandatory | Appends a `## Testing Strategy` section to `plan.md` mapping every P1 Acceptance Scenario / Functional Requirement to concrete unit/contract test cases (TDD, fail-first) with test framework, file paths, and mocking boundaries inferred from `plan.md`. Idempotent. |
| `speckit.test.tasksaudit` | `after_tasks` (advisory) + `before_implement` (mandatory gate) | both | Verifies `tasks.md` materialized every case from the Testing Strategy as a real test task. Audit-only by default; the `before_implement` hook BLOCKS if any P1 item is missing its unit/contract task. With `planaudit` in place, this should normally find zero gaps. |
| `speckit.test.qaprep` | `after_implement` | mandatory | Writes `FEATURE_DIR/test-plan.md` (traceability matrix, entry/exit criteria, risks), scaffolds the higher-layer tests (integration / E2E / regression / perf / a11y) as failing stubs labelled with spec item IDs, and seeds `FEATURE_DIR/checklists/test.md`. Idempotent; never overwrites existing tests. |
| `speckit.test.qareview` | `after_analyze` | mandatory | Reads `/speckit-analyze`'s report plus workflow artefacts, computes requirement-level coverage (Strong/Medium/Weak/Stub/Missing), runs stub scan + traceability + constitution + checklist checks, emits a `Gate PASS or BLOCKED` verdict to chat **and** writes `FEATURE_DIR/review.md` (overwritten each run) so every invocation leaves a tracked record. Runnable anytime; the run after `/speckit-implement` is the formal pre-merge gate. |

> Command files are named `speckit.test.*.md`; Spec Kit surfaces them with dots -> hyphens,
> so they appear as `/speckit-test-*` in chat. You rarely invoke them manually -- the hooks
> handle it.

---

## The unified Quality-Built-In workflow

```
/speckit-constitution                  defines whether/which tests are mandatory
/speckit-specify  ->  /speckit-clarify  spec items: US{n}-AS{m}, FR-###, SC-###
/speckit-plan
   └─ after_plan       *mandatory  ->  planaudit
                                       writes ## Testing Strategy to plan.md
/speckit-tasks
   └─ after_tasks       advisory   ->  tasksaudit
                                       confirms test tasks match the Testing Strategy
/speckit-implement
   ├─ before_implement *mandatory  ->  tasksaudit (gate, audit-only)
   │                                   BLOCKS if any P1 unit/contract task missing
   └─ after_implement  *mandatory  ->  qaprep
                                       writes test-plan.md + scaffolds + checklist
/speckit-analyze
   └─ after_analyze    *mandatory  ->  qareview
                                       writes review.md with Gate PASS or BLOCKED
                                       (anytime; the latest after /speckit-implement
                                        is the formal pre-merge gate)
```

In one line, commands only -- a single linear workflow with no role split:

```
/speckit-specify -> /speckit-clarify -> /speckit-plan -> /speckit-tasks -> /speckit-implement -> /speckit-analyze
                                            |                  |                  |                   |
                                            v                  v                  v                   v
                                       planaudit          tasksaudit          qaprep             qareview
                                       (Testing           (gate +             (test-plan.md      (review.md
                                        Strategy           verify)             + scaffolds        + Gate
                                        -> plan.md)                            + checklist)        verdict)
```

---

## Artefacts produced

| Path | Produced by | When | Lifecycle |
|------|-------------|------|-----------|
| `FEATURE_DIR/plan.md` (## Testing Strategy section) | `planaudit` | after `/speckit-plan` | Refreshed in place each run |
| `FEATURE_DIR/tasks.md` (test tasks) | `/speckit-tasks` (materializes Testing Strategy); `tasksaudit --write` may add missing ones manually | after `/speckit-tasks` | Edited additively |
| `FEATURE_DIR/test-plan.md` | `qaprep` | after `/speckit-implement` | Refreshed in place; manual edits preserved between markers |
| `tests/integration/`, `tests/e2e/`, `tests/regression/`, `tests/perf/`, `tests/a11y/` stubs | `qaprep` | after `/speckit-implement` | Created if absent; **never overwrites** existing files |
| `FEATURE_DIR/checklists/test.md` | `qaprep` | after `/speckit-implement` | Refreshed; ticked rows preserved |
| `FEATURE_DIR/review.md` | `qareview` | after every `/speckit-analyze` | **Overwritten** each run; `git log review.md` shows verdict evolution |

---

## The pre-merge gate

The formal pre-merge gate is whatever `qareview` writes to `FEATURE_DIR/review.md` on the run
that follows `/speckit-implement`. The file has a metadata header (feature path, timestamp,
verdict, mode) followed by the Blocker / Major / Minor tables and a single line:

```
SPECTEST QAREVIEW: 12 items, 7 Strong, 3 Blockers, 2 Majors, 1 Minor -- FAIL
```

CI can grep that line; the PR description can link to `review.md`. Rerun `/speckit-analyze`
anytime to refresh the verdict.

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

| Item | Layer | Case | Test file |
|------|-------|------|-----------|
| US1-AS1 | unit | star-rating selection filters list and updates count | tests/unit/star-filter.test.ts |
| US1-AS2 | unit | adding 4-star to 3-star selection shows both | tests/unit/star-filter-multi.test.ts |
| FR-001 | unit | filter persists across pagination | tests/unit/filter-persistence.test.ts |
| FR-002 | unit | result-count reflects filtered set | tests/unit/result-count.test.ts |
```

### After `/speckit-tasks` (tasksaudit advisory verifies)

`tasks.md` has materialized those cases as test tasks. The advisory `after_tasks` hook
reports `PASS` (zero gaps) because the Testing Strategy was already locked in plan.md.

### Before `/speckit-implement` (tasksaudit gate)

Mandatory gate runs audit-only. Either `PASS` (proceed) or `BLOCKED` with the exact task
lines to add.

### After `/speckit-implement` (qaprep auto-runs)

Implementation writes T010/T015/T016 first (they fail), then implements until green.
`qaprep` writes `test-plan.md`, scaffolds `tests/integration/filter-persistence.integration.test.ts`
and `tests/perf/search-latency.perf.test.ts` (both failing stubs for SC-001), and seeds
`checklists/test.md`.

### `/speckit-analyze` (qareview auto-runs)

Reads the analyze report plus all artefacts, writes the verdict to `FEATURE_DIR/review.md`:

```markdown
# Consistency + Quality Verdict -- 001-connect-hotel-filter

| Field        | Value                                         |
|--------------|-----------------------------------------------|
| Run at       | 2026-06-08T14:32:11Z                          |
| Verdict      | **Gate: BLOCKED**                             |

### Blockers
| ID | Where  | Issue                                                            |
|----|--------|------------------------------------------------------------------|
| B1 | SC-001 | Perf test is still the qaprep failing stub                       |

SPECTEST QAREVIEW: 4 items, 3 Strong, 1 Blocker -- FAIL
```

Implement the stubbed perf test, rerun `/speckit-analyze`, `review.md` refreshes to
`Gate: PASS`.

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

## Key conventions

| Convention | Detail |
|------------|--------|
| **Feature directory** | Resolved via `.specify/scripts/powershell/check-prerequisites.ps1 -Json` (`FEATURE_DIR`) |
| **Testable items** | `US{n}-AS{m}`, `FR-###`, buildable `SC-###` -- drawn from stock `spec.md` |
| **Test tasks** | Identified by a `### Tests for User Story N` subsection **or** a test path -- not by `[P]` |
| **`[P]` marker** | Means *parallelizable* (Spec Kit semantics); never used to identify tests |
| **`[US#]` label** | Maps a task to its user story |
| **Tests mandatory?** | Unit/contract (TDD) tests are mandatory by default. `constitution.md` can escalate which layers block; `--advisory` is an explicit opt-out |
| **Verdict file** | `FEATURE_DIR/review.md` -- overwritten on each `/speckit-analyze` run |
| **Test plan** | `FEATURE_DIR/test-plan.md` (written by `qaprep` after `/speckit-implement`) |
| **Checklist** | `FEATURE_DIR/checklists/test.md` (seeded by `qaprep`) |
| **Stub detection** | `.skip` / `.todo` / `xit` / `xdescribe`, `@pytest.mark.skip`, `throw new Error('TODO')`, `raise NotImplementedError`, `expect(true).toBe(true)`, bare `toBeTruthy()` / `assert True`, empty bodies, unmodified qaprep stubs |
| **Confidence rating** | Strong (test cites item ID), Medium (keyword match), Weak (file maps to story only), Stub (0%) |
| **Out of scope** | Read from `spec.md` -> `## Assumptions` (Spec Kit has no `## Out of scope` heading) |

---

## Hooks

Registered in `extension.yml`, dispatched via `.specify/extensions.yml`. **All five hooks
are workflow-internal** -- there is no separate role lane:

| Event | Command | Mode | Behaviour |
|-------|---------|------|-----------|
| `after_plan` | `planaudit` | **mandatory** | Appends Testing Strategy section to `plan.md` |
| `after_tasks` | `tasksaudit` | optional | Advisory verify; should find zero gaps when planaudit ran |
| `before_implement` | `tasksaudit` | **mandatory** | Gate (audit-only); BLOCKS if any P1 unit/contract task missing |
| `after_implement` | `qaprep` | **mandatory** | Writes `test-plan.md`, scaffolds higher-layer tests, seeds checklist |
| `after_analyze` | `qareview` | **mandatory** | Writes `review.md` wi
