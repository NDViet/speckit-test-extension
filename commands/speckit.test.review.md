---
description: "QA pre-merge sign-off. Runs the full Step 7 checklist: AC→test-task mapping, stub scan, /speckit.analyze consistency, constitution compliance, scope-drift check, traceability chain. Outputs Blocker/Major/Minor table for the PR."
---

# QA Pre-Merge Review

Run the complete QA Step 7 pre-merge checklist for the current feature branch.
This is the **final QA gate before PR approval**.

The command is the automated equivalent of the QA sign-off checklist in the team's
SDD Testing Process. It does not replace human judgment on test quality or product
correctness — it verifies the *structural* completeness of the testing artefacts.

Read-only — never modifies any file.

## User Input

```text
$ARGUMENTS
```

Consider user input before proceeding. The user may specify:
- `--strict` — treat all Major findings as Blockers
- `--skip-analyze` — skip running /speckit.analyze (if already run separately)
- `--feature specs/NNN-name` — target a specific feature folder explicitly

## Prerequisites

1. Confirm you are inside a git repository with a clean or committed working tree.
2. Locate `specs/NNN-*/spec.md` on the current branch. If multiple feature folders have
   changed on this branch, audit all of them.
3. Read `spec.md`, `plan.md`, `tasks.md` for each feature folder changed in this branch.
4. Read `.specify/memory/constitution.md`.
5. Locate all test files added or modified in this branch (`git diff --name-only main`).
6. Locate `testplan-NNN-*.md` if present.
7. Run the equivalent of `/speckit.analyze` inline (consistency check).

## Outline

### Step 1 — AC → Test Task Mapping (mirrors /speckit.test.tasksaudit)

For each AC-N in spec.md:
- Is there a `T00x [P]` test task in tasks.md? → Missing = **Blocker**
- Does the test task description name the AC and specific behaviour? → Vague = **Major**
- Does the test task have an automation tag `[MANUAL]`, `[AUTO]`, or `[BOTH]`? → Missing = **Minor**

### Step 2 — Stub Test Scan

Scan all test files changed on this branch:
- Search for: `expect(true)`, `.toBe(true)`, `toBeTruthy()` with no setup, `.todo`, `.skip`, `throw new Error('TODO')`, `raise NotImplementedError`
- Flag each occurrence with file:line
- Any stub in a P1 AC test = **Blocker**
- Any stub in a P2+ test = **Major**

### Step 3 — AC Coverage Spot-Check (mirrors /speckit.test.coverage)

For each AC-N:
- Does a test file exist with an `AC-N` label (Strong confidence)? → ✅
- Does a test file exist with keyword match only (Medium)? → ⚠️ **Minor** — suggest label fix
- No test file at all? → **Blocker**

### Step 4 — /speckit.analyze Consistency Check

Run the equivalent of `/speckit.analyze` (or reference its last output if `--skip-analyze`):
- Diff vs tasks.md: code does exactly the tasks — nothing extra = ✅; scope creep = **Major**
- Code below tasks: incomplete implementation = **Blocker**
- Constitution violations = **Blocker**
- Reuse violations (code duplicates existing module) = **Major**

### Step 5 — Scope-Drift Check

Compare the diff (files changed in this branch) against tasks.md:
- Files changed that are not covered by any task ID = **Major** (scope drift)
- Task IDs in tasks.md with no corresponding diff = **Major** (incomplete implementation)

### Step 6 — Traceability Chain Completeness

For each AC-N, verify the full chain is intact:
```
spec.md AC-N → tasks.md T00x [P] → test file (label includes AC-N) → CI (green)
```
- Any broken link = **Major**
- Weak confidence (no AC-N label) = **Minor**

### Step 7 — Test Plan Check

- Does `testplan-NNN-*.md` exist in `specs/NNN-*/`? → Missing = **Major**
- Is the PR description expected to link it? → Flag as reminder if testplan exists but link not verifiable

### Step 8 — Constitution Compliance

Read `.specify/memory/constitution.md` and check:
- QA non-negotiables are present
- Every flagged rule is respected in the diff
- Any missing QA non-negotiable in constitution = **Minor** (flag for next constitution PR)

### Step 9 — Compile and Output Report

Output a severity table and overall gate verdict:

```markdown
## QA Pre-Merge Review

Feature: specs/001-connect-hotel-filter/
Branch: feature/001-connect-hotel-filter
Reviewed: spec.md ✅ | plan.md ✅ | tasks.md ✅ | constitution.md ✅

---

### Findings

| Severity | File / Location | AC / Task / Rule | Issue | Suggested Fix |
|----------|----------------|------------------|-------|---------------|
| Blocker | tests/e2e/StarRatingFilter.a11y.test.ts:18 | AC-4 / T004 | Test body is `throw new Error('TODO')` — stub test on a P1 AC | Implement test assertions before merge |
| Major | tests/unit/StarRatingFilter.test.ts:42 | AC-3 | Test label does not include AC-3 reference — traceability chain broken | Rename to "AC-3: result count updates..." |
| Major | — | tasks.md T005 | Task T005 has no corresponding diff — implementation may be incomplete | Confirm T005 is done or remove from tasks.md |
| Minor | tasks.md T004 | AC-4 | Test task has no automation tag | Add [BOTH] to T004 |

---

### AC Coverage Summary

| AC | Test Task | Test File | Traceability | Status |
|----|-----------|-----------|--------------|--------|
| AC-1 | T001 ✅ | ✅ Strong | ✅ Complete | ✅ |
| AC-2 | T002 ✅ | ✅ Strong | ✅ Complete | ✅ |
| AC-3 | T003 ✅ | ⚠️ Medium | ⚠️ Weak label | ⚠️ |
| AC-4 | T004 ✅ | ❌ Stub | ❌ Broken | ❌ |

---

### Manual Verification Required

The following items cannot be verified automatically — a human must check:

| Item | Why Manual |
|------|-----------|
| AC-4 keyboard flow | Keyboard navigation requires a human tester; axe-core alone is insufficient |
| Product correctness of AC-2 | Pagination filter persistence requires clicking through the live UI |

---

### Gate Verdict

| Category | Count |
|----------|-------|
| 🔴 Blockers | 1 |
| 🟠 Major | 2 |
| 🟡 Minor | 1 |

**GATE: ❌ BLOCKED**
Resolve all Blockers before requesting PR approval.
Majors must be resolved or documented with justification.
Minors may be deferred to a follow-up ticket.
```

**When all clean:**
```markdown
### Gate Verdict
Blockers: 0 | Major: 0 | Minor: 0
**GATE: ✅ APPROVED**
QA structural checks passed. Human sign-off on manual test cases and product judgment still required.
```

## Rules

- **Read-only** — never modify any file on the branch
- **Severity hierarchy**: Blocker = PR must not merge until fixed; Major = must resolve or explicitly justify in PR comment; Minor = should fix, may defer
- **Stub tests on P1 ACs are always Blockers** — no exceptions; flag with exact file:line
- **Missing test plan is Major, not Minor** — the test plan is a required deliverable per the team's QA process
- **Manual verification section is mandatory** — always list what cannot be verified automatically and why; this section is for the human reviewer
- **Constitution violations are Blockers** — any rule in constitution.md that is violated by the diff is a Blocker, not a Major
- **Traceability weak labels are Minor** — a Medium-confidence test label (no AC-N in label) is a Minor finding; the fix is a label rename, not a new test
- **Gate verdict is explicit** — always end with `GATE: ✅ APPROVED` or `GATE: ❌ BLOCKED` on its own line; this makes it parseable by CI or PR automation
- **This does not replace human judgment** — always include the Manual Verification section; QA sign-off on product correctness is the human's responsibility, not this command's
