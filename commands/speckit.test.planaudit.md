---
description: "Plan-time unit/contract test strategy. Mandatory after_plan hook. Appends/refreshes a '## Testing Strategy' section in plan.md mapping every P1 US{n}-AS{m} and FR-### to concrete fail-first unit/contract test cases. Idempotent; modifies plan.md only."
argument-hint: "[--dry-run] [--story US1] [--advisory]"
---

# Plan-time Unit Test Strategy — `after_plan` hook

Decides the unit/contract test layer at planning time so `/speckit-tasks` materializes the cases as real tasks and `tasksaudit` runs as a thin verification pass.

**Scope:** unit + contract only. Integration / E2E / regression / perf / a11y belong to `qaprep`'s `test-plan.md`.
**Writes:** `plan.md` § `## Testing Strategy` only. Never touches `spec.md`, `tasks.md`, tests, or other plan.md sections.
**Hook default:** write. `--dry-run` previews.

## User Input

```text
$ARGUMENTS
```

Flags: `--dry-run` (preview), `--story US1` (scope to one story), `--advisory` (banner only, TDD waived).

## Prerequisites

1. `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -IncludePlan` → parse `FEATURE_DIR`.
2. Read `spec.md` (Acceptance Scenarios, FR, Success Criteria, Edge Cases), `plan.md` (stack, layout, declared test framework), `.specify/memory/constitution.md` (TDD policy).
3. Do **not** read `tasks.md` — it does not exist yet.

## Outline

### 1. Policy
- **Default:** TDD mandatory — every P1 AS and FR needs ≥1 unit/contract case.
- **Constitution** may escalate layers (record principle name).
- `--advisory` records "TDD waived" banner, no gating change.

State the active policy at the top of the rendered section.

### 1b. Change Profile (detect once; downstream commands read it from here)

Scan spec.md headings/text and plan.md Technical Context for these literal signals; multi-tag allowed; default `feature` if none match. Record in the rendered section header as `**Change Profile:** [tag, …]`. Conflicting tags are logged, not silenced.

| Tag | Signals (any) | Adds to test recipe |
|---|---|---|
| `feature` | default | standard unit/contract per P1 AS/FR |
| `ui` | UI screens, UX flows, "user-facing UI", design files | + a11y + visual + cross-browser plan rows |
| `api` | endpoints, `contracts/`, SDK, schema | + contract tests, schema-compat, error envelopes, authz |
| `bugfix` | linked defect ID, FR phrased "MUST no longer …", "regression" | + 1 reproducing test (fails without fix) + 1 root-cause guard test |
| `refactor` | plan says "refactor/no behaviour change", no new FR | **characterization** tests on touched surface; **forbid** new functional cases unless surface changes |
| `concurrency` | race/lock/deadlock/async/parallel/atomic in spec or plan | + concurrent/N-caller stress, invariant/property tests, deterministic-seed repeat-N |
| `performance` | buildable `SC-###` with latency/throughput/resource budget | + baseline-vs-new perf test with a regression budget (% over baseline = FAIL) |
| `security` | auth/PII/permissions/crypto/threat in spec or plan | + authz negative tests, secrets handling, SAST + dep-scan rows (planned in test-plan.md) |
| `data-migration` | schema change, backfill, ETL, migration file in plan | + migration up/down, idempotency, data-integrity sampling, rollback drill |

State conflicts plainly: `Conflict: refactor + new FR-007 — treat as feature, log warning`.

### 2. Testable items (from spec.md)

| Source | ID | Gated here |
|---|---|---|
| `### User Story N` → Acceptance Scenarios | `US{N}-AS{M}` | **Yes** (P1). P2/P3 advisory. |
| `### Functional Requirements` | `FR-###` | **Yes** |
| `## Success Criteria` (perf/security/availability only) | `SC-###` | Advisory — deferred to `qaprep` |
| `### Edge Cases` | — | Case candidates under their FR/AS |

### 3. Framework & paths
Infer from plan.md (language → conventional framework; declared paths). If undeclared, propose one and tag `NEEDS CONFIRMATION`.

### 4. Generate cases
For each in-scope item, emit ≥1 happy-path case and ≥1 error/edge case (when an edge applies). Each case has: Item ID, Layer (`unit` default; `contract` for API/schema), Case name, Arrange/Act/Assert (map G/W/T directly when AS), concrete test path, mocking boundary.

**Change-Profile additions at the unit/contract layer** (deferring heavier layers to qaprep):

- `bugfix` → for each corrective FR, also emit a **reproducing-bug** case (must fail before fix) and a **root-cause guard** case.
- `refactor` → for each touched module, emit **characterization** cases that lock current behaviour from existing call sites; do **not** invent new behavioural cases.
- `concurrency` → for each invariant in spec/plan, emit a **property** or **repeat-N deterministic-seed** case at unit level; full stress belongs to qaprep.
- `api` → for each contract, emit a **schema-compat** case (current schema = green, breaking change = red) alongside the contract test.
- `performance` → unit-level **micro-benchmark guard** if plan declares one; otherwise defer to qaprep.
- `security` → for each authz boundary in plan, emit a **negative-path** unit/contract case (forbidden role rejected).
- `data-migration` → emit a **migration up + down** unit/contract case per migration file.

Each added case still names a real `US{N}-AS{M}` or `FR-###`; never invented.

### 5. Render `## Testing Strategy` block

Append at end of plan.md (or replace existing block between `## Testing Strategy` and the next `## ` heading — never duplicate).

```markdown
## Testing Strategy

> Generated by speckit.test.planaudit (after_plan). Source of truth for unit/contract cases.
> `/speckit-tasks` materializes each row as a test task; `tasksaudit` verifies the mapping.

**Policy:** TDD mandatory (unit + contract, fail-first).
**Change Profile:** [feature | ui | api | bugfix | refactor | concurrency | performance | security | data-migration]
**Test framework:** <inferred> <NEEDS CONFIRMATION if undeclared>
**Test root:** <inferred>

### Unit / Contract Test Cases — User Story 1 (P1)

| Item | Layer | Case | A → A → A | Test file | Mocking |
|------|-------|------|-----------|-----------|---------|
| US1-AS1 | unit | filter persists across pagination | seeded state · paginate · assert filter applied | tests/unit/filter-persistence.test.ts | DB stub; router real |
| FR-002 | contract | GET /search response matches schema v2 | … | tests/contract/search.contract.test.ts | network real |

### Edge Cases Covered
- Empty filter set → FR-001

### Advisory (planned later by qaprep in test-plan.md)
- Integration, perf SC-001, a11y keyboard nav

### Traceability
Every P1 AS/FR above has ≥1 unit/contract case. SC items deferred.
```

### 6. Report

```
SPECTEST PLAN: profile=[api,security], 6 P1 items, 9 unit + 1 contract cases (incl. 2 authz-negative) — OK
```

`--dry-run`: `SPECTEST PLAN (dry-run): would write 10 cases; plan.md unchanged.`
Missing framework: append `— framework proposed as Vitest, NEEDS CONFIRMATION`.

## Rules

- **Idempotent** — re-running replaces the block in place; never duplicates.
- **Modify only plan.md / Testing Strategy section.**
- **Unit + contract only** — never plan higher layers as gated here.
- **No invented items** — every case traces to a real `US{N}-AS{M}` or `FR-###`.
- **Concrete paths** — no `tests/somewhere/*`.
- **Constitution may escalate, never silently waive** — waiving requires explicit `--advisory`.
