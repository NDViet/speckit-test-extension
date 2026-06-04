---
description: "Generate FEATURE_DIR/test-plan.md from spec.md (scenarios, FR-###, SC-###), plan.md, tasks.md, and constitution.md, with a full item traceability matrix."
argument-hint: "[--audience qa|dev] [--scope smoke|regression|full] [--also-checklist]"
---

# Generate QA Test Plan

**QA lane — the QA engineer's first step on the opened PR** (after `/speckit-implement`):
`test-plan → test-generate → test-coverage → test-gaps → test-review`. The developer does not
run this; it is QA's analysis of the implemented change.

Produce a complete QA test plan at `FEATURE_DIR/test-plan.md` — the document linked in the PR
description before merge. It is generated from the stock Spec Kit artefacts:

- `spec.md` — User Stories + Acceptance Scenarios, `FR-###`, `SC-###`, edge cases, `## Assumptions` (out-of-scope), `[NEEDS CLARIFICATION]`
- `plan.md` — tech stack, architecture, integration points, contracts
- `tasks.md` — test tasks (identified by Tests subsection / test path), `[US#]` labels
- `constitution.md` — test framework, test principles, coverage gates

## User Input

```text
$ARGUMENTS
```

The user may specify:
- `--audience qa|dev` — tailor depth
- `--scope smoke|regression|full`
- `--also-checklist` — additionally seed `FEATURE_DIR/checklists/test.md` (see Step 10)
- A filename override, or specific items to include/exclude

## Prerequisites

1. Resolve the feature directory:
   `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`
   Parse `FEATURE_DIR`. Fall back to `specs/*/spec.md` if unavailable.
2. Read `spec.md` fully — actor, user stories + priorities, Acceptance Scenarios, FR-###, SC-###, edge cases, out-of-scope (in `## Assumptions`), `[NEEDS CLARIFICATION]`.
3. Read `plan.md` — architecture, integration points, external services, error modes.
4. Read `tasks.md` — test tasks and their `[US#]` / paths.
5. Read `.specify/memory/constitution.md` — framework, test principles, thresholds.
6. If `FEATURE_DIR/test-plan.md` exists, **update** it rather than overwriting.

## Outline

### Step 1 — Header

```markdown
# Test Plan: [Feature Name from spec.md]

| Field | Value |
|-------|-------|
| Feature | [name] |
| Spec | specs/NNN-name/spec.md |
| Branch | [Feature Branch from spec.md] |
| Actor | [from user stories] |
| Date | [today] |
| Status | Draft |
| Framework | [from constitution.md / plan.md] |
| Author | /speckit-test-plan — reviewed by QA |
```

### Step 2 — Feature Summary

One paragraph from the user stories and their "Why this priority" / value statements.

### Step 3 — Scope

```markdown
## Scope

### In Scope (by user story priority)
- US1 (P1): [story title] — scenarios US1-AS1, US1-AS2
- US2 (P2): [story title] — scenarios US2-AS1
- Functional requirements: FR-001 … FR-00n
- Success criteria (buildable): SC-001 …

### Out of Scope
[Derived from spec.md ## Assumptions — items stated as out of scope / deferred]
```

### Step 4 — Impact Analysis & Impact Areas

QA's analysis of what this change touches and how far regression must reach. Derived from
`plan.md` (architecture, integration points, dependencies, data model) and the change scope.
For a microservice platform, walk the service map: a change in one service ripples to its
consumers, shared contracts, and downstream events.

```markdown
## Impact Analysis & Impact Areas

### Affected Areas
| Area / Module / Service | Change Type | Risk | Regression Scope |
|-------------------------|-------------|------|------------------|
| [this service/module] | new/changed behaviour | High/Med/Low | [existing flows to re-test] |
| [consumer / dependent] | contract unchanged / changed | Med | [smoke / full] |

### Downstream & Cross-Service Impact
- [Services/consumers that call this one or share its contracts — from plan.md integration points]
- [Events/queues/webhooks emitted or consumed]

### Data / Migration Impact
- [Schema changes, migrations, backfills, data compatibility]

### Regression Test Scope
- [Existing test suites / journeys to re-run because they pass through the impacted areas]
- [Explicitly note areas judged NOT impacted, with a one-line reason]
```

### Step 5 — Item Traceability Matrix (the core artefact)

Every testable item → test task → test cases → automation status → priority.

```markdown
## Traceability Matrix

| Item | Description | Test Task (tasks.md) | Test Cases | Automation | Priority |
|------|-------------|---------------------|------------|------------|----------|
| US1-AS1 | single rating filters | T010 [US1] | TC-001, TC-002 | Automated (Jest) | P1 |
| US1-AS2 | multi rating filters | T010 [US1] | TC-003 | Automated (Jest) | P1 |
| FR-001 | persist across pagination | T015 [US1] | TC-004 | Automated (unit) | P1 |
| FR-002 | result count updates | T016 [US1] | TC-005 | Automated (unit) | P1 |
| SC-001 | render < 500ms / 1000 hotels | T017 [US1] | TC-006 | Automated (perf) | P1 |
```

### Step 6 — Test Layers: Strategy, Ownership & Timing

Make the responsibility split explicit. **Unit/contract tests are developer-owned and planned
*before* `/speckit-implement`** (the TDD gate enforced by `/speckit-test-tasksaudit`). The
remaining layers are **QA-owned and prepared *after* implementation**.

```markdown
## Test Layers — Strategy, Ownership & Timing

| Layer | Purpose | Owner | When | Framework (constitution.md) | Est. Cases |
|-------|---------|-------|------|-----------------------------|-----------|
| Unit / Contract (TDD) | Fail-first capability/contract checks; the pre-implement gate | Developer | BEFORE /speckit-implement | [Jest / pytest / …] | ~6 |
| Integration | Scenario journeys, state across layers | Dev + QA | During / after implement | [Jest+Supertest / …] | ~4 |
| E2E | Full user flow | QA | AFTER implement | [Playwright / …] | ~2 |
| Regression | Re-test impacted existing areas (see Impact Analysis) | QA | AFTER implement | [existing suites] | scope-based |
| Performance | Buildable Success Criteria (SC-###) | QA | AFTER implement | [k6 / Jest perf / …] | ~1 |
| Accessibility | ARIA, keyboard, axe-core | QA | AFTER implement | jest-axe + manual | ~2 |
| Manual / Exploratory | Human-judgment edge cases | QA | AFTER implement | QA checklist | ~3 |
```

> Pre-implementation, only the Unit/Contract row is required (gate). QA completes the
> remaining rows after `/speckit-implement`, scoping Regression from the Impact Analysis.

### Step 7 — Test Cases by Item

For each item, derive cases from its text, boundaries, and edge cases. Acceptance Scenarios
map their Given/When/Then straight into Precondition/Steps/Expected.

```markdown
## Test Cases

### US1-AS1 — single rating filters the list (P1)
| TC-ID | Test Case | Precondition (Given) | Steps (When) | Expected (Then) | Level | Priority |
|-------|-----------|----------------------|--------------|-----------------|-------|----------|
| TC-001 | Single selection | Hotel list loaded | Select 3-star | Only 3-star shown; count updates | Integration | P1 |
| TC-002 | Empty result | No 1-star hotels | Select 1-star | Empty state; no crash | Integration/Edge | P1 |

**Acceptance threshold**: all P1 cases pass before merge.
```

Repeat per item.

### Step 8 — Entry / Exit Criteria

```markdown
## Entry Criteria
- All implementation tasks for the targeted stories are complete (marked [X] in tasks.md)
- Feature branch deployed to the test environment
- Test data / fixtures ready

## Exit Criteria
- All P1 test cases pass (automated + manual)
- Zero P1 defects open
- /speckit-test-coverage ≥ the constitution threshold (default: all P1 items Strong)
- /speckit-test-gaps reports 0 Critical gaps
- /speckit-analyze reports no unresolved CRITICAL/HIGH findings
- This test plan is linked in the PR description
```

### Step 9 — Test Environment

```markdown
## Test Environment

| Component | Requirement |
|-----------|------------|
| Environment | [staging/dev from plan.md] |
| Framework | [constitution.md] |
| Test data | [fixtures / seed] |
| External services | [stubs/mocks per plan.md] |
| Env variables | [names only, no secrets] |
| Browser (if UI) | [Chromium via Playwright / …] |
```

### Step 10 — Risk Assessment

```markdown
## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| [External service] down in test env | E2E fails | Recorded fixture / mock server |
| Schema not migrated before run | Integration fails | Run migrations in test setup |
| [spec.md NEEDS CLARIFICATION] unresolved | Behaviour undefined | Escalate to PM; block until resolved |
```

Every unresolved `[NEEDS CLARIFICATION]` from spec.md MUST appear here.

### Step 11 — Write the File(s)

- Always write/update `FEATURE_DIR/test-plan.md`.
- If `--also-checklist`: additionally seed `FEATURE_DIR/checklists/test.md` with a short
  coverage checklist (one `- [ ] CHK### <item> has a passing, ID-labelled test` per P1 item).
  Spec Kit's `/speckit-implement` gates on `checklists/*.md` completion, so this turns the
  plan into an enforceable pre-implementation gate. Append (continue CHK numbering) if it exists.

Report:
```markdown
## Test Plan Generated
File: specs/001-connect-hotel-filter/test-plan.md
Items: 5 | Test cases: 6 | P1: 6 | Manual: 2 | Automated: 4
(+ checklists/test.md seeded with 5 items)   ← only if --also-checklist
Next: fill test implementations, run /speckit-test-coverage, link this file in the PR.
```

## Rules

- **Item-driven** — every test case references a `US{n}-AS{m}` / `FR-###` / `SC-###`; no freestanding cases.
- **Matrix mandatory** — the traceability matrix (Step 5) appears in every plan; it is the primary QA artefact.
- **Impact analysis mandatory** — the Impact Analysis & Impact Areas section (Step 4) appears in every plan; it scopes regression and names cross-service/downstream effects from plan.md.
- **Ownership & timing explicit** — the layer table (Step 6) must state owner and when: unit/contract is developer-owned and pre-implement (the gate); integration/E2E/regression/perf/a11y/manual are QA-owned and post-implement.
- **No tech leakage in cases** — case descriptions state observable behaviour, not implementation (same rule as spec.md).
- **Out-of-scope excluded** — nothing the spec's `## Assumptions` mark out of scope gets a case.
- **P1 threshold explicit** — state "all P1 cases pass" as the acceptance threshold in every item section.
- **Framework from artefacts** — reference the real framework from constitution.md / plan.md, never a generic placeholder.
- **Exit criteria fixed** — always include the six exit criteria in Step 8.
- **Update, don't overwrite** — if test-plan.md exists, update it to reflect spec changes.
- **NEEDS CLARIFICATION → risk** — every unresolved one becomes a risk with "Escalate to PM".
- **`[P]` is parallelism** — when reading tasks.md, identify test tasks by Tests subsection / test path, never by `[P]`.
