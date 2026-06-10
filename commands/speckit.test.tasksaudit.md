---
description: "Pre-implementation gate. Mandatory before_implement hook (audit-only); BLOCKS if any P1 spec item lacks a unit/contract test task in tasks.md. With --write (manual only), adds the missing tasks in place."
argument-hint: "[--write] [--advisory] [--require integration,e2e] [--story US1]"
---

# Pre-Implementation Gate (Unit / TDD)

The unit/contract plan was decided by `planaudit`; this command verifies `/speckit-tasks` materialized every case as a real test task. Higher-layer absence is **advisory** (handled by `qaprep`).

**Hook behaviour:** `before_implement` fires with no flags → **audit-only**. `--write` is a deliberate developer action, never an unattended hook side effect.

**Writes (only with `--write`):** adds unit/contract tasks to `tasks.md`. Never edits other files, deletes, or renumbers.

> ⚠️ After `--write`, do **NOT** re-run `/speckit-tasks` — it regenerates tasks.md and discards the additions.

## User Input

```text
$ARGUMENTS
```

Flags: `--write` (apply fix), `--advisory` (warning instead of block; never writes), `--require integration,e2e` (escalate layers), `--story US1`.

## Prerequisites

1. `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` → parse `FEATURE_DIR`, `AVAILABLE_DOCS`.
2. Read `spec.md`, `tasks.md`, `plan.md` (if present), `.specify/memory/constitution.md`.

## Outline

### 1. Gate policy
- **Default:** Unit Gate ON — every P1 AS/FR needs a unit or contract task.
- **Constitution / `--require`** can add layers to the blocking set.
- **`--advisory`** downgrades unit gate to warning.

State the active policy + source at top of report.

### 2. Testable-item inventory (from spec.md)

| Source | ID | Gated? |
|---|---|---|
| User Story → Acceptance Scenarios | `US{N}-AS{M}` | **Yes** (P1) |
| Functional Requirements | `FR-###` | **Yes** |
| Success Criteria (buildable) | `SC-###` | Advisory; QA layer in test-plan.md |
| Edge Cases | — | Candidates; not gated |

### 3. Classify test tasks (from tasks.md)

Stock format is `- [ ] T0NN [P?] [US#?] desc + path` (Speckit). `[P]` = parallelizable, not "test". Treat a task as a test task if it sits under a `### Tests for User Story N` subsection **or** its description names a test (path/keyword).

Layer signals:

| Layer | Signals |
|---|---|
| **unit** | `tests/unit/`, `*.test.*`/`*.spec.*`/`test_*`, "unit test" |
| **contract** | `tests/contract/`, "contract test", schema/API contract |
| integration | `tests/integration/`, cross-layer/journey |
| e2e | `tests/e2e/`, Playwright/Cypress |
| perf | `tests/perf/`, k6/load/latency, tied to SC |
| a11y | axe/jest-axe, "keyboard"/"ARIA"/screen reader |
| manual | "manual"/"exploratory" |

**unit** and **contract** satisfy the gate.

### 4. Apply the gate

For each P1 AS / FR:

| Check | Result |
|---|---|
| ≥1 unit/contract test task planned (TDD) | ✅ / ❌ Blocker |
| Names a specific behaviour (not "add tests") | ✅ / ⚠️ Major |
| Not a stub-by-description (no path, no behaviour) | ✅ / ❌ |
| Layers in escalated blocking set planned | ✅ / ❌ Blocker |
| Higher layers planned | ℹ️ Advisory (qaprep) |

For **SC-###**: report presence; **never Blocker** unless escalated.
Stub-by-description = no task.

### 5. Report (and complete with `--write`)

**Default audit (BLOCKED, no writes):**
```markdown
## Pre-Implementation Gate — BLOCKED ❌

Feature: specs/001-…/
Policy: Unit Gate ON (default)
P1 gated: 4 | Covered: 2 | Gaps: 2 | Stubs: 1

### ❌ Missing unit/contract task (add to close)
| Item | Task to add |
|------|-------------|
| FR-001 | `- [ ] T015 [P] [US1] Unit test for filter persistence (FR-001) in tests/unit/filter-persistence.test.ts` |
| FR-002 | `- [ ] T016 [P] [US1] Unit test for result-count (FR-002) in tests/unit/result-count.test.ts` |

### ⚠️ Should fix
| Task | Issue |
|------|-------|
| T011 [US1] Add tests | Stub-by-description |

### ℹ️ Advisory — QA layers (test-plan.md)
- SC-001 has no perf test — prepared by qaprep post-impl.

Gate: BLOCKED — `/speckit-implement` must not proceed until tasks added.
Run `/speckit-test-tasksaudit --write` to add (then review), or add by hand.
```

**`--write` insertion rules:**
- **Where:** under owning `### Tests for User Story N`. If missing, create it at the top of that story's phase with the TDD note: `> NOTE: Write these tests FIRST, ensure they FAIL before implementation.`
- **ID:** next free `T{max+1}`; never renumber.
- **Layer:** unit by default; contract for API/schema; with `--require`, add named higher layers.
- **Idempotent:** skip items already covered by a non-stub unit/contract task.
- **Stubs flagged, never deleted** — add the proper task alongside; developer removes the stub.

After `--write`, re-check Step 4 and emit `PASS` listing additions. Remind: do **not** re-run `/speckit-tasks`.

### 6. CI one-liner

```
SPECTEST AUDIT: 4 gated, 2 covered, 2 gaps (FR-001, FR-002), 1 stub — FAIL
SPECTEST AUDIT: 4 gated, 2 present + 2 added = 4, 1 stub flagged — PASS (written)
SPECTEST AUDIT: 4 gated, 4 covered, 0 gaps, 0 stubs — PASS
```

Under `--advisory`: render tables but label unit gaps `⚠️ Advisory (TDD waived)` and end `Gate: PASS (advisory)`.

## Rules

- **Hook = audit-only; `--write` is opt-in, never silent.**
- **After `--write`, do NOT re-run `/speckit-tasks`** — it would discard the additions.
- **Unit gate mandatory by default** — P1 AS/FR without a unit/contract task is a Blocker; `--advisory` is the only waiver.
- **SC-### advisory** — never a gate Blocker unless constitution/`--require` escalates.
- **Higher layers post-impl** — advisory here; home is `test-plan.md`.
- **`[P]` is parallelism, not "test"** — classify by Tests subsection or test path.
- **TDD intent** — additions sit in story Tests subsection with fail-first note.
- **Additive & idempotent** — only ever add; re-running after PASS changes nothing.
- **Never renumber existing tasks; never auto-delete stubs.**
- **Constitution may escalate, never silently waive the unit gate.**
- **Explicit verdict** — always emit `Gate: PASS|BLOCKED` + `SPECTEST AUDIT:` line.
