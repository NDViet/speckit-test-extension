"""
update_sdd_v2b.py — Second-pass patch on QA_Testing_Process_SDD_v2.docx

Changes:
  1. Rename "QA Responsibility" → "Quality Responsibility" in artifacts table header
  2. Update every artifact row so Dev AND QA quality ownership is explicit
  3. Prepend a "The Quality Spec Kit Workflow" overview to Section 3 (pipeline + role split + gate model)
  4. Update TDD Gate principle to describe the Dev/QA ownership split correctly
  5. Add enforceability note to Section 4 constitution
  6. Fix /speckit-test-generate description to include "any item still missing a test"
  7. Update Section 1 intro to mention both Dev and QA lanes

Based on the extension README ("The Quality Spec Kit workflow" section).
"""

import copy
import sys

try:
    from docx import Document
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'python-docx', '-q'])
    from docx import Document
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

INPUT_PATH  = '/home/user/speckit-test-extension/QA_Testing_Process_SDD_v2.docx'
OUTPUT_PATH = '/home/user/speckit-test-extension/QA_Testing_Process_SDD_v2.docx'

NS_SPACE = '{http://www.w3.org/XML/1998/namespace}space'


# ---------------------------------------------------------------------------
# Helpers (same as v2 script)
# ---------------------------------------------------------------------------

def first_text(elem):
    return ''.join(t.text or '' for t in elem.iter(qn('w:t')))


def replace_text_in(elem, old, new):
    all_t = list(elem.iter(qn('w:t')))
    full = ''.join(t.text or '' for t in all_t)
    if old not in full:
        return False
    new_full = full.replace(old, new, 1)
    if all_t:
        all_t[0].text = new_full
        all_t[0].set(NS_SPACE, 'preserve')
        for t in all_t[1:]:
            t.text = ''
    return True


def set_cell_text(cell_elem, new_text):
    paras = cell_elem.findall(qn('w:p'))
    if not paras:
        return
    para = paras[0]
    for r in list(para.findall(qn('w:r'))):
        para.remove(r)
    for child in list(para):
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag not in ('pPr',):
            para.remove(child)
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    sz = OxmlElement('w:sz'); sz.set(qn('w:val'), '20')
    szCs = OxmlElement('w:szCs'); szCs.set(qn('w:val'), '20')
    rPr.append(sz); rPr.append(szCs)
    r.append(rPr)
    t = OxmlElement('w:t')
    t.set(NS_SPACE, 'preserve')
    t.text = new_text
    r.append(t)
    para.append(r)


def make_paragraph(style_val, text, bold=False, italic=False, font_size='20', font_name=None):
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    if style_val:
        pStyle = OxmlElement('w:pStyle')
        pStyle.set(qn('w:val'), style_val)
        pPr.append(pStyle)
    p.append(pPr)
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    if font_name:
        rFonts = OxmlElement('w:rFonts')
        rFonts.set(qn('w:ascii'), font_name)
        rFonts.set(qn('w:hAnsi'), font_name)
        rPr.append(rFonts)
    if bold:
        rPr.append(OxmlElement('w:b'))
        rPr.append(OxmlElement('w:bCs'))
    if italic:
        rPr.append(OxmlElement('w:i'))
        rPr.append(OxmlElement('w:iCs'))
    if font_size:
        sz = OxmlElement('w:sz'); sz.set(qn('w:val'), font_size)
        rPr.append(sz)
    r.append(rPr)
    t = OxmlElement('w:t')
    t.set(NS_SPACE, 'preserve')
    t.text = text
    r.append(t)
    p.append(r)
    return p


def make_code_paragraph(text):
    """Paragraph styled for pipeline/code display — Normal style, Courier New."""
    return make_paragraph('Normal', text, font_name='Courier New', font_size='18')


def insert_before(body, ref_elem, new_elem):
    children = list(body)
    idx = children.index(ref_elem)
    body.insert(idx, new_elem)


def find_heading(body, level, contains):
    style_name = f'Heading{level}'
    for child in body:
        if not child.tag.endswith('}p'):
            continue
        pPr = child.find(qn('w:pPr'))
        if pPr is None:
            continue
        pStyle = pPr.find(qn('w:pStyle'))
        if pStyle is None:
            continue
        val = pStyle.get(qn('w:val'), '')
        if style_name.lower() in val.lower():
            if contains.lower() in first_text(child).lower():
                return child
    return None


def next_table_after(body, elem):
    children = list(body)
    idx = children.index(elem)
    for sibling in children[idx + 1:]:
        if sibling.tag.endswith('}tbl'):
            return sibling
    return None


def get_table_rows(tbl):
    return tbl.findall(qn('w:tr'))


def get_cells(row):
    return row.findall(qn('w:tc'))


def copy_row_with_texts(template_row, cell_texts):
    new_row = copy.deepcopy(template_row)
    cells = get_cells(new_row)
    for i, text in enumerate(cell_texts):
        if i < len(cells):
            set_cell_text(cells[i], text)
    return new_row


# ---------------------------------------------------------------------------
# Gate model table builder
# ---------------------------------------------------------------------------

def make_gate_table(template_row):
    """Build a 3-row, 3-column gate model table from a template row."""
    tbl = OxmlElement('w:tbl')

    # Table properties (simple borders)
    tblPr = OxmlElement('w:tblPr')
    tblStyle = OxmlElement('w:tblStyle')
    tblStyle.set(qn('w:val'), 'TableGrid')
    tblPr.append(tblStyle)
    tblW = OxmlElement('w:tblW')
    tblW.set(qn('w:w'), '9360')
    tblW.set(qn('w:type'), 'dxa')
    tblPr.append(tblW)
    tbl.append(tblPr)

    rows_data = [
        ('Phase', 'Owner', 'Quality Gate / Actions'),
        ('Before /speckit-implement\n(Developer local)',
         'Developer',
         '/speckit-test-tasksaudit (mandatory before_implement hook)\n'
         '  Audit: every P1 US{n}-AS{m} and FR-### must have a unit/contract (TDD, fail-first) test task in tasks.md\n'
         '  BLOCKS /speckit-implement if any P1 task is missing (read-only; never edits tasks.md)\n'
         '  Fix: run --write to add the missing task lines to tasks.md, review, then re-run implement\n'
         '  Note: hook binds when working through /speckit-implement; pair with --also-checklist or CI check for stricter enforcement'),
        ('After /speckit-implement\n(PR opened — QA)',
         'QA Engineer',
         '/speckit-test-plan      → test-plan.md: impact analysis + QA test layers\n'
         '/speckit-test-generate  → scaffold integration/E2E/regression/perf/a11y tests and any item still missing a test\n'
         '/speckit-test-coverage  → map items to test files; rate Strong/Medium/Weak/Stub\n'
         '/speckit-test-gaps      → find untested items; severity Critical/Medium/Low\n'
         '/speckit-test-review    → pre-merge sign-off; GATE: APPROVED / GATE: BLOCKED'),
    ]

    header = True
    for row_texts in rows_data:
        new_row = copy.deepcopy(template_row)
        cells = get_cells(new_row)
        # Ensure 3 cells
        while len(cells) < 3:
            new_cell = copy.deepcopy(cells[-1])
            new_row.append(new_cell)
            cells = get_cells(new_row)
        for i, txt in enumerate(row_texts):
            if i < len(cells):
                set_cell_text(cells[i], txt)
        tbl.append(new_row)
        header = False

    return tbl


# ===========================================================================
# Main
# ===========================================================================

doc = Document(INPUT_PATH)
body = doc.element.body

print('Loaded v2. Applying patch...')

# ---------------------------------------------------------------------------
# 1. Rename "QA Responsibility" → "Quality Responsibility" in artifacts table
# ---------------------------------------------------------------------------
artifacts_tbl = None
for child in body:
    if not child.tag.endswith('}tbl'):
        continue
    txt = first_text(child)
    if 'constitution.md' in txt and 'tasks.md' in txt and 'spec.md' in txt:
        artifacts_tbl = child
        break

if artifacts_tbl:
    rows = get_table_rows(artifacts_tbl)
    if rows:
        # Header row — find the "QA Responsibility" / "Quality Responsibility" cell
        header_cells = get_cells(rows[0])
        for cell in header_cells:
            txt = first_text(cell)
            if 'QA Responsibility' in txt or 'Responsibility' in txt:
                replace_text_in(cell, 'QA Responsibility', 'Quality Responsibility')
                # If already updated, make sure it reads correctly
                if 'Quality Responsibility' not in first_text(cell):
                    set_cell_text(cell, 'Quality Responsibility')
                print('  [1] Renamed column header → Quality Responsibility')
                break

    # 2. Update each artifact row to show Dev AND QA quality ownership
    row_updates = {
        'spec.md': (
            'Dev: produces spec items (US{n}-AS{m}, FR-###, SC-###) via /speckit-specify and /speckit-clarify. '
            'QA: reviews before /speckit-plan — gap analysis, AC quality, boundary conditions, '
            'edge cases, cross-cutting concerns (a11y, i18n). '
            'QA runs /speckit-clarify to harden the spec.'
        ),
        'plan.md': (
            'Dev: produces technical architecture, API contracts, data shapes, error paths. '
            'QA: reviews for testability — explicit request/response shapes, state flows, '
            'integration points for stub/fixture strategies, non-functional requirements.'
        ),
        'tasks.md': (
            'Dev (mandatory): runs /speckit-test-tasksaudit (before_implement gate) — every P1 '
            'US{n}-AS{m} and FR-### must have a unit/contract test task; runs --write to add missing tasks. '
            'QA (advisory): may run /speckit-test-tasksaudit after /speckit-tasks to surface gaps early. '
            'Dev must NOT re-run /speckit-tasks after closing the gate (added tasks would be discarded).'
        ),
        'test-plan.md': (
            'QA: generates FEATURE_DIR/test-plan.md via /speckit-test-plan — traceability matrix, '
            'impact analysis, test layers (Dev-owned unit/contract vs. QA-owned integration/E2E/perf/a11y), '
            'entry/exit criteria, risks. Must be linked in PR description.'
        ),
        'Source': (
            'Dev: writes unit/contract tests FIRST (TDD, fail-first — tests must FAIL before implementation), '
            'then implements until green. '
            'QA: runs the five /speckit-test-* commands on the opened PR branch to generate test-plan.md, '
            'scaffold QA-layer tests, measure coverage, find gaps, and sign off.'
        ),
        'constitution.md': (
            'QA encodes non-negotiables (test framework, mandatory layers, coverage thresholds). '
            'Dev respects and may escalate via --require. '
            'Update: US{n}-AS{m}/FR-### mapping rule, no stub tests, /speckit-test-tasksaudit gate policy, '
            'any CI check requirements for the gate.'
        ),
    }

    for row in rows[1:]:
        cells = get_cells(row)
        if not cells:
            continue
        artifact_name = first_text(cells[0])
        for key, new_resp in row_updates.items():
            if key.lower() in artifact_name.lower():
                resp_cell = cells[2] if len(cells) > 2 else cells[-1]
                set_cell_text(resp_cell, new_resp)
                print(f'  [2] Updated Quality Responsibility for: {artifact_name.strip()[:30]}')
                break

    print('  Artifacts table done.')

# ---------------------------------------------------------------------------
# 3. Update TDD Gate principle in principles table (Section 1)
# ---------------------------------------------------------------------------
principles_tbl = None
for child in body:
    if not child.tag.endswith('}tbl'):
        continue
    txt = first_text(child)
    if 'Shift Left' in txt or 'Contract-Based' in txt:
        principles_tbl = child
        break

if principles_tbl:
    for row in get_table_rows(principles_tbl):
        cells = get_cells(row)
        if cells and 'TDD Gate' in first_text(cells[0]):
            if len(cells) > 1:
                set_cell_text(cells[1],
                    'Dev owns unit/contract tests (pre-implement, TDD gate via /speckit-test-tasksaudit). '
                    'QA owns integration/E2E/regression/performance/accessibility layers (post-implement, '
                    'planned in test-plan.md). The gate audits and BLOCKS /speckit-implement when a P1 '
                    'unit/contract test task is missing — it never edits tasks.md itself. '
                    'Dev runs --write to add the missing tasks, reviews, then re-runs implement.')
                print('  [3] Updated TDD Gate principle')

# ---------------------------------------------------------------------------
# 4. Fix /speckit-test-generate description in Step 5 (now includes missing items)
# ---------------------------------------------------------------------------
for child in body:
    if not child.tag.endswith('}p'):
        continue
    txt = first_text(child)
    if '/speckit-test-generate' in txt and '2nd QA command' in txt and 'missing a test' not in txt:
        replace_text_in(child, txt,
            'QA runs /speckit-test-generate on the opened PR branch (2nd QA command). '
            'Args: [US1-AS2 | FR-001 | SC-001] [unit|integration|e2e] [--dir tests/]. '
            'Scaffolds QA-owned layers (integration/E2E/regression/perf/a11y) and '
            'any spec item still missing a test. '
            'Auto-detects test framework from package.json (Jest/Vitest/Playwright), '
            'pyproject.toml (pytest), or go.mod (go test). '
            'Generates failing TDD scaffolds labelled with item IDs (e.g., "US1-AS1: ..."). '
            'Never overwrites existing test files. QA fills in assertion logic after implementation.')
        print('  [4] Updated /speckit-test-generate description')
        break

# ---------------------------------------------------------------------------
# 5. Add enforceability note to Section 4 — Constitution
# ---------------------------------------------------------------------------
sec4_h = find_heading(body, 1, '4.')
if not sec4_h:
    sec4_h = find_heading(body, 1, 'QA Requirements')
if sec4_h:
    children = list(body)
    sec4_idx = children.index(sec4_h)
    # Find last bullet in section 4 (within ~20 paragraphs)
    last_bullet = sec4_h
    for p in children[sec4_idx + 1:sec4_idx + 25]:
        if not p.tag.endswith('}p'):
            break
        if first_text(p).strip():
            last_bullet = p

    # Only add if not already present
    last_txt = first_text(last_bullet)
    if 'unbypassable' not in last_txt and 'enforceab' not in last_txt.lower():
        note = make_paragraph('',
            'Enforceability note: The before_implement hook binds when the developer works through '
            '/speckit-implement. To make the gate unbypassable regardless of how code is written, '
            'pair it with /speckit-test-plan --also-checklist (which seeds FEATURE_DIR/checklists/test.md '
            'and blocks /speckit-implement until it is checked off) and/or a required CI check on the PR.',
            italic=True)
        children = list(body)
        last_bullet_idx = children.index(last_bullet)
        body.insert(last_bullet_idx + 1, note)
        print('  [5] Added enforceability note to Section 4')

# ---------------------------------------------------------------------------
# 6. Prepend "The Quality Spec Kit Workflow" overview before Section 3 steps
# ---------------------------------------------------------------------------
sec3_h = find_heading(body, 1, '3.')
if not sec3_h:
    sec3_h = find_heading(body, 1, 'Step-by-Step')

if sec3_h:
    # We'll insert the workflow overview between the section heading and the first step heading
    step1_h = find_heading(body, 2, 'Step 1')

    if step1_h:
        # Build overview content (insert in reverse order so they appear top-to-bottom)
        overview_items = []

        # Overview heading
        overview_items.append(
            make_paragraph('Heading2', 'Workflow Overview — Quality Spec Kit Pipeline'))

        # Role-split one-liners
        overview_items.append(make_paragraph('',
            'The Quality Spec Kit workflow proves a feature was built right. '
            'Core Spec Kit steps are unchanged; quality steps are woven in at two points: '
            'a mandatory developer gate before implementation, and five QA commands on the opened PR.'))

        overview_items.append(make_paragraph('',
            'Developer lane (runs locally; opens the PR after implementing):'))
        overview_items.append(make_code_paragraph(
            '/speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks '
            '→ /speckit-test-tasksaudit ★ → /speckit-implement → open PR'))

        overview_items.append(make_paragraph('',
            'QA lane (inspects the PR):'))
        overview_items.append(make_code_paragraph(
            '/speckit-test-plan → /speckit-test-generate → /speckit-test-coverage '
            '→ /speckit-test-gaps → /speckit-test-review → ✅ approve'))

        overview_items.append(make_paragraph('',
            '★ = mandatory before_implement gate. '
            'Audits and BLOCKS if a P1 spec item has no unit/contract (TDD) test task. '
            'Developer runs /speckit-test-tasksaudit --write to add missing tasks to tasks.md, '
            'reviews the additions, then re-runs /speckit-implement.'))

        # Full pipeline heading
        overview_items.append(
            make_paragraph('Heading3', 'Full Pipeline (with all Spec Kit commands)'))
        pipeline_lines = [
            '/speckit-constitution       → constitution.md  (defines whether/which tests are mandatory)',
            '/speckit-specify            → spec.md           (User Stories: US{n}-AS{m}, FR-###, SC-###)',
            '/speckit-clarify            → spec.md updated',
            '/speckit-plan               → plan.md',
            '/speckit-tasks              → tasks.md',
            '   └─ [Dev] /speckit-test-tasksaudit   ← after_tasks hook (advisory audit)',
            '/speckit-checklist          → checklists/*.md  (requirements-quality gate)',
            '/speckit-analyze            → cross-artefact consistency report',
            '★  [Dev] /speckit-test-tasksaudit   ← before_implement hook (MANDATORY gate)',
            '         Audits & BLOCKS if a P1 unit/contract test task is missing',
            '         Run --write to add missing tasks to tasks.md, review, re-run implement',
            '/speckit-implement          → source + unit/contract tests (TDD: write tests first, FAIL → implement → GREEN)',
            '══════ Developer opens the PR ══════',
            '[QA] /speckit-test-plan     ← test-plan.md: impact analysis + QA test layers',
            '[QA] /speckit-test-generate ← scaffold QA-layer tests (and any item still missing a test)',
            '[QA] /speckit-test-coverage ← requirement-level coverage (Strong/Medium/Weak/Stub)',
            '[QA] /speckit-test-gaps     ← untested items (Critical/Medium/Low severity)',
            '[QA] /speckit-test-review   ← pre-merge sign-off → GATE: ✅ APPROVED / ❌ BLOCKED',
            'PR approved + merged',
        ]
        for line in pipeline_lines:
            overview_items.append(make_code_paragraph(line))

        # Gate model table — need a template row from any existing table
        gate_model_heading = make_paragraph('Heading3', 'Gate Model — Who Owns What and When')
        overview_items.append(gate_model_heading)

        # Spacer before Step 1
        overview_items.append(make_paragraph('', ''))

        # Insert all overview items before Step 1 heading, in reverse order
        for item in reversed(overview_items):
            insert_before(body, step1_h, item)
        print(f'  [6] Inserted Workflow Overview ({len(overview_items)} elements) before Step 1')

        # Now insert the gate model table after the gate model heading
        # Find the gate model heading in the (now updated) body
        gate_heading_node = find_heading(body, 3, 'Gate Model')
        if gate_heading_node:
            # Use any existing table row as template for cell formatting
            first_tbl = None
            for child in body:
                if child.tag.endswith('}tbl'):
                    rows = get_table_rows(child)
                    if rows:
                        first_tbl = child
                        break
            if first_tbl:
                template_row = get_table_rows(first_tbl)[0]
                gate_tbl = make_gate_table(template_row)
                # Insert after gate model heading
                children = list(body)
                gh_idx = children.index(gate_heading_node)
                body.insert(gh_idx + 1, gate_tbl)
                print('  [6b] Inserted gate model table')

# ---------------------------------------------------------------------------
# 7. Update Section 1 overview intro paragraph to mention both lanes
# ---------------------------------------------------------------------------
sec1_h = find_heading(body, 1, '1.')
if not sec1_h:
    sec1_h = find_heading(body, 1, 'Overview')
if sec1_h:
    children = list(body)
    sec1_idx = children.index(sec1_h)
    for p in children[sec1_idx + 1:sec1_idx + 5]:
        if not p.tag.endswith('}p'):
            continue
        txt = first_text(p)
        if len(txt) > 30 and ('process' in txt.lower() or 'QA' in txt or 'SDD' in txt):
            replace_text_in(p, txt,
                'This document defines the end-to-end quality process for both Developers and QA Engineers '
                'working on features governed by Spec-Driven Development (SDD) with the spectest-sdet extension. '
                'Quality responsibility is shared: Developers own the TDD unit/contract gate before implementation; '
                'QA owns the five post-implementation PR checks through to pre-merge sign-off. '
                'The spectest-sdet extension (speckit-test-extension v1.1.0) automates both lanes.')
            print('  [7] Updated Section 1 intro paragraph')
            break

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
doc.save(OUTPUT_PATH)
print(f'\nDone! Saved to: {OUTPUT_PATH}')
