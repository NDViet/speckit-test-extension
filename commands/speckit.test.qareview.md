---
description: "Consistency + quality verdict — runs as the after_analyze hook. Reads /speckit-analyze's report, then computes requirement-level coverage (Strong/Medium/Weak/Stub), finds untested items, runs the stub scan + scope-drift + traceability + constitution checks, and emits a Blocker/Major/Minor table with an explicit Gate: PASS / BLOCKED verdict. Always writes the verdict to FEATURE_DIR/review.md (overwrites prior run) so every /speckit-analyze invocation leaves a tracked record. Runnable anytime in the workflow; the run after /speckit-implement is the formal pre-merge gate."
argument-hint: "[--strict] [--story US1] [--no-write]"
---

# Consistency + Quality Verdict — built-in step of `/speckit-analyze`

**Runs automatically as the mandatory `after_analyze` hook of `/speckit-analyze`.**
Quality is part of the workflow, not a separate role. Anyone — at any point — can invoke
`/speckit-analyze` to see the current consistency + quality state; this hook bundles what
would otherwise be three separate manual commands (`test-coverage`, `test-gaps`,
`test-review`) into one verdict. The run that follows `/speckit-implement` is the formal
**pre-merge gate**; earlier runs are status checks.

The command **reads `/speckit-analyze`'s in-conversation report** (the consistency findings,
the coverage summary table, the unmapped tasks list) plus the artefacts `qaprep` produced
after `/speckit-implement` (test-plan.md, scaffolded tests, checklists/test.md), and emits the
final Gate decision.

**Write scope is exactly one file: `FEATURE_DIR/review.md`** (always overwritten with the
latest verdict). All source artefacts — `spec.md`, `plan.md`, `tasks.md`, `test-plan.md`,
test code, checklists — are **read-only**. Edits to those artefacts remain reserved to
`planaudit` (plan.md) and `qaprep` (test-plan.md / scaffolds / checklist).

The `review.md` file is the persisted record of each `/speckit-analyze` run. The PR
description links to it; CI parses its `Gate:` line; the user can diff it across runs to see
how the verdict evolved. The file is overwritten on each run so it always reflects the
**latest** state — the run that follows `/speckit-implement` is therefore the formal
pre-merge gate captured in this file.

## User Input

```text
$ARGUMENTS
```

The user (or hook) may specify:
- _(no flags)_ — default; emit the verdict to chat **and** write it to `FEATURE_DIR/review.md`
- `--strict` — treat Majors as Blockers (CI-grade)
- `--story US1` — scope the verdict to one user story
- `--no-write` — skip writing `review.md` (chat-only); rarely used since tracking is the default

## Prerequisites

1. Resolve the feature directory:
   `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`
   Parse `FEATURE_DIR`.
2. Read `FEATURE_DIR/spec.md` fully — items: `US{n}-AS{m}`, `FR-###`, buildable `SC-###`.
3. Read `FEATURE_DIR/plan.md` — including the `## Testing Strategy` section written by
   `planaudit`.
4. Read `FEATURE_DIR/tasks.md` — test tasks (Tests subsection / test path), `[US#]` labels.
5. Read `FEATURE_DIR/test-plan.md` — the traceability matrix, entry/exit criteria.
6. Read `FEATURE_DIR/checklists/test.md` — checked/unchecked items.
7. Read `.specify/memory/constitution.md` — gates and thresholds.
8. **Read the `/speckit-analyze` report** from the active conversation:
   - The finding table (IDs A1, D1, …) with severities.
   - The Coverage Summary Table (requirement → task IDs).
   - The Unmapped Tasks list.
   - Constitution Alignment Issues block.
9. Scan `tests/` for actual files present.

## Outline

The command runs five checks, aggregates findings, and emits a single verdict.

### Check 1 — Requirement-level Coverage (rates each mapping)

For every gated item (P1 `US{n}-AS{m}`, `FR-###`, buildable `SC-###`), find its tests and
rate the mapping:

| Rating | Criteria |
|--------|----------|
| **Strong** | ≥1 non-stub test exists that names the item ID and exercises the documented behaviour |
| **Medium** | Test exists and names the item, but only partial coverage (happy path only, no edge cases) |
| **Weak** | Test exists in the right area but does not reference the item ID — traceability broken |
| **Stub** | Only a generated stub file exists (still failing on purpose) — counts as 0% coverage |
| **Missing** | No test file at all |

Constitution threshold (default: every P1 must be Strong; SC perf may be Medium) decides
which ratings escalate to Blocker.

### Check 2 — Stub Scan

For every test file referenced in `tasks.md` or `test-plan.md`:
- If the file is **the `qaprep` failing stub still unchanged** and the item is P1 → Blocker
  ("QA has not implemented integration test for US1-AS1").
- If the file body matches a "stub by description" task in `tasks.md` → Major.

### Check 3 — Cross-reference `/speckit-analyze` Findings

Read `/speckit-analyze`'s report from the conversation; lift each finding:
- Any CRITICAL → Blocker here (preserve analyze's ID, prefix with `[ANALYZE]`).
- Any constitution-aligned violation → Blocker.
- Requirements with no mapped task (in analyze's coverage summary) → Blocker.
- Unmapped tasks (work not traced to a requirement) → Major (scope drift).

### Check 4 — Traceability Chain

Verify the chain holds end-to-end for every gated item:
`spec item ID → plan.md Testing Strategy row → tasks.md test task → test file with the ID in
its header → test-plan.md matrix row`.
Any broken link → Major.

### Check 5 — Checklist & Test-Plan Presence

- `FEATURE_DIR/test-plan.md` exists and has every gated item in its matrix → else Blocker.
- `FEATURE_DIR/checklists/test.md` exists; all gated rows ticked → else Major (Blocker under
  `--strict`).
- Constitution-required sections of `test-plan.md` present → else Major.

### Output — Verdict Report (chat + `FEATURE_DIR/review.md`)

The same verdict body is emitted to both destinations: streamed to chat (so the user sees it
immediately) and written verbatim to `FEATURE_DIR/review.md` (so the run is tracked). The
file body is the markdown shown below, with a metadata header prepended:

```markdown
<!-- Generated by speckit.test.qareview (after_analyze hook). Do not edit by hand;
     this file is overwritten on every /speckit-analyze run. -->

# Consistency + Quality Verdict — <feature name>

| Field        | Value |
|--------------|-------|
| Feature      | specs/001-… |
| Run at       | 2026-06-08T14:32:11Z |
| Triggered by | /speckit-analyze (after_analyze hook) |
| Verdict      | **Gate: BLOCKED ❌** (or **Gate: PASS ✅**) |
| Mode         | normal / --strict / --no-write |

---

Source: after_analyze hook of /speckit-analyze
Gated items: 12 (8 P1, 4 SC) | Strong: 7 | Medium: 2 | Weak: 1 | Stub: 1 | Missing: 1

### ❌ Blockers
| ID | Where | Issue | Action |
|----|-------|-------|--------|
| B1 | US1-AS2 | Integration test is still the qaprep failing stub | QA must implement tests/integration/filter-persistence.integration.test.ts |
| B2 | FR-007 | No test of any kind | Add unit test (developer) and integration test (QA) |
| B3 | [ANALYZE] A4 | Constitution MUST violation: SC-001 perf criterion has no test | Add k6 scenario in tests/perf/search-latency.perf.test.ts |

### ⚠️ Majors
| ID | Where | Issue |
|----|-------|-------|
| M1 | tests/integration/checkout.test.ts | Does not reference US3-AS1 (weak traceability) |
| M2 | T021 | Task is unmapped to any spec item (scope drift) |

### ℹ️ Minors
| ID | Where | Issue |
|----|-------|-------|
| m1 | test-plan.md §Risk | Risk Register has 2 rows; spec.md has 4 edge cases — extend |

### Constitution
- "Integration Testing" principle: 1 violation (see B3).
- "Test-First" principle: clean (planaudit + tasksaudit + qaprep all ran).

### Checklist
checklists/test.md: 12 of 15 ticked; 3 unchecked (rows: 7, 9, 13)

### Verdict
**Gate: BLOCKED ❌** — 3 Blockers must be resolved before merge.

SPECTEST QAREVIEW: 12 items, 7 Strong, 3 Blockers, 2 Majors, 1 Minor — FAIL
```

If clean:

```
### Verdict
**Gate: PASS ✅** — all gated items Strong; no Blockers; no constitution violations.

SPECTEST QAREVIEW: 12 items, 12 Strong, 0 Blockers, 0 Majors — PASS
```

Under `--strict`, Majors are reported as Blockers and the verdict reflects that.

## Rules

- **Single write target: `FEATURE_DIR/review.md`** — every run overwrites it with the latest
  verdict. All source artefacts (spec.md, plan.md, tasks.md, test-plan.md, tests, checklists)
  are read-only. `--no-write` skips the file but is rarely used; tracking is the default.
- **Chat + file always agree** — the same verdict body that streams to chat is the body of
  `review.md`, plus a metadata header (run timestamp, mode, feature path). Never let them
  diverge.
- **Overwrite, not append** — `review.md` is the **latest** verdict, not a log. History lives
  in git (commit `review.md` alongside the change to see the verdict evolve).
- **Single workflow entry point** — `/speckit-analyze` is the consistency + quality verdict
  step. Anyone may invoke it at any point; this hook produces the verdict automatically.
  The verdict from the last run after `/speckit-implement` is the formal pre-merge gate
  captured in `review.md`.
- **Reads /speckit-analyze's report** — does not re-derive consistency findings; lifts them
  from the conversation so analyze stays the single source of truth on consistency.
- **Mandatory hook** — `after_analyze` fires this with no flags; it always produces a
  verdict, never asks the user.
- **Constitution authority** — its MUSTs always escalate to Blocker; cannot be silenced.
- **Stubs are not coverage** — a `qaprep` stub still in its failing state is `Stub = 0%`.
- **Traceability requires the item ID in the test** — without the ID in the test header,
  rating is at most Weak.
- **Explicit verdict** — always emits `Gate: PASS` / `Gate: BLOCKED` and the
  `SPECTEST QAREVIEW:` one-line summary for CI.
- **Three artefacts must exist** — `test-plan.md`, `checklists/test.md`, the scaffolds. If
  any is absent, this command's first finding is a Blocker telling the developer to re-run
  `/speckit-implement` (which fires `qaprep`).
