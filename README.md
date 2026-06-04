# speckit-test-extension — SDET Edition

A [Spec Kit](https://github.com/github/spec-kit) extension built from the perspective of an
Expert QA Engineer / SDET. Adds the complete testing layer that connects `spec.md`
Acceptance Criteria to test tasks, test files, and pre-merge sign-off — closing the loop
that Spec Kit's core workflow leaves open.

Adapted from [spec-kit-spectest](https://github.com/Quratulain-bilal/spec-kit-spectest)
by Quratulain-bilal (MIT). Key changes are listed under [Differences](#differences-from-upstream).

---

## Problem

Spec Kit's core workflow (`/speckit.specify` → `/speckit.plan` → `/speckit.tasks` →
`/speckit.implement`) produces detailed `spec.md` Acceptance Criteria and a
`tasks.md` task breakdown — but leaves the testing layer entirely manual:

- ACs exist in `spec.md` but no tool checks that `tasks.md` has a test task for each one
- Developers write tests from memory, not from spec — traceability breaks
- There is no way to measure "which ACs are actually tested" before the PR is approved
- QA pre-merge checks are done ad-hoc from a checklist document

This extension closes those gaps.

---

## Commands

| Command | Step in QA Process | What it does |
|---------|-------------------|--------------|
| `/speckit.test.tasksaudit` | Step 3 — Tasks Audit | Verify every AC has a `T00x [P]` test task before implementation starts |
| `/speckit.test.generate` | Step 5 — Scaffold | Generate AC-tagged test scaffolds from spec.md |
| `/speckit.test.plan` | Step 4 — Test Plan | Write `testplan-NNN-feature.md` inside `specs/NNN-*/` |
| `/speckit.test.coverage` | Step 6 — Coverage | Map AC-N → test file, rate Strong/Medium/Weak confidence |
| `/speckit.test.gaps` | Step 6 — Gaps | Find ACs with no test task or no test file (CI-friendly) |
| `/speckit.test.review` | Step 7 — Pre-merge | Full QA gate: stub scan, traceability chain, constitution check, scope drift |

---

## How It Fits the SDD Pipeline

```
/speckit.specify          → spec.md (AC-1, AC-2, AC-3...)
/speckit.clarify          → spec.md updated
                            ↓
                   [QA: /speckit.test.tasksaudit]   ← Step 3 gate
                   Blocks /speckit.implement if any AC
                   has no T00x [P] test task
                            ↓
/speckit.plan             → plan.md
/speckit.tasks            → tasks.md  (T001 [P] test (AC-1)...)
                            ↓
                   [QA: /speckit.test.plan]         ← Step 4
                   Writes testplan-NNN-feature.md
                            ↓
/speckit.implement        → source code + test scaffolds
                            ↓
                   [QA: /speckit.test.generate]     ← Step 5
                   Scaffolds tests per AC if not already present
                            ↓
Fill in test implementations
                            ↓
                   [QA: /speckit.test.coverage]     ← Step 6 check
                   [QA: /speckit.test.gaps]         ← Step 6 gaps
                            ↓
                   [QA: /speckit.test.review]       ← Step 7 gate
                   Pre-merge sign-off
                            ↓
PR approved + merged
```

---

## Installation

```bash
specify extension add --from https://github.com/<your-org>/speckit-test-extension/archive/refs/tags/v1.0.0.zip
```

Or, to use locally from this repo:

```bash
# From the repo root, after specify init
specify extension add --from ./speckit-test-extension
```

Requires Spec Kit >= 0.8.13 (pinned version recommended for consistent templates).

---

## Key Conventions

This extension is built around expert QA/SDET conventions for the SDD workflow:

| Convention | Detail |
|------------|--------|
| **Spec folder** | `specs/NNN-name/spec.md` (not `.specify/spec.md`) |
| **AC identifiers** | `AC-1`, `AC-2`, … (not `REQ-001`) |
| **Test tasks** | `T00x [P]` pattern in `tasks.md` |
| **Automation tags** | `[MANUAL]`, `[AUTO]`, `[BOTH]` on every test task |
| **Test plan** | `specs/NNN-*/testplan-NNN-feature.md` |
| **Test framework** | Declared in `.specify/memory/constitution.md` |
| **Stub detection** | `expect(true)`, `.toBe(true)`, `.todo`, `.skip`, `throw new Error('TODO')` are all treated as stubs |
| **Traceability** | Every `describe`/`it` label must include `AC-N:` for Strong confidence |

---

## Hooks

| Hook | Command | Behaviour |
|------|---------|-----------|
| `before_implement` | `/speckit.test.tasksaudit` | **Mandatory** — blocks implementation if any AC lacks a test task |
| `after_implement` | `/speckit.test.gaps` | **Optional** — prompts QA to scan for untested ACs |

---

## Differences from Upstream

Based on [spec-kit-spectest v1.0.0](https://github.com/Quratulain-bilal/spec-kit-spectest).

| Area | Upstream | This extension |
|------|----------|----------------|
| Requirement IDs | `REQ-001` | `AC-N` (matches spec.md format) |
| Spec location | `.specify/spec.md` | `specs/NNN-*/spec.md` |
| Test plan output | `.specify/test-plan.md` | `specs/NNN-*/testplan-NNN-feature.md` |
| Tasks.md awareness | Not checked | `/speckit.test.tasksaudit` — core QA gate |
| Automation tags | None | `[MANUAL]`, `[AUTO]`, `[BOTH]` required per test task |
| Constitution enforcement | None | All commands read `constitution.md` QA rules |
| Stub detection | Not present | All review commands flag `TODO`/`.skip`/`expect(true)` stubs |
| Pre-merge gate | None | `/speckit.test.review` — full Step 7 sign-off |
| `before_implement` hook | None | Mandatory tasks audit before implementation starts |
| New command | — | `/speckit.test.tasksaudit` and `/speckit.test.review` |

---

## License

MIT — same as upstream.
