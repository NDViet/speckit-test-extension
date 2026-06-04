# speckit-test-extension — SDET Edition

A [Spec Kit](https://github.com/github/spec-kit) extension built from the perspective of an
Expert QA Engineer / SDET. It adds the testing layer that connects a feature's `spec.md` to
test tasks, test files, and pre-merge sign-off — closing the loop that Spec Kit's core
workflow leaves to manual effort.

It is anchored on the **stock Spec Kit artefacts** (no custom spec format required) and
defers to your project `constitution.md` to decide how strict the QA gates are.

Adapted from [spec-kit-spectest](https://github.com/Quratulain-bilal/spec-kit-spectest)
by Quratulain-bilal (MIT). See [Differences](#differences-from-upstream).

---

## Problem

Spec Kit's core workflow (`/speckit-specify` → `/speckit-plan` → `/speckit-tasks` →
`/speckit-implement`) produces a rich `spec.md` (prioritized user stories with Acceptance
Scenarios, Functional Requirements, Success Criteria) and a `tasks.md` breakdown — but the
testing layer is left manual:

- Nothing checks that `tasks.md` has a test task for each testable spec item
- Tests get written from memory, not from spec — traceability breaks
- There is no measure of "which spec items are actually tested" before the PR is approved
- QA pre-merge checks are ad-hoc

This extension closes those gaps, using the spec's own identifiers.

---

## Testable items — the unit of traceability

Everything keys off the **stock `spec.md`**, not a custom `AC-N` format. Three item types:

| Item | Where in spec.md | ID scheme |
|------|------------------|-----------|
| **Acceptance Scenario** | `### User Story N (Priority: Px)` → `**Acceptance Scenarios**` (Given/When/Then) | `US{n}-AS{m}` (priority inherited from the story) |
| **Functional Requirement** | `### Functional Requirements` | `FR-###` |
| **Success Criterion** | `## Success Criteria` → Measurable Outcomes | `SC-###` (only the *buildable* ones — perf/security/availability — are gated; business KPIs are not) |

Every generated test labels itself with the item ID, so the chain
`spec item → tasks.md test task → test file → CI` is checkable end to end.

---

## Commands

| Command | Lane — when | What it does |
|---------|------|--------------|
| `/speckit-test-tasksaudit` | 👤 **Dev** — after `/speckit-tasks`, before `/speckit-implement` (★) | **Pre-implementation gate.** Audits that every P1 spec item has a **unit/contract (TDD) test task** and **blocks** if not (default = read-only). `--write` adds the missing tasks to `tasks.md` so `/speckit-implement` builds them. Higher layers advisory here. |
| `/speckit-test-plan` | 🔎 **QA** — on the PR (1st) | Write `FEATURE_DIR/test-plan.md` — traceability matrix, **impact analysis**, and **layer ownership/timing** (dev unit pre-implement, QA layers post-implement); optionally seed `checklists/test.md`. |
| `/speckit-test-generate` | 🔎 **QA** — on the PR (2nd) | Scaffold the QA-owned layers (integration/E2E/regression/perf/a11y) and any item still missing a test. |
| `/speckit-test-coverage` | 🔎 **QA** — on the PR (3rd) | Map each item → test file, rate Strong/Medium/Weak (Stub = 0%). |
| `/speckit-test-gaps` | 🔎 **QA** — on the PR (4th) | Find items with no test task or no test file; severity-classified. |
| `/speckit-test-review` | 🔎 **QA** — on the PR (5th, pre-merge) | Full QA sign-off: mapping, stub scan, `/speckit-analyze`, scope-drift, traceability, constitution. |

> Command files are named `speckit.test.*.md`; Spec Kit surfaces them with dots → hyphens,
> so you invoke them as `/speckit-test-*`.

---

## The Quality Spec Kit workflow

Spec Kit's **core** workflow proves a feature was *built*:

```
/speckit-specify → /speckit-plan → /speckit-tasks → /speckit-implement
```

The **Quality** workflow proves it was *built right* — the same core flow with quality steps
woven in (core steps unchanged; `← Dev` / `← QA` marks who runs each addition; **★** is the one
mandatory gate):

```
/speckit-constitution                         ← defines whether/which tests are mandatory
/speckit-specify  →  /speckit-clarify         ← spec items: US{n}-AS{m}, FR-###, SC-###
/speckit-plan
/speckit-tasks
   └─ /speckit-test-tasksaudit                 ← Dev  advisory audit (after_tasks)
★  /speckit-test-tasksaudit                    ← Dev  MANDATORY gate (before_implement): audits &
                                                      BLOCKS; dev runs `--write` to add missing tasks
   /speckit-implement                          ← builds the feature + writes those tests first (TDD)
   ────────────────────────────── open PR ──────────────────────────────
   /speckit-test-plan                          ← QA   test-plan.md: impact analysis + QA test layers
   /speckit-test-generate                      ← QA   scaffold the QA-layer tests
   /speckit-test-coverage                      ← QA   requirement-level coverage
   /speckit-test-gaps                          ← QA   untested items
   /speckit-test-review                        ← QA   pre-merge sign-off  →  approve
```

In one line (commands only), split by role at the PR handoff:

```
👤 Developer (local; opens the PR after implementing)
/speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-test-tasksaudit ★ → /speckit-implement → 🔀 open PR

🔎 QA engineer (inspects the PR)
/speckit-test-plan → /speckit-test-generate → /speckit-test-coverage → /speckit-test-gaps → /speckit-test-review → ✅ approve
```

`★` = mandatory pre-implement gate (`before_implement` hook). It **audits and blocks** when a P1
scenario/FR has no unit/contract (TDD) test task — and prints the exact task lines to add. The
developer closes the gate by running `/speckit-test-tasksaudit --write` (which adds those tasks to
`tasks.md` for review) or by adding them by hand, then re-runs `/speckit-implement`. The hook
itself never edits `tasks.md`. The PR is raised only after `/speckit-implement`, so QA always
inspects a changeset whose unit tests were planned before any code was written.

---

## Who owns what, and when (the gate model)

The single hard gate lives **inside the Spec Kit flow**, before implementation — so it runs on
the developer's machine without any external CI:

```
BEFORE /speckit-implement   ── Developer ── Spec Kit MANDATORY gate (before_implement hook)
   /speckit-test-tasksaudit → audits that every P1 item has a UNIT/CONTRACT (TDD, fail-first)
                              test task in tasks.md; BLOCKS if not (read-only).
                              Dev runs `--write` to add the missing tasks, reviews, re-runs implement.

AFTER  /speckit-implement   ── QA ── planned in FEATURE_DIR/test-plan.md
   • Impact analysis + impact areas + regression scope
   • Integration / E2E / regression / performance / accessibility / manual layers
```

- **Unit/contract tests are a non-negotiable development gate** — the `before_implement` hook
  is mandatory and **read-only**: it blocks `/speckit-implement` when a P1 unit/contract test
  task is missing and prints the lines to add. The developer closes it with
  `/speckit-test-tasksaudit --write` (which adds the tasks to `tasks.md` for review) or by hand.
  Use `--advisory` only as an explicit, recorded opt-out; the constitution can *escalate* the gate
  to more layers but cannot silently remove it.
- **The heavier layers and impact analysis are QA's**, prepared after implementation and
  captured in `test-plan.md`. Regression scope is derived from the Impact Analysis section.

> Note on enforceability: Spec Kit hooks are agent-driven, so they bind when the developer
> works *through* `/speckit-implement`. To make the gate unbypassable regardless of how code
> is written, pair it with `test-plan.md --also-checklist` (which `/speckit-implement` blocks
> on) and/or a required CI check on the PR.

---

## Worked example: the gate in action

A feature `specs/001-connect-hotel-filter/` after `/speckit-tasks`.

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
- **SC-001**: Filtered results render in < 500ms for 1000 hotels.
```

Testable P1 items: `US1-AS1`, `US1-AS2`, `FR-001`, `FR-002`, `SC-001`.

### Step 1 — `tasks.md` straight from `/speckit-tasks` (unit tests incomplete)

```markdown
## Phase 3: User Story 1 - Filter hotels by star rating (Priority: P1) 🎯 MVP

### Tests for User Story 1
- [ ] T010 [P] [US1] Unit test for star-rating selection in tests/unit/star-filter.test.ts
- [ ] T011 [US1] Add tests

### Implementation for User Story 1
- [ ] T012 [P] [US1] Create StarRatingFilter in src/components/StarRatingFilter.tsx
- [ ] T013 [US1] Add pagination-aware filter state in src/state/filter.ts
- [ ] T014 [US1] Wire result-count badge in src/components/ResultCount.tsx
```

`FR-001` and `FR-002` have no unit test task, and `T011` is a stub.

### Step 2 — Run the gate (default audit) — it BLOCKS and shows what to add

```text
/speckit-test-tasksaudit          # this is what the before_implement hook runs (audit-only)
```

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
- SC-001 has no perf test — QA owns performance, prepared after implementation.

Gate: BLOCKED — run `/speckit-test-tasksaudit --write` to add these, or add them by hand.
```
```text
SPECTEST AUDIT: 4 gated items, 2 with unit/contract tests, 2 gaps (FR-001, FR-002), 1 stub — FAIL
```

### Step 3 — Developer runs `--write`; reviews the resulting `tasks.md`

```text
/speckit-test-tasksaudit --write
```

```markdown
### Tests for User Story 1
> NOTE: Write these tests FIRST, ensure they FAIL before implementation.
- [ ] T010 [P] [US1] Unit test for star-rating selection in tests/unit/star-filter.test.ts
- [ ] T011 [US1] Add tests                                   ← flagged: remove (stub)
- [ ] T015 [P] [US1] Unit test for filter persistence across pagination (FR-001) in tests/unit/filter-persistence.test.ts
- [ ] T016 [P] [US1] Unit test for result-count calculation (FR-002) in tests/unit/result-count.test.ts
```

The developer reviews the additions, deletes the flagged `T011` stub, then re-runs the gate
(now `PASS`) and `/speckit-implement` — which writes T010/T015/T016 first (they fail), then
implements until green. The developer must **not** re-run `/speckit-tasks` (it would discard
T015/T016). SC-001's perf test stays for QA's `test-plan.md`, post-implementation.

> Note: `SC-001` (a performance Success Criterion) passes the gate untouched because perf is a
> QA-owned layer prepared after implementation — the gate only acts on missing **unit/contract**
> tasks. SC-001 still appears in QA's `test-plan.md` as a post-implementation perf test.

---

## How it fits the SDD pipeline

```
/speckit-constitution     → constitution.md   (defines whether tests are mandatory)
/speckit-specify          → spec.md           (User Stories, Acceptance Scenarios, FR-###, SC-###)
/speckit-clarify          → spec.md updated
/speckit-plan             → plan.md
/speckit-tasks            → tasks.md
                            ↓
                   [Dev: /speckit-test-tasksaudit]  ← after_tasks hook (advisory)
/speckit-checklist        → checklists/*.md   (requirements-quality gate)
/speckit-analyze          → cross-artefact consistency report
                            ↓
                   [Dev: /speckit-test-tasksaudit]  ← before_implement hook (MANDATORY gate)
                   Audits & BLOCKS if a P1 unit/contract (TDD) test task is missing
                   (dev runs `--write` to add them to tasks.md, then reviews)
                            ↓
/speckit-implement        → source + tests (TDD: unit tests written first, must FAIL)
                            ↓
                   ══ Developer opens the PR ══
                            ↓
                   [QA: /speckit-test-plan]         ← test-plan.md: impact analysis + QA layers
                   [QA: /speckit-test-generate]     ← scaffold the QA-layer tests
                   [QA: /speckit-test-coverage]     ← requirement-level coverage
                   [QA: /speckit-test-gaps]         ← untested items
                   [QA: /speckit-test-review]       ← pre-merge sign-off
                            ↓
PR approved + merged
```

---

## Installation

```bash
# From a Spec Kit project root, after `specify init`
specify extension add --from ./speckit-test-extension
```

Requires Spec Kit ≥ 0.8.13.

---

## Key conventions

| Convention | Detail |
|------------|--------|
| **Feature directory** | Resolved via `.specify/scripts/powershell/check-prerequisites.ps1 -Json` (the `FEATURE_DIR`), not a hard-coded `specs/NNN-*` glob |
| **Testable items** | `US{n}-AS{m}` (Acceptance Scenarios), `FR-###`, buildable `SC-###` — drawn from stock `spec.md` |
| **Test tasks** | Identified by a `### Tests for User Story N` subsection **or** a test path/description — **not** by `[P]` |
| **`[P]` marker** | Means *parallelizable* (Spec Kit semantics), reported but never used to identify tests |
| **`[US#]` label** | Maps a task to its user story; used to attribute test tasks to scenarios |
| **Tests mandatory?** | Unit/contract (TDD) tests are mandatory by default before `/speckit-implement` (the gate). The `constitution.md` can escalate which layers block; `--advisory` is an explicit opt-out |
| **Automation kind** | `AUTO`/`MANUAL`/`BOTH` is *inferred* from the test path/wording for reports — never required on tasks |
| **Test plan** | `FEATURE_DIR/test-plan.md`; optional `FEATURE_DIR/checklists/test.md` to gate `/speckit-implement` |
| **Stub detection** | `.skip`/`.todo`/`xit`/`xdescribe`, `@pytest.mark.skip`, `throw new Error('TODO')`, `raise NotImplementedError`, `expect(true).toBe(true)`, bare `toBeTruthy()`/`assert True`, empty bodies |
| **Confidence** | Strong (label cites the item ID), Medium (keyword match), Weak (file maps to story only), Stub (0%) |
| **Out of scope** | Read from `spec.md` → `## Assumptions` (Spec Kit has no `## Out of scope` heading) |

---

## Hooks

Registered in `extension.yml`, dispatched via `.specify/extensions.yml`. **Only the
developer-lane gate is hooked** — the QA-lane commands are run by hand against the PR, not as
lifecycle hooks (QA never runs `/speckit-implement`):

| Event | Command | Mode | Behaviour |
|-------|---------|------|-----------|
| `after_tasks` | `/speckit-test-tasksaudit` | optional | Advisory audit right after tasks are generated — surface missing unit tests early |
| `before_implement` | `/speckit-test-tasksaudit` | **mandatory** | Unit-test gate (audit-only) — **blocks** if a P1 unit/contract (TDD) test task is missing; the dev runs `--write` to add them to `tasks.md` |

The QA-lane commands (`test-plan`, `test-generate`, `test-coverage`, `test-gaps`,
`test-review`) are invoked manually by the QA engineer on the opened PR.

---

## Differences from upstream

Based on [spec-kit-spectest v1.0.0](https://github.com/Quratulain-bilal/spec-kit-spectest).

| Area | Upstream | This extension |
|------|----------|----------------|
| Requirement IDs | `REQ-001` | Stock Spec Kit items: `US{n}-AS{m}`, `FR-###`, `SC-###` |
| Spec location | `.specify/spec.md` | `FEATURE_DIR/spec.md` via `check-prerequisites.ps1` |
| Test plan output | `.specify/test-plan.md` | `FEATURE_DIR/test-plan.md` (+ optional `checklists/test.md` gate) |
| `[P]` meaning | treated as test marker | corrected to *parallelizable*; tests found by subsection/path |
| Tests required? | always | unit/contract (TDD) mandatory before implement; QA layers post-implement; constitution can escalate |
| Automation tags | required on tasks | inferred for reports; never required (matches stock tasks.md) |
| Constitution | none | drives the test-requirement mode and coverage thresholds |
| Stub detection | not present | all review commands flag stubs with `file:line` |
| Pre-merge gate | none | `/speckit-test-review` full sign-off, folds in `/speckit-analyze` |
| Tasks audit | none | `/speckit-test-tasksaudit` — audits the unit-test plan and blocks (read-only); `--write` adds the missing tasks. Wired to `before_implement` |

---

## License

MIT — same as upstream.
