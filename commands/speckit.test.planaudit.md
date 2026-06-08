---
description: "Built-in unit-test strategy step for /speckit-plan. Runs automatically as an after_plan hook and appends a '## Testing Strategy' section to plan.md mapping every P1 Acceptance Scenario (US{n}-AS{m}) and Functional Requirement (FR-###) to concrete unit-test cases the developer must write first (TDD)."
argument-hint: "[--write] [--dry-run] [--story US1]"
---

# Plan-time Unit Test Strategy — built-in step of `/speckit-plan`

**Runs automatically as the mandatory `after_plan` hook of `/speckit-plan`.** This is
the built-in replacement for running `/speckit-test-tasksaudit --write` separately. Instead of
auditing test tasks *after* `/speckit-tasks` has already generated them, the unit-test plan
is decided **at planning time** and recorded in `plan.md`. `/speckit-tasks` then naturally
materializes those cases as test tasks, and `/speckit-test-tasksaudit` runs a thin verification.

**Default behaviour: write the section.** Because this command is invoked as the mandatory
`after_plan` hook (Spec Kit hooks pass no flags), default mode is `--write`: append the
`## Testing Strategy` section to `plan.md` if it is missing, or refresh it in place if it
already exists. `--dry-run` previews without modifying `plan.md` (useful when invoking the
command by hand). This is the **one place** in the workflow where the unit-test plan is
authored; downstream commands consume it.

**Write scope:** the only file this command may modify is `plan.md`, and only by adding or
refreshing the `## Testing Strategy` section. It never edits `spec.md`, `tasks.md`,
`test-plan.md`, or any test code. It never re-orders existing plan.md sections.

> ⚠️ This step covers **unit and contract tests only** (the developer-level, TDD fail-first
> layer). Integration / E2E / regression / perf / a11y belong to QA and are planned in
> `FEATURE_DIR/test-plan.md` after implementation, not here.

## User Input

```text
$ARGUMENTS
```

The user (or hook) may specify:
- _(no flags)_ — default; writes the Testing Strategy section to `plan.md`
- `--dry-run` — print what would be written; modify nothing
- `--write` — explicit; same as default
- `--story US1` — limit case generation to one user story
- `--advisory` — append the section but mark it `Advisory (TDD waived)` (only when the team explicitly opts out of TDD)

## Prerequisites

1. Resolve the feature directory. From repo root:
   `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -IncludePlan`
   Parse `FEATURE_DIR`. Fall back to `specs/*/spec.md` if unavailable (ask the user if more
   than one match).
2. Read `FEATURE_DIR/spec.md` fully — Acceptance Scenarios, Functional Requirements, Success
   Criteria, Edge Cases.
3. Read `FEATURE_DIR/plan.md` fully — language, framework, test framework, file structure.
4. Read `.specify/memory/constitution.md` — determine TDD policy (mandatory / waived / extra
   layers required).
5. **Do not** read `tasks.md` — `/speckit-tasks` has not run yet at this point.

## Outline

### Step 1 — Determine the Testing Policy

- **Default: TDD mandatory.** Every P1 Acceptance Scenario and Functional Requirement must
  have at least one unit or contract test case in the Testing Strategy section.
- **Constitution escalation.** If a principle mandates more (e.g., a NON-NEGOTIABLE Test-First
  rule covering integration), include those layers — but only as planning entries; the gate
  remains unit/contract.
- **`--advisory`** records the section with a "TDD waived" banner; do not block.

State the active policy at the top of the inserted section.

### Step 2 — Extract Testable Items from spec.md

| Source | ID scheme | In scope here? |
|--------|-----------|----------------|
| `### User Story N (Priority: Px)` → `**Acceptance Scenarios**` | `US{N}-AS{M}` | **Yes** for P1 (gated). P2/P3 listed as advisory. |
| `### Functional Requirements` | `FR-###` | **Yes** (gated). |
| `## Success Criteria` (buildable perf/security/availability) | `SC-###` | Advisory only — deferred to test-plan.md (written by `qaprep` after implementation). |
| `### Edge Cases` | — | Listed as case candidates under their owning FR/AS. |

### Step 3 — Infer Test Framework and Paths from plan.md

From `plan.md`:
- **Language / framework** → choose the conventional test framework (`jest` / `vitest` for
  TypeScript, `pytest` for Python, `go test` for Go, `xUnit` for .NET, etc.) unless plan.md
  declares one.
- **Source layout** → derive test paths (`tests/unit/<file>.test.ts`, `tests/contract/...`,
  `<pkg>_test.go`, etc.).
- If plan.md does not yet specify a test framework, **propose one** in the Testing Strategy
  section and mark it `NEEDS CONFIRMATION` so the developer locks it in before
  `/speckit-tasks`.

### Step 4 — Generate Unit / Contract Test Cases

For each in-scope item, generate one or more test cases. Each case has:

| Field | How to fill |
|-------|-------------|
| Item ID | `US{N}-AS{M}` or `FR-###` |
| Layer | `unit` by default; `contract` if the item describes an API/schema contract |
| Case name | Short imperative describing the behaviour under test |
| Arrange / Act / Assert | Map Given/When/Then directly when the item is an Acceptance Scenario; otherwise derive from the FR text |
| Test file path | Concrete path inferred from Step 3 |
| Mocking boundary | What is real vs. stubbed (DB, network, time, randomness) |
| Edge cases | Pull from `### Edge Cases` in spec.md that apply to this item |

**Coverage rule:** every P1 AS/FR must yield **at least one** happy-path case plus **at least
one** error/edge case (when an edge case applies).

### Step 5 — Render the `## Testing Strategy` Section

Append (or refresh) the following block at the end of `plan.md`. If a `## Testing Strategy`
heading already exists, replace its contents between the heading and the next `## ` heading
— do not duplicate.

```markdown
## Testing Strategy

> Generated at plan-time by `speckit.test.planaudit` (after_plan hook). This section is the
> source of truth for unit/contract test cases. `/speckit-tasks` materializes each case as a
> test task; `/speckit-test-tasksaudit` verifies the mapping before `/speckit-implement`.

**Policy:** TDD mandatory (unit + contract, fail-first).
**Test framework:** <inferred from plan.md, e.g. Vitest> <NEEDS CONFIRMATION if not declared>
**Test root:** <inferred path, e.g. tests/>

### Unit / Contract Test Cases — User Story 1 (P1)

| Item | Layer | Case | Arrange → Act → Assert | Test file | Mocking |
|------|-------|------|------------------------|-----------|---------|
| US1-AS1 | unit | filter persists across pagination | Arrange: seeded filter state · Act: paginate next · Assert: filter still applied | tests/unit/filter-persistence.test.ts | DB stubbed; router real |
| US1-AS1 | unit | filter clears on explicit reset | … | tests/unit/filter-reset.test.ts | — |
| FR-001 | unit | invalid filter rejected with 400 | … | tests/unit/filter-validation.test.ts | — |
| FR-002 | contract | GET /search response matches schema v2 | … | tests/contract/search.contract.test.ts | network real (contract) |

### Edge Cases Covered
- Empty filter set → FR-001
- Filter with 1000+ values → FR-001 (perf SC-001 covered separately in test-plan.md)

### Advisory — higher layers (planned in FEATURE_DIR/test-plan.md by `qaprep` after implementation)
- Integration: end-to-end filter → results flow
- Perf: SC-001 p95 latency
- A11y: keyboard navigation of filter chips

### Traceability
Every P1 AS/FR above has ≥1 unit/contract case. SC items are deferred to test-plan.md.
```

### Step 6 — Report

Default (`--write`, no gaps):
```
SPECTEST PLAN: 6 P1 items planned (4 AS, 2 FR), 9 unit + 1 contract cases written to plan.md — OK
```

`--dry-run`:
```
SPECTEST PLAN (dry-run): would write 10 cases for 6 P1 items; plan.md unchanged.
```

If plan.md lacks a declared test framework:
```
SPECTEST PLAN: 10 cases written; test framework proposed as Vitest — NEEDS CONFIRMATION in plan.md
```

## Rules

- **Default writes, hook runs default** — the `after_plan` hook fires with no flags, so by
  default the section is written. `--dry-run` is the only way to preview without writing.
- **Modify only plan.md** — never edits spec.md, tasks.md, test-plan.md, or test code.
- **Idempotent** — re-running replaces the existing `## Testing Strategy` block in place; does
  not duplicate, does not append a second section.
- **Unit/contract only** — higher layers (integration/E2E/perf/a11y) are listed advisory and
  belong to `test-plan.md` (written by `qaprep`); never planned here as gated cases.
- **TDD intent** — every generated case is fail-first; `/speckit-implement` will write the
  test, see it fail, then implement to green.
- **No invented items** — every case must trace to a `US{N}-AS{M}` or `FR-###` from spec.md.
  Never invent behaviour the spec does not state.
- **Concrete paths** — each case names a real test file path, derived from plan.md's
  declared source layout. Never `tests/somewhere/*`.
- **At-least-one rule** — every P1 AS/FR gets ≥1 happy-path case plus ≥1 error/edge case when
  an applicable edge case exists.
- **Framework gap = NEEDS CONFIRMATION** — if plan.md hasn't declared a test framework,
  propose one and tag it; do not silently lock the choice.
- **Constitution authority** — may escalate (extra mandatory layers) but cannot silently
  remove the unit/contract requirement (that requires explicit `--advisory`).
- **Replaces the audit `--write` step** — with this hook in place, `/speckit-test-tasksaudit`
  should normally find zero gaps and run as a verification pass only.
