# speckit-test-extension -- Quality Built-In

A [Spec Kit](https://github.com/github/spec-kit) extension that bakes quality and testing
into the core SDD workflow as a built-in step at every lifecycle event. Hooks attach to
`/speckit-plan`, `/speckit-tasks`, `/speckit-analyze` (optional), and `/speckit-implement`
so quality work happens automatically and in the right order.

It anchors on the **stock Spec Kit artefacts** (no custom spec format required) and defers
to your project `constitution.md` to decide how strict the gates are.

---

## Installation

```bash
# From a Spec Kit project root, after `specify init`
specify extension add --force --from https://github.com/NDViet/speckit-test-extension/archive/refs/heads/master.zip EXTENSION
```

Or from a local folder (offline / development):

```bash
specify extension add --dev /path/to/speckit-test-extension
```

Requires Spec Kit >= 0.8.0.

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
- Non-functional changes (perf, security, race conditions, refactors) get the same generic
  unit-test treatment as a fresh feature, so QA effort lands in the wrong places

This extension closes those gaps by hooking quality work into the core workflow at every
lifecycle event, and by adapting the test recipe to the type of change.

---

## Design ideas behind the commands

### 1. Quality is part of the workflow, not a separate role

Every command fires as a hook on a non-skippable core command (`/speckit-plan`,
`/speckit-tasks`, `/speckit-implement`). Nothing here is invoked manually in the happy path.
A developer or PM running the standard Spec Kit workflow gets the quality scaffolding for
free.

### 2. Single source of truth per artefact, single writer per file

| Artefact | Owned by | Other commands |
|---|---|---|
| `plan.md` § Testing Strategy | `planaudit` | read-only |
| `tasks.md` (test tasks) | `/speckit-tasks` (+ `tasksaudit --write`) | read-only |
| `test-plan.md` | `qaprep` | read-only |
| `tests/**` scaffolds | `qaprep` (create only; never overwrites) | dev/QA implement |
| `checklists/test.md` | `qaprep` (refresh; never unchecks) | dev/QA tick + add Evidence |
| `review.md` | `qareview` (overwrite each run) | read-only |

No command edits two files. No file has two writers. Reading is unrestricted.

### 3. Spec is authority -- never invent behaviour

Every generated test case, task, and stub traces to a real `US{n}-AS{m}`, `FR-###`, or
buildable `SC-###`. The chain
`spec item -> plan.md Testing Strategy -> tasks.md test task -> test file -> test-plan.md
matrix -> review.md` is checkable end to end. Missing the item ID in the test header caps
qareview's rating at Weak.

### 4. Change Profile -- adapt the recipe to the type of change

`planaudit` runs a deterministic keyword scan of `spec.md` and `plan.md` Technical Context
once, then writes the result into `plan.md` § Testing Strategy header as
`**Change Profile:** [tag, ...]`. The other three commands read it from there; nobody
re-detects.

| Tag | Detection signal | Adds to the test recipe |
|---|---|---|
| `feature` | default | standard unit/contract per P1 AS/FR |
| `ui` | UI screens, UX flows, design files, user-facing UI stories | a11y + visual regression + cross-browser/device matrix |
| `api` | endpoints declared, `contracts/` exists, SDK, schema | contract tests, schema-compat, error envelopes, authz |
| `bugfix` | linked defect ID, FR phrased "MUST no longer ...", "regression" | reproducing test (fails pre-fix, passes post-fix) + root-cause guard |
| `refactor` | plan says "refactor / no behaviour change", no new FR | characterization tests on touched surface; new functional cases forbidden unless surface changes |
| `concurrency` | race / lock / deadlock / async / parallel / atomic | concurrent N-caller stress + invariants + deterministic-seed repeat-N |
| `performance` | buildable `SC-###` with latency/throughput/resource budget | baseline-vs-new perf test with a regression budget (% over baseline = FAIL) |
| `security` | auth / PII / permissions / crypto / threat | authz negative tests, secrets handling, SAST + dep-scan |
| `data-migration` | schema change, backfill, ETL, migration files | up/down/idempotency + rollback drill |

Multi-tag is allowed; conflicts (e.g. `refactor` + new FR) are logged, not silenced.

### 5. Mandatory gates, but `--write` is opt-in

The `before_implement` hook fires `tasksaudit` audit-only -- it can BLOCK but never silently
mutates `tasks.md`. Adding the missing tasks is a deliberate developer action
(`/speckit-test-tasksaudit --write`). This rule keeps automated hooks from editing files
behind the developer's back.

### 6. Constitution is authority

Your project's `constitution.md` may escalate which layers block, but cannot silently waive
a gate. Waiving requires an explicit `--advisory` flag, which is recorded.

---

## Commands (4 total, all hook-driven)

The core Spec Kit workflow is
`/speckit-plan` -> `/speckit-tasks` -> `/speckit-analyze` (optional) -> `/speckit-implement`.
Because `/speckit-analyze` is skippable, every mandatory quality gate anchors to one of the
non-skippable commands.

| Command | Hook | Mode | What it does | Expected outcome |
|---|---|---|---|---|
| `speckit.test.planaudit` | `after_plan` | mandatory | Detects the **Change Profile**; appends `## Testing Strategy` to `plan.md` mapping every P1 AS / FR to concrete fail-first unit/contract cases plus profile-specific additions (e.g. authz-negative for `security`, characterization for `refactor`, reproducing test for `bugfix`). Idempotent. | `plan.md` now contains a Testing Strategy section that `/speckit-tasks` will materialize. Includes profile tag, framework, test root, and per-item case rows. |
| `speckit.test.qaprep` | `after_tasks` | mandatory | Writes `FEATURE_DIR/test-plan.md` with QA-grade Test Case Catalogue (manual + automated TCs with preconditions / steps / expected / test data / env), traceability matrix, env matrix, risk register, entry/exit, **append-only Test Execution Log**; scaffolds higher-layer + profile-driven tests as failing stubs; seeds `checklists/test.md` with Evidence-link discipline. Idempotent; never overwrites existing tests or manual edits between markers. | `test-plan.md` is the QA source of truth -- manual testers can execute from §3 without re-reading spec, automation engineers can scaffold from it. Stubs fail until implemented, so missing coverage is visible in CI. |
| `speckit.test.tasksaudit` | `before_implement` | mandatory gate | Audit-only. BLOCKS `/speckit-implement` if any P1 spec item lacks a unit/contract test task; escalates the blocking set per active Change Profile (e.g. `performance` makes SC perf tasks gated; `bugfix` requires a reproducing test task). With `--write` (manual, opt-in), adds the missing tasks in place. | Either `Gate: PASS` (proceed) or `Gate: BLOCKED` with the exact task lines to add. The hook never silently mutates `tasks.md`. |
| `speckit.test.qareview` | `after_analyze` (advisory) + `after_implement` (mandatory) | both | Reads all artefacts, lifts `/speckit-analyze`'s findings (does not re-derive), computes per-item coverage (Strong / Medium / Weak / Stub / Missing), runs stub scan + traceability + constitution + checklist + **execution-evidence + Change-Profile** checks, emits `Gate: PASS / BLOCKED` to chat and to `FEATURE_DIR/review.md` (overwritten each run). | The `after_analyze` run is advisory (pre-impl readiness check). The `after_implement` run is the **formal pre-merge gate** -- it requires recorded test runs in §8 of `test-plan.md`, evidence links on every ticked checklist row, and profile-specific pass conditions. |

> Command files are named `speckit.test.*.md`; Spec Kit surfaces them with dots -> hyphens,
> so they appear as `/speckit-test-*` in chat. You rarely invoke them manually -- the hooks
> handle it.

---

## The unified Quality-Built-In workflow

```
/speckit-constitution                  defines whether/which tests are mandatory
/speckit-specify  ->  /speckit-clarify  spec items: US{n}-AS{m}, FR-###, SC-###

/speckit-plan
   |
   +-- after_plan       *mandatory  ->  planaudit
                                        detects Change Profile;
                                        writes ## Testing Strategy to plan.md

/speckit-tasks
   |
   +-- after_tasks      *mandatory  ->  qaprep
                                        writes test-plan.md (incl. TC Catalogue + Exec Log)
                                        + scaffolds higher-layer + profile-driven tests
                                        + seeds checklists/test.md

/speckit-analyze                       (OPTIONAL in Spec Kit; skippable)
   |
   +-- after_analyze     advisory   ->  qareview
                                        refreshes review.md with pre-impl read of
                                        consistency + readiness + Catalogue completeness;
                                        NEVER gates implement

/speckit-implement
   |
   +-- before_implement *mandatory  ->  tasksaudit (gate, audit-only)
   |                                    BLOCKS if any P1 unit/contract task missing
   |                                    (plus Change-Profile escalations)
   |
   +-- after_implement  *mandatory  ->  qareview
                                        refreshes review.md with the FORMAL pre-merge
                                        Gate PASS / BLOCKED, incl. real test results +
                                        execution evidence + profile checks
```

One line:
```
/speckit-plan -> /speckit-tasks -> [/speckit-analyze] -> /speckit-implement
   planaudit       qaprep            qareview              tasksaudit (gate)
                                     (advisory)            + qareview (formal)
```

---

## Artefacts produced

| Path | Produced by | When | Lifecycle |
|---|---|---|---|
| `FEATURE_DIR/plan.md` § Testing Strategy | `planaudit` | after `/speckit-plan` | Refreshed in place |
| `FEATURE_DIR/tasks.md` (test tasks) | `/speckit-tasks` materializes the Strategy; `tasksaudit --write` adds gaps | after `/speckit-tasks` | Edited additively |
| `FEATURE_DIR/test-plan.md` | `qaprep` | after `/speckit-tasks` | Refreshed; **§5, 6 preserve QA edits between markers; §8 Exec Log is append-only** |
| `tests/{integration,e2e,regression,perf,a11y,concurrency,security,migration}/` stubs | `qaprep` | after `/speckit-tasks` | Created if absent; **never overwrites** |
| `tests/manual/<slug>.runbook.md` | `qaprep` (when TC type = manual) | after `/speckit-tasks` | Created if absent; manual testers fill in evidence |
| `FEATURE_DIR/checklists/test.md` | `qaprep` | after `/speckit-tasks` | Refreshed; ticked rows + Evidence links preserved |
| `FEATURE_DIR/review.md` | `qareview` | after `/speckit-analyze` (advisory) and after `/speckit-implement` (formal) | **Overwritten** each run; `git log review.md` shows verdict evolution |

---

## Human in the loop -- where humans must engage

The hooks automate everything they can deterministically, but the following touchpoints
**require a human**. The artefacts make these touchpoints explicit so they cannot be
forgotten.

| Touchpoint | Who | What | Where it surfaces |
|---|---|---|---|
| Confirm framework choice | Developer | If `planaudit` could not infer the test framework, it tags the section `NEEDS CONFIRMATION` | `plan.md` § Testing Strategy |
| Add missing test tasks | Developer | `tasksaudit` BLOCKS on the hook; developer runs `--write` then reviews the additions | `tasks.md` after `--write` |
| Implement failing stubs | Developer (dev-layer) + QA (higher layers) | `qaprep` writes stubs that fail; implementation turns them green | `tests/**` |
| Fill the Test Case Catalogue | QA / Test author | Preconditions, Steps, Expected, Test data ref, Env per TC -- automated TCs link to the test file, manual TCs link to a runbook | `test-plan.md` § 3 |
| Edit Entry/Exit and Risk Register | QA lead | qaprep regenerates §1, 2, 3, 4, 7, 9 but **preserves §5 (Entry/Exit) and §6 (Risk Register)** between QA-edit markers | `test-plan.md` § 5 + § 6 |
| Tick the checklist with Evidence | QA / Reviewer | Every tick MUST carry an Evidence link (run URL / screenshot path / defect ID / commit SHA); bare ticks are flagged as Major by `qareview` | `checklists/test.md` |
| Record each test run | QA / CI | Append a row to the Test Execution Log: date, runner, build/commit, TC IDs run, pass/fail/skip, defects filed | `test-plan.md` § 8 |
| Triage defects | QA + Dev | When `qareview` reports a P1 TC FAIL, file a defect and link the ID in §8 -- a fail with no linked defect is a Blocker | defect tracker + `test-plan.md` § 8 |
| Sign off the review | Tech lead + QA lead | `review.md` is overwritten each run; the PR body should link to the latest `review.md` at the merge commit | PR description |
| Waive a gate | Tech lead with constitution authority | Only with explicit `--advisory`, recorded in the section banner; never silent | `plan.md` / `tasks.md` / `test-plan.md` banners |

The rule of thumb: anything that requires *judgement* (was the bug really fixed, is this
visual diff acceptable, is the perf regression worth shipping) is a human decision and the
artefact has a slot for the human to record it. Anything mechanical (does an item have a
test, is a stub still failing, is the schema backwards-compatible) is checked by the hooks.

---

## `.gitignore` guidance -- what to keep, what to ignore

Commit everything that is **part of the spec-driven record of the change**. Ignore
everything that is **a transient run output**.

### Commit (do NOT ignore)

These are the durable artefacts that make the change reviewable and the verdict reproducible.

```
specs/**/plan.md
specs/**/tasks.md
specs/**/test-plan.md
specs/**/checklists/**
specs/**/review.md
tests/**            # incl. qaprep stubs (failing stubs document missing coverage)
tests/manual/**     # manual runbooks are part of the spec
```

`review.md` is intentionally overwritten on every `qareview` run. Commit it alongside the
PR -- `git log review.md` is the verdict history.

### Special cases

**Fixture data**: small, deterministic fixtures belong in `tests/fixtures/` and should be
committed. Large or generated fixtures belong in a fixture store and should be referenced
by URL/SHA from `test-plan.md` § 7, not committed.

**Secrets**: never commit credentials, even for test environments. `test-plan.md` § 7 lists
*accounts and references*, not values. Use `.env.example` for shape and an ignored `.env`
for values.

**Approved baselines** (visual, perf, schema): commit them under
`tests/{visual,perf,contract}/baselines/`. Diff *output* is ignored; the *baseline* is
checked in so the regression budget is reviewable.

**`spec.md` itself**: always committed -- it is the input to the entire chain.

---

## The pre-merge gate

The formal pre-merge gate is whatever `qareview` writes to `FEATURE_DIR/review.md` **on the
`after_implement` run** -- the run that completes after `/speckit-implement` finishes, when
real test results are available. The file has a metadata header (feature, timestamp,
verdict, mode, Change Profile) followed by the Blocker / Major / Minor tables and a single
CI-grepable line:

```
SPECTEST QAREVIEW: 12 items, 7 Strong, 3 Blockers, 2 Majors, 1 Minor -- FAIL
```

CI can grep that line; the PR description links to `review.md` at the merge commit. To
refresh the verdict after fixing a Blocker, re-run `/speckit-implement` (its
`after_implement` hook fires `qareview` again).

If the developer also runs `/speckit-analyze` before implementing, `review.md` gets an
earlier advisory verdict (consistency + Catalogue readiness, no test results yet) -- useful
as a sanity check but never the formal gate.

---

## Hooks (mirrors `extension.yml`)

| Event | Command | Mode | Behaviour |
|---|---|---|---|
| `after_plan` | `planaudit` | **mandatory** | Detects Change Profile; appends Testing Strategy to `plan.md` |
| `after_tasks` | `qaprep` | **mandatory** | Writes `test-plan.md` (incl. TC Catalogue + Exec Log), scaffolds higher-layer + profile-driven tests, seeds `checklists/test.md` |
| `before_implement` | `tasksaudit` | **mandatory** | Audit-only gate; BLOCKS if any P1 unit/contract task missing (plus profile escalations) |
| `after_analyze` | `qareview` | advisory | Refreshes `review.md` with pre-implementation readiness verdict; never gates implement |
| `after_implement` | `qareview` | **mandatory** | Refreshes `review.md` with the **formal pre-merge** verdict, incl. real test results + execution evidence + profile checks |

---

## Key conventions

| Convention | Detail |
|---|---|
| **Feature directory** | Resolved via `.specify/scripts/powershell/check-prerequisites.ps1 -Json` (`FEATURE_DIR`) |
| **Testable items** | `US{n}-AS{m}`, `FR-###`, buildable `SC-###` -- drawn from stock `spec.md` |
| **Change Profile tags** | `feature`, `ui`, `api`, `bugfix`, `refactor`, `concurrency`, `performance`, `security`, `data-migration` -- detected once by `planaudit`, read everywhere else |
| **Test tasks** | Identified by `### Tests for User Story N` subsection or a test path -- not by `[P]` |
| **`[P]` marker** | Means *parallelizable* (Spec Kit semantics); never used to identify tests |
| **`[US#]` label** | Maps a task to its user story |
| **TC-ID** | Stable test-case ID in `test-plan.md` § 3, referenced from test file headers and Execution Log |
| **Evidence link** | Every ticked checklist row needs a run URL / screenshot / defect ID / commit SHA; bare ticks = Major in qareview |
| **Tests mandatory?** | Unit/contract (TDD) tests are mandatory by default. `constitution.md` can escalate which layers block; `--advisory` is the only opt-out, recorded explicitly |
| **Verdict file** | `FEATURE_DIR/review.md` -- written by `qareview` on `after_analyze` (advisory) and `after_implement` (formal). Overwritten each run |
| **Test plan** | `FEATURE_DIR/test-plan.md` (written by `qaprep` on `after_tasks`); § 5 + § 6 preserve QA edits; § 8 Exec Log is append-only |
| **Checklist** | `FEATURE_DIR/checklists/test.md` (seeded by `qaprep` on `after_tasks`) |
| **Stub detection** | `.skip` / `.todo` / `xit` / `xdescribe`, `@pytest.mark.skip`, `throw new Error('TODO')`, `raise NotImplementedError`, `expect(true).toBe(true)`, bare `toBeTruthy()` / `assert True`, empty bodies, unmodified qaprep stubs |
| **Confidence rating** | Strong (test cites item ID), Medium (keyword match), Weak (file maps to story only), Stub (0%), Missing (no test) |
| **Out of scope** | Read from `spec.md` § Assumptions (Spec Kit has no `## Out of scope` heading) |

---

## License

MIT
