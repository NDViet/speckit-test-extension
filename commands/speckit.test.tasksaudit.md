---
description: "Pre-implementation gate: verify every P1 spec item (Acceptance Scenarios, FR-###) has a UNIT/CONTRACT (TDD) test task in tasks.md before /speckit-implement. Audits by default; with --write it adds the missing test tasks in place so they become part of implementation."
argument-hint: "[--write] [--advisory] [--require integration,e2e] [--story US1]"
---

# Test Task Audit — Pre-Implementation Gate (Unit / TDD)

**Runs automatically as the advisory `after_tasks` hook and the mandatory `before_implement`
hook** of the core Spec Kit workflow. The unit/contract test plan is decided earlier (by
`planaudit` during `/speckit-plan`); this command verifies that `/speckit-tasks` materialized
every case as a real test task before `/speckit-implement` runs. Higher-layer test artefacts
(integration / E2E / perf / a11y) are produced by `qaprep` after `/speckit-implement`; their
absence is advisory here.

**Default is audit-only (read-only).** Following TDD, every P1 testable item must have a
**unit or contract test task in `tasks.md` (written first, to fail)** before implementation
code is written. This command:
1. **Audits (default)** — finds P1 Acceptance Scenarios / Functional Requirements with no
   unit/contract test task, reports `BLOCKED`, and prints the exact task lines needed to close
   the gate. **It does not modify any file in this mode.**
2. **Completes (only with `--write`)** — a developer runs `/speckit-test-tasksaudit --write` to
   insert the missing unit/contract test tasks into `tasks.md` in place (under the right
   user-story Tests subsection, TDD fail-first), reviews the additions, then proceeds.

**Why `--write` is opt-in, not automatic:** the `before_implement` hook fires this command with
no arguments (Spec Kit hooks pass no flags), so by default it **audits and blocks** rather than
silently editing `tasks.md` with generated task lines the developer has not seen. Writing is a
deliberate, reviewed action — never an unattended side effect of the hook.

The heavier test layers — integration, E2E, regression, performance, accessibility, manual —
are **prepared by `qaprep` after `/speckit-implement`** and tracked in
`FEATURE_DIR/test-plan.md`. This command never writes those layers; their absence here is
**advisory** (unless the constitution escalates them, or you pass `--require`).

**Write scope (`--write` only):** the single file this command may modify is `tasks.md`, and
only by *adding* unit/contract test tasks. It never edits `spec.md`, `plan.md`, `test-plan.md`,
or any test code, and never deletes or renumbers existing tasks.

> ⚠️ After `--write`, **do NOT re-run `/speckit-tasks`** — it regenerates `tasks.md` from
> scratch and would silently discard the test tasks just added. Edit `tasks.md` in place from
> here on.

## User Input

```text
$ARGUMENTS
```

The user may specify:
- `--write` — apply the fix: add the missing unit/contract test tasks to `tasks.md` (default is audit-only, no writes)
- `--advisory` — downgrade the unit gate to a warning; never writes (only if the team explicitly opts out of TDD)
- `--require integration,e2e` — also require named layers at this gate (and add them under `--write`)
- `--story US1` — limit to one user story

## Prerequisites

1. Resolve the feature directory. From repo root:
   `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`
   Parse `FEATURE_DIR` and `AVAILABLE_DOCS`. Fall back to `specs/*/spec.md` if unavailable
   (ask the user if more than one exists).
2. Read `FEATURE_DIR/spec.md` fully.
3. Read `FEATURE_DIR/tasks.md` fully.
4. Read `FEATURE_DIR/plan.md` if present.
5. Read `.specify/memory/constitution.md` — determine the gate policy (see Step 1).

## Outline

### Step 1 — Determine the Gate Policy

- **Default: Unit Gate ON.** Every P1 testable item must have a unit or contract test task
  planned. This is the team's development standard (TDD / fail-first).
- **Constitution escalation.** If a principle mandates more (e.g., "Integration Testing" for
  contract changes, or a NON-NEGOTIABLE Test-First rule covering all layers), add those layers
  to the blocking set. State which principle and which layers.
- **`--require <layers>`** adds the named layers to the blocking set for this run.
- **`--advisory`** downgrades the unit gate to a warning (record that TDD was waived and by whom).

State the active policy and its source at the top of the report.

### Step 2 — Extract the Testable-Item Inventory from spec.md

| Source in spec.md | ID scheme | Notes |
|-------------------|-----------|-------|
| `### User Story N (Priority: Px)` → `**Acceptance Scenarios**` | `US{N}-AS{M}` | **Gated.** Priority inherited from the story (P1/P2/P3). |
| `### Functional Requirements` | `FR-###` | **Gated.** Each `**FR-###**` line. |
| `## Success Criteria` (buildable only) | `SC-###` | **Not gated by default** — perf/security/availability criteria are higher-layer (post-implementation, in test-plan.md). Reported as advisory; exclude business KPIs entirely. |
| `### Edge Cases` | — | Coverage candidates; not gated. |

The unit gate binds on **P1 Acceptance Scenarios and Functional Requirements** — the
behaviour a developer can cover with a fail-first unit/contract test. **Success Criteria
(`SC-###`) are advisory at this gate**: perf/security/availability are higher-layer concerns
prepared after implementation by `qaprep`, so they belong in `test-plan.md`, not the pre-implement gate
(unless the constitution or `--require` escalates them). Lower-priority items are reported
but not blocking unless the constitution says otherwise.

### Step 3 — Extract & Classify Test Tasks from tasks.md (do NOT use `[P]` for this)

Task format is `- [ ] T0NN [P?] [US#?] Description with path`.
- `[P]` = **parallelizable** — record only; it does **not** mark a test task.
- `[US#]` maps the task to a user story; `[X]` = done.

Classify a task as a **test task** if it sits under a `### Tests for User Story N` subsection
**or** its description denotes a test. Then assign each test task a **layer** from its
path/wording:

| Layer | Signals |
|-------|---------|
| **unit** | `tests/unit/`, `*.test.*`/`*.spec.*`/`test_*` on a function/component, "unit test" |
| **contract** | `tests/contract/`, "contract test", schema/API contract |
| integration | `tests/integration/`, "integration test", cross-layer/journey |
| e2e | `tests/e2e/`, Playwright/Cypress, "end-to-end" |
| perf | `tests/perf/`, k6/load/latency, ties to an SC |
| a11y | axe/jest-axe, "keyboard"/"ARIA"/"screen reader" |
| manual | "manual"/"exploratory" |

**unit** and **contract** are the developer-level, fail-first layers that satisfy the gate.

### Step 4 — Apply the Gate

For each **P1 Acceptance Scenario and Functional Requirement** (not SC — see Step 2):

| Check | Result |
|-------|--------|
| A unit **or** contract test task is planned for it (TDD) | ✅ / ❌ **Blocker** |
| That task names the specific behaviour (not "add tests") | ✅ / ⚠️ Major |
| It is not a stub-by-description ("Add tests", no path) | ✅ / ❌ |
| Higher layers (integration/e2e/perf/a11y) planned | ℹ️ Advisory — handled later by `qaprep` in test-plan.md |
| Layers in the escalated blocking set are planned | ✅ / ❌ Blocker |

For **`SC-###`** items: report whether a perf/security test is planned, but mark it
`ℹ️ Advisory (QA, post-impl)` — never a Blocker unless the constitution or `--require` escalates it.

A stub-by-description task counts as no task.

### Step 5 — Report the Gate, and (only with `--write`) Complete It

**Default (no `--write`): audit only.** Report `BLOCKED` listing every gated item missing a
unit/contract task, and print the exact task lines that would close the gate. **Modify no file.**
This is the mode the `before_implement` hook runs, so the gate audits and blocks rather than
mutating `tasks.md` unattended.

**With `--write`: complete the gate.** A developer runs `/speckit-test-tasksaudit --write` to
**edit `tasks.md` in place**, adding a unit or contract test task for every gated item missing
in Step 4, then reviews the additions before implementing.

Insertion rules (apply only under `--write`; in audit mode these describe what *would* be added):
- **Where**: under the owning user story's `### Tests for User Story N` subsection. If that
  subsection does not exist, create it at the top of that story's phase (before its
  Implementation subsection) with the standard TDD note:
  `> NOTE: Write these tests FIRST, ensure they FAIL before implementation.`
- **ID**: assign the next free sequential ID — `T{max existing T-number + 1}`, incrementing per
  task added. **Never renumber existing tasks** (it would break references).
- **Format**: stock Spec Kit format `- [ ] T0NN [P] [US#] <description with exact test path>`,
  e.g. `- [ ] T015 [P] [US1] Unit test for filter persistence across pagination (FR-001) in tests/unit/filter-persistence.test.ts`.
  Use `[P]` (separate test files are parallel-safe), the correct `[US#]`, the item ID in the
  description, and a concrete path inferred from plan.md's structure and existing test layout.
- **Layer**: add a **unit** task by default; add **contract** instead when the item is an API/schema
  contract. With `--require`, also add the named higher-layer tasks.
- **Idempotent**: if a non-stub unit/contract task already covers the item, add nothing for it.
  Re-running `--write` after a pass adds nothing.
- **Stubs**: a stub-by-description task (e.g. `Add tests`) is *flagged for the developer to remove*
  but is **not** auto-deleted (deletion is destructive); add the proper concrete task alongside it.

After a `--write` run, re-check Step 4 against the updated `tasks.md` and report `PASS`, listing
exactly what was added. Remind the developer **not to re-run `/speckit-tasks`** (it would discard
the additions).

### Step 6 — Gate Report

**Default audit example (gaps found — BLOCKED, nothing written):**
```markdown
## Pre-Implementation Gate — BLOCKED ❌

Feature: specs/001-connect-hotel-filter/
Policy: Unit Gate ON (default)
P1 gated items: 4 (2 scenarios, 2 FR) | Unit/contract present: 2 | Gaps: 2 | Stubs: 1

### ❌ Missing unit/contract test task (add these to close the gate)
| Item | Task to add |
|------|-------------|
| FR-001 | `- [ ] T015 [P] [US1] Unit test for filter persistence across pagination (FR-001) in tests/unit/filter-persistence.test.ts` |
| FR-002 | `- [ ] T016 [P] [US1] Unit test for result-count calculation (FR-002) in tests/unit/result-count.test.ts` |

### ⚠️ Should fix
| Task | Issue |
|------|-------|
| T011 [US1] Add tests | Stub-by-description — names no behaviour/path |

### ℹ️ Advisory — QA layers (defer to test-plan.md, after implementation)
- SC-001 has no perf test — performance is prepared after implementation by `qaprep`.

Gate: BLOCKED — /speckit-implement must not proceed until these unit/contract tasks exist.
Run `/speckit-test-tasksaudit --write` to add them to tasks.md (then review), or add them by hand.
```

**`--write` example (developer applies the fix):**
```markdown
## Pre-Implementation Gate — COMPLETED ✅ (--write)

Feature: specs/001-connect-hotel-filter/
Before: 2 covered, 2 gaps, 1 stub  →  After: 4 covered, 0 gaps

### ✍️ Added to tasks.md (unit, TDD fail-first)
| Item | Task added |
|------|-----------|
| FR-001 | `- [ ] T015 [P] [US1] Unit test for filter persistence across pagination (FR-001) in tests/unit/filter-persistence.test.ts` |
| FR-002 | `- [ ] T016 [P] [US1] Unit test for result-count calculation (FR-002) in tests/unit/result-count.test.ts` |

### ⚠️ Flagged for you to remove (not auto-deleted)
| Task | Issue |
|------|-------|
| T011 [US1] Add tests | Stub-by-description — superseded by T015/T016; delete it |

Gate: PASS — every P1 scenario/FR now has a fail-first unit test task. Review the additions and
remove the flagged stub, then run /speckit-implement (it writes these tests first, they fail, then
implements to green). Do NOT re-run /speckit-tasks — it would discard these additions.
```

**Already-passing:** if no gaps are found, report
`Gate: PASS — all P1 scenarios/FRs already have unit/contract tests; no changes needed.`

Under `--advisory`, never write; render the BLOCKED tables but label unit gaps
`⚠️ Advisory (TDD waived)` and end with `Gate: PASS (advisory)`.

### Step 7 — CI-Friendly One-Line Summary

Default audit (gaps found):
```
SPECTEST AUDIT: 4 gated items, 2 with unit/contract tests, 2 gaps (FR-001, FR-002), 1 stub — FAIL
```
After `--write`:
```
SPECTEST AUDIT: 4 gated items, 2 present + 2 added (FR-001, FR-002) = 4, 1 stub flagged — PASS (written)
```
Nothing to do:
```
SPECTEST AUDIT: 4 gated items, 4 with unit/contract tests, 0 gaps, 0 stubs — PASS
```

## Rules

- **Audit-only by default; writes `tasks.md` only with `--write`** — without `--write` (and as
  fired by the `before_implement` hook) the command modifies nothing; it reports `BLOCKED` and
  prints the task lines to add. `--write` adds them additively (never editing `spec.md`,
  `plan.md`, `test-plan.md`, or test code, and never deleting or renumbering existing tasks).
- **Never silently mutate from the hook** — the hook passes no flags, so it always runs
  audit-only; writing is a deliberate developer action that is reviewed before implementation.
- **After `--write`, do NOT re-run `/speckit-tasks`** — it regenerates `tasks.md` and discards
  the added test tasks; say so in the report.
- **The gate is unit/contract (TDD), and it is mandatory by default** — a P1 Acceptance
  Scenario or Functional Requirement with no unit or contract test task is a **Blocker**; close
  it with `--write` or by hand (or, under `--advisory`, record the waiver).
- **Success Criteria are not gated** — `SC-###` (perf/security/availability) are higher
  layers; report them as advisory, never as a gate Blocker, unless escalated.
- **Higher layers are post-implementation** — integration/E2E/regression/perf/a11y are
  advisory at this gate; their home is `FEATURE_DIR/test-plan.md`, prepared after implement.
  Do not block on them unless the constitution or `--require` escalates them.
- **`[P]` is parallelism, not tests** — classify test tasks by the Tests subsection / test path, never by `[P]`.
- **No invented tags** — never flag a task for lacking `[AUTO]/[MANUAL]/[BOTH]`; stock tasks don't use them. Infer the layer yourself.
- **TDD intent** — added unit/contract test tasks are written first and must fail before implementation; place them in the story's Tests subsection with the fail-first note.
- **Additive & idempotent** — only ever add tasks; skip items already covered by a non-stub unit/contract task; re-running after a pass changes nothing.
- **Never renumber** — assign new IDs continuing from the highest existing T-number; do not shift existing task IDs.
- **Stubs flagged, not deleted** — a stub-by-description task does not satisfy the gate; add the proper task and flag the stub for the developer to remove (no auto-delete).
- **Stub-by-description = no task** — a task naming no behaviour and no path does not satisfy the gate.
- **SC excluded, KPIs excluded** — Success Criteria are advisory at this gate (not a Blocker); business KPIs are not test items at all. Never count either toward the unit gate.
- **Constitution is authority** — it may escalate which layers block; it cannot silently remove the unit gate (that requires explicit `--advisory`).
- **Gate verdict explicit** — always emit `Gate: PASS` / `Gate: BLOCKED` and the `SPECTEST AUDIT:` line.
- **Hook context** — invoked as the mandatory `before_implement` hook (no flags), the command runs **audit-only**: a `BLOCKED` verdict means `/speckit-implement` must stop until the developer adds the unit/contract tasks (via `/speckit-test-tasksaudit --write` or by hand). The hook never writes `tasks.md` itself.
