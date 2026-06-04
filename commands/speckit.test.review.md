---
description: "QA pre-merge sign-off: item→test-task mapping, stub scan, /speckit-analyze consistency, constitution compliance, scope-drift, traceability chain. Outputs a Blocker/Major/Minor table. Read-only."
argument-hint: "[--strict] [--skip-analyze] [--base main]"
---

# QA Pre-Merge Review

**QA lane — the QA engineer's final step on the opened PR** (last in
`test-plan → test-generate → test-coverage → test-gaps → test-review`).

Run the full QA pre-merge checklist for the current feature branch — the final QA gate
before PR approval. It verifies the **structural** completeness of the testing artefacts
against the stock Spec Kit feature; it does not replace human judgment on product correctness.

**Read-only** — never modifies any file.

## User Input

```text
$ARGUMENTS
```

The user may specify:
- `--strict` — treat all Major findings as Blockers
- `--skip-analyze` — reuse the last `/speckit-analyze` output instead of re-running it
- `--base main` — diff base branch (default `main`)
- `--feature specs/NNN-name` — target a specific feature folder

## Prerequisites

1. Confirm a git repo with a committed/clean working tree.
2. Resolve the feature directory:
   `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`
   Parse `FEATURE_DIR`. If several feature folders changed on this branch, review each.
3. Read `spec.md`, `plan.md`, `tasks.md` for each changed feature folder.
4. Read `.specify/memory/constitution.md`.
5. List test/source files changed on the branch: `git diff --name-only <base>...HEAD`.
6. Read `FEATURE_DIR/test-plan.md` and `FEATURE_DIR/checklists/*.md` if present.
7. Run `/speckit-analyze` inline (or reuse last output with `--skip-analyze`).

## Outline

### Step 1 — Item → Test-Task Mapping (mirrors /speckit-test-tasksaudit)

For each **P1 Acceptance Scenario and Functional Requirement** (the gated items):
- A **unit/contract** test task exists in tasks.md (identified by Tests subsection / test path,
  **not** `[P]`)? Missing = **Blocker** (the TDD gate must have held); `--advisory` downgrades to Minor.
- The task names the specific behaviour? Vague = **Major**.

For **`SC-###`** and the QA layers (integration/E2E/regression/perf/a11y): check them against
`FEATURE_DIR/test-plan.md` instead — a planned-but-absent layer at merge time is a **Major**.

### Step 2 — Stub Test Scan

Scan test files changed on the branch for: `expect(true)`, `.toBe(true)`, bare `toBeTruthy()`,
`.todo`, `.skip`, `xit`/`xdescribe`/`it.skip`, `@pytest.mark.skip`, `throw new Error('TODO')`,
`raise NotImplementedError`, empty bodies. Flag each with `file:line`.
- Stub on a P1 item = **Blocker**; on a P2/P3 item = **Major**.

### Step 3 — Coverage Spot-Check (mirrors /speckit-test-coverage)

For each item:
- Test file with the item ID in its label (Strong) → ✅
- Keyword-only match (Medium) → **Minor** (suggest label fix)
- No real test at all for a P1 scenario/FR → **Blocker** (`--advisory` downgrades to Major)

### Step 4 — /speckit-analyze Consistency

Run/reuse `/speckit-analyze` and fold in its findings:
- Requirements with zero task coverage = **Blocker** (matches analyze CRITICAL)
- Constitution MUST violations = **Blocker**
- Duplicate/conflicting requirements, scope creep = **Major**
- Terminology drift = **Minor**

### Step 5 — Scope-Drift Check

Compare the branch diff against tasks.md:
- Source files changed that map to no task ID = **Major** (scope drift)
- Task IDs marked `[X]` with no corresponding diff = **Major** (claimed-but-absent)
- Task IDs not yet `[X]` but already implemented = **Minor** (update tasks.md)

### Step 6 — Traceability Chain

For each item verify `spec item → tasks.md test task → test file (label cites the ID) → CI`.
- Any broken link = **Major**
- Weak label (no ID) = **Minor**

### Step 7 — Test Plan & Checklists

- `FEATURE_DIR/test-plan.md` present and linked in the PR? Missing = **Major**.
- `FEATURE_DIR/checklists/*.md` all complete? Incomplete items = **Major** (Spec Kit's
  `/speckit-implement` itself blocks on these).

### Step 8 — Constitution Compliance

- Every constitution MUST principle respected by the diff (test principles especially).
- A violated principle = **Blocker**.
- A missing-but-expected test principle (e.g., no Test-First while the team practises TDD) = **Minor** (flag for a constitution PR).

### Step 9 — Report

```markdown
## QA Pre-Merge Review

Feature: specs/001-connect-hotel-filter/
Branch: 001-connect-hotel-filter (base: main)
Unit gate: enforced (default; constitution: "III. Test-First (NON-NEGOTIABLE)")
Reviewed: spec.md ✅ | plan.md ✅ | tasks.md ✅ | constitution.md ✅ | test-plan.md ✅

### Findings
| Severity | Location | Item / Task / Rule | Issue | Suggested Fix |
|----------|----------|--------------------|-------|---------------|
| Blocker | tests/perf/filter.perf.ts:18 | SC-001 / T017 | `.skip` stub on a P1 item | Implement the < 500ms assertion |
| Major | tests/unit/result-count.test.ts:42 | FR-002 | Label omits FR-002 — chain broken | Rename to "FR-002: …" |
| Major | — | tasks.md T015 | Marked [X] but no diff | Confirm done or unmark |
| Minor | — | constitution | No Integration-Testing principle | Propose in next constitution PR |

### Coverage Summary
| Item | Test Task | Test File | Traceability | Status |
|------|-----------|-----------|--------------|--------|
| US1-AS1 | T010 ✅ | ✅ Strong | ✅ Complete | ✅ |
| FR-002 | T016 ✅ | ⚠️ Medium | ⚠️ Weak label | ⚠️ |
| SC-001 | T017 ✅ | ❌ Stub | ❌ Broken | ❌ |

### Manual Verification Required
| Item | Why Manual |
|------|-----------|
| US2-AS1 keyboard flow | Keyboard navigation needs a human; axe-core alone is insufficient |
| FR-001 product correctness | Pagination persistence needs a live click-through |

### Gate Verdict
| Category | Count |
|----------|-------|
| 🔴 Blockers | 1 |
| 🟠 Major | 2 |
| 🟡 Minor | 1 |

**GATE: ❌ BLOCKED**
Resolve all Blockers before requesting approval. Majors must be fixed or justified in a PR comment. Minors may be deferred.
```

**When clean:**
```markdown
### Gate Verdict
Blockers: 0 | Major: 0 | Minor: 0
**GATE: ✅ APPROVED**
Structural QA checks passed. Human sign-off on manual cases and product correctness still required.
```

End with a CI line:
```
SPECTEST REVIEW: 1 blocker, 2 major, 1 minor — BLOCKED
```

## Rules

- **Read-only** — never modify any file on the branch.
- **Severity hierarchy** — Blocker = must not merge; Major = fix or justify in PR; Minor = should fix, may defer.
- **Unit gate held** — a P1 scenario/FR with no unit/contract test is a Blocker (the pre-implement TDD gate should have caught it); `--advisory` downgrades. SC and QA layers are judged against test-plan.md (planned-but-absent = Major).
- **`[P]` is parallelism** — identify test tasks by Tests subsection / test path, never by `[P]`.
- **Stub on P1 = Blocker** — always, flagged with exact `file:line`.
- **Missing test plan = Major; incomplete checklist = Major** — both are required deliverables; checklists additionally block `/speckit-implement`.
- **Manual Verification section mandatory** — always list what cannot be auto-verified and why.
- **Constitution violations = Blocker** — any violated MUST principle.
- **Fold in /speckit-analyze** — do not duplicate its logic; reuse its findings and map their severities.
- **Verdict explicit** — always end with `GATE: ✅ APPROVED` / `GATE: ❌ BLOCKED` and the `SPECTEST REVIEW:` line.
- **Not a substitute for human judgment** — structural checks only; product correctness is the reviewer's call.
