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
2. Read `spec.md` (items, Edge Cases, Assumptions), `plan.md` (incl. `## Testing Strategy` from planaudit — **read `Change Profile:` tags from its header; do not re-detect**), `tasks.md`, `.specify/memory/constitution.md`. Scan `tests/`.
3. If `Change Profile` is missing (planaudit older / older feature), default to `[feature]` and emit a Major.

## Outline

### Phase A — Write `FEATURE_DIR/test-plan.md`

Refresh in place; preserve content between `<!-- MANUAL-EDITS START -->` / `<!-- MANUAL-EDITS END -->`.

Sections in order:

1. **Header** — feature, owner, status, links, constitution version, framework, scope, defect-tracker base URL, **Change Profile (mirrored from plan.md)**.
2. **Item Traceability Matrix** — rows: every `US{n}-AS{m}`, gated `FR-###`, buildable `SC-###`. Cols: priority, unit/contract task ID(s), integration test, E2E, regression note, perf/a11y plan, status.
3. **Test Case Catalogue** — the QA source-of-truth. One row per executable case (manual or automated), authored from spec.md, usable without re-reading spec:
   | TC-ID | Item | Type (manual/auto) | Layer | Priority | Preconditions | Steps (G/W/T) | Expected | Test data ref | Env | Test file or runbook | Tags |
   TC-IDs are stable (`TC-001`…); manual cases get a runbook path instead of a test file.
4. **Test Strategy** — pyramid summary (unit/contract from planaudit + QA layers), env matrix (browsers/OS/devices), data fixtures + masking, defect workflow, **per-Change-Profile addenda**: `performance` → baseline + budget %, `security` → threat model ref + SAST/dep-scan tools, `concurrency` → load profile + soak duration, `ui` → visual baseline + supported viewports, `api` → schema-compat policy, `bugfix` → defect ID + regression-window, `refactor` → public-API surface inventory, `data-migration` → migration plan + rollback steps.
5. **Entry & Exit Criteria** — entry: PR open + unit/contract green + this plan present. Exit: zero P1 gaps + zero `qareview` Blockers + checklist green + every P1 TC has a recorded run result + every Change-Profile add-on layer is green or waived in writing.
6. **Risk Register** — from `### Edge Cases` + `## Assumptions` **plus** profile-driven rows: `bugfix` adds a "regression in linked area" row; `refactor` adds "behaviour drift on unowned callers"; `concurrency` adds "deadlock under contention"; `performance` adds "regression vs baseline"; `security` adds OWASP-relevant rows; `data-migration` adds "partial backfill / rollback failure". Each row names a mitigating TC-ID.
7. **Test Environment & Data** — tools, accounts (refs not secrets), seed, teardown, fixture file paths.
8. **Test Execution Log** — appended-to, never regenerated. Rows: run date, runner (CI URL or tester), build/commit, TC-IDs run, pass/fail/skip counts, defect IDs filed, notes.
9. **Open Questions** — every `[NEEDS CLARIFICATION]` in spec.md.

Idempotency: regenerate §1, 2, 3, 4, 7, 9; preserve §5, 6 if QA-edited; **append-only** §8 (never rewrite history).

### Phase B — Scaffold higher-layer stubs

For every gated item missing a QA-layer test, create a **failing** stub labelled with the item ID.

| Layer | Trigger (always-on) | Change-Profile add-ons |
|---|---|---|
| `tests/integration/` | every P1 `US{n}-AS{m}` without one | — |
| `tests/e2e/` | each user story without an E2E happy path | `ui` → also visual-regression + cross-browser variants |
| `tests/regression/` | FR tied to a high-blast-radius Risk row | `bugfix` → 1 reproducing test (must fail without fix) per defect FR; `refactor` → characterization snapshot per touched module |
| `tests/perf/` | every buildable `SC-###` with a perf criterion | `performance` → baseline file + regression-budget threshold; `concurrency` → soak/load profile |
| `tests/a11y/` | every `User-facing UI` story | — |
| `tests/concurrency/` | — | `concurrency` → N-parallel-callers stress + invariant property test per documented invariant |
| `tests/security/` | — | `security` → authz negative-path test per documented boundary; SAST + dep-scan runbook |
| `tests/migration/` | — | `data-migration` → up/down + idempotency + rollback drill per migration file |

- **Path:** `tests/<layer>/<slug>.<layer>.test.<ext>`; `<slug>` from spec item.
- **Framework:** from plan.md Testing Strategy.
- **Body:** A/A/A skeleton mapping G/W/T; header comment names the item ID **and TC-ID** from the Catalogue; fixture import points to §7 path; CI tag matches `--scope` (smoke/regression/full); TODO list of edge cases.
- **Must fail on first run** (`expect.fail("not implemented")` or equivalent).
- **Never overwrites.** Existing file → skip, record "kept".

For **manual cases**, scaffold a runbook at `tests/manual/<slug>.runbook.md` with the same TC-ID header, Preconditions, numbered Steps, Expected, Test Data ref, Env, and an "Evidence" section (screenshot / log / defect ID placeholders). Skip if exists.

### Phase C — Seed `FEATURE_DIR/checklists/test.md`

```markdown
# Test Checklist: <feature>

> Source: speckit.test.qaprep (after_tasks). Every tick MUST have an Evidence link
> (test run URL, screenshot path, defect ID, or commit SHA).

## Coverage
- [ ] Every P1 AS has a unit/contract test (tasksaudit verified) — Evidence: <run URL>
- [ ] Every P1 AS has an integration test — Evidence:
- [ ] Every user story has an E2E happy-path test — Evidence:
- [ ] Every buildable SC-### has a perf test (within threshold) — Evidence:
- [ ] Every user-facing UI story has an a11y test (zero criticals) — Evidence:

## Change-Profile gates (only rows for active tags shown)
- [ ] `bugfix`: reproducing test recorded failing pre-fix, passing post-fix — Evidence:
- [ ] `refactor`: characterization suite green; public-API surface unchanged — Evidence:
- [ ] `concurrency`: stress + invariant tests passed N=<n> runs, no deadlocks — Evidence:
- [ ] `performance`: baseline vs new within <x>% budget; flame-graph attached — Evidence:
- [ ] `security`: SAST clean, dep-scan clean, authz-negative tests green — Evidence:
- [ ] `ui`: visual diff reviewed; cross-browser matrix green — Evidence:
- [ ] `api`: schema-compat report clean (no breaking changes without version bump) — Evidence:
- [ ] `data-migration`: up/down/rollback rehearsed on staging — Evidence:

## Manual / Exploratory
- [ ] Every P1 TC of type=manual executed; result logged in test-plan.md §8 — Evidence:
- [ ] Exploratory charter run on highest-risk area — Evidence:

## Quality
- [ ] No stub-by-description tasks remain in tasks.md
- [ ] All integration/E2E tests pass on target env matrix — Evidence:
- [ ] Risk Register reviewed; mitigating TC-IDs linked
- [ ] Open defects triaged; Blockers fixed or waived — Evidence:

## Sign-off
- [ ] /speckit-analyze produced zero CRITICAL findings (if run)
- [ ] qareview produced zero Blocker findings — Evidence: review.md@<sha>
- [ ] Test plan peer-reviewed — Reviewer:
```

Refresh rule: **never uncheck** QA-ticked rows; add new rows for newly gated items. Evidence column is free-text; qareview parses it for traceability.

### Phase D — Report

```
SPECTEST QAPREP:
  test-plan.md: <created|refreshed> (12 items, 18 TCs [14 auto / 4 manual], 3 risks, 1 open Q)
  scaffolds:    integration +4, e2e +2, perf +1, a11y +1, manual runbooks +4 (kept: 3)
  checklist:    <created|refreshed> (17 rows, 4 ticked, 4 missing Evidence)
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
