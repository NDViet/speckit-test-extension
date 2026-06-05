"""
update_sdd_v2.py — Updates QA Testing Process SDD to v2.0

Incorporates speckit-test-extension (spectest-sdet v1.1.0) commands, purpose,
and workflow into the existing QA Testing Process SDD DOCX.
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

INPUT_PATH = '/root/.claude/uploads/b526558f-1dc6-44be-8467-2099c0ef8ba1/fc4516cb-QA_Testing_Process_SDD.docx'
OUTPUT_PATH = '/home/user/speckit-test-extension/QA_Testing_Process_SDD_v2.docx'

NS_SPACE = '{http://www.w3.org/XML/1998/namespace}space'


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def iter_texts(elem):
    """Yield all w:t elements under elem."""
    return elem.iter(qn('w:t'))


def first_text(elem):
    """Return concatenated text of all w:t children."""
    return ''.join(t.text or '' for t in iter_texts(elem))


def replace_text_in(elem, old, new):
    """Replace first occurrence of `old` substring across all w:t runs in elem."""
    all_t = list(iter_texts(elem))
    full = ''.join(t.text or '' for t in all_t)
    if old not in full:
        return False
    # Build combined replacement
    new_full = full.replace(old, new, 1)
    # Put everything in first run, blank the rest
    all_t[0].text = new_full
    all_t[0].set(NS_SPACE, 'preserve')
    for t in all_t[1:]:
        t.text = ''
    return True


def set_cell_text(cell_elem, new_text):
    """Replace all paragraph content in a table cell with a single plain-text run."""
    paras = cell_elem.findall(qn('w:p'))
    if not paras:
        return
    para = paras[0]
    # Remove every existing run
    for r in list(para.findall(qn('w:r'))):
        para.remove(r)
    # Also remove hyperlinks etc.
    for child in list(para):
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag not in ('pPr',):
            para.remove(child)
    # Insert new run
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), '20')
    szCs = OxmlElement('w:szCs')
    szCs.set(qn('w:val'), '20')
    rPr.append(sz)
    rPr.append(szCs)
    r.append(rPr)
    t = OxmlElement('w:t')
    t.set(NS_SPACE, 'preserve')
    t.text = new_text
    r.append(t)
    para.append(r)


def copy_row_with_texts(template_row, cell_texts):
    """Deep-copy a table row and set cell texts."""
    new_row = copy.deepcopy(template_row)
    cells = new_row.findall(qn('w:tc'))
    for i, text in enumerate(cell_texts):
        if i < len(cells):
            set_cell_text(cells[i], text)
    return new_row


def make_paragraph(style_val, text, bold=False, italic=False, font_size='20'):
    """Create a new w:p element with given style and text."""
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    if style_val:
        pStyle = OxmlElement('w:pStyle')
        pStyle.set(qn('w:val'), style_val)
        pPr.append(pStyle)
    p.append(pPr)

    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    if bold:
        rPr.append(OxmlElement('w:b'))
        rPr.append(OxmlElement('w:bCs'))
    if italic:
        rPr.append(OxmlElement('w:i'))
        rPr.append(OxmlElement('w:iCs'))
    if font_size:
        sz = OxmlElement('w:sz')
        sz.set(qn('w:val'), font_size)
        rPr.append(sz)
    r.append(rPr)

    t = OxmlElement('w:t')
    t.set(NS_SPACE, 'preserve')
    t.text = text
    r.append(t)
    p.append(r)
    return p


def make_list_para(text, num_id='2', ilvl='0'):
    """Create a ListParagraph bullet paragraph."""
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    pStyle = OxmlElement('w:pStyle')
    pStyle.set(qn('w:val'), 'ListParagraph')
    pPr.append(pStyle)
    numPr = OxmlElement('w:numPr')
    ilvl_el = OxmlElement('w:ilvl')
    ilvl_el.set(qn('w:val'), ilvl)
    numId_el = OxmlElement('w:numId')
    numId_el.set(qn('w:val'), num_id)
    numPr.append(ilvl_el)
    numPr.append(numId_el)
    pPr.append(numPr)
    p.append(pPr)

    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), '20')
    rPr.append(sz)
    r.append(rPr)
    t = OxmlElement('w:t')
    t.set(NS_SPACE, 'preserve')
    t.text = text
    r.append(t)
    p.append(r)
    return p


def insert_after(body, ref_elem, new_elem):
    """Insert new_elem immediately after ref_elem in body."""
    children = list(body)
    idx = children.index(ref_elem)
    body.insert(idx + 1, new_elem)


def insert_before(body, ref_elem, new_elem):
    """Insert new_elem immediately before ref_elem in body."""
    children = list(body)
    idx = children.index(ref_elem)
    body.insert(idx, new_elem)


def find_heading(body, level, contains):
    """Find a heading paragraph by style level and text content."""
    style_map = {1: 'Heading1', 2: 'Heading2', 3: 'Heading3'}
    style = style_map.get(level, f'Heading{level}')
    for child in body:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag != 'p':
            continue
        pPr = child.find(qn('w:pPr'))
        if pPr is None:
            continue
        pStyle = pPr.find(qn('w:pStyle'))
        if pStyle is None:
            continue
        val = pStyle.get(qn('w:val'), '')
        if style.lower() in val.lower():
            txt = first_text(child)
            if contains.lower() in txt.lower():
                return child
    return None


def find_para_containing(body, text):
    """Find first paragraph whose text contains the given string."""
    for child in body:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag != 'p':
            continue
        if text in first_text(child):
            return child
    return None


def next_sibling(body, elem, skip_types=None):
    """Return the next body sibling after elem, optionally skipping certain tag names."""
    children = list(body)
    idx = children.index(elem)
    for sibling in children[idx + 1:]:
        tag = sibling.tag.split('}')[-1] if '}' in sibling.tag else sibling.tag
        if skip_types and tag in skip_types:
            continue
        return sibling
    return None


def next_table_after(body, elem):
    """Return the first table after elem in body."""
    children = list(body)
    idx = children.index(elem)
    for sibling in children[idx + 1:]:
        tag = sibling.tag.split('}')[-1] if '}' in sibling.tag else sibling.tag
        if tag == 'tbl':
            return sibling
    return None


def get_table_rows(tbl_elem):
    return tbl_elem.findall(qn('w:tr'))


def get_cells(row_elem):
    return row_elem.findall(qn('w:tc'))


def global_replace(body, replacements):
    """Apply a list of (old, new) text replacements across ALL paragraphs in body."""
    for child in body:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'p':
            for old, new in replacements:
                replace_text_in(child, old, new)
        elif tag == 'tbl':
            for cell in child.iter(qn('w:tc')):
                for para in cell.findall(qn('w:p')):
                    for old, new in replacements:
                        replace_text_in(para, old, new)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

doc = Document(INPUT_PATH)
body = doc.element.body

print('Document loaded. Applying updates...')

# ===========================================================================
# PHASE 1: IN-PLACE TEXT REPLACEMENTS (no index shifting)
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. Section 1 — Overview: tooling header & traceability chain
# ---------------------------------------------------------------------------

# 1a. Tooling header line
p = find_para_containing(body, 'Tooling: Speckit')
if p:
    replace_text_in(p,
        'Tooling: Speckit',
        'Tooling: Speckit · spectest-sdet')
    print('  [1a] Updated tooling header')

# 1b. Traceability principle in overview table (cell text)
# Find the principles table (first table in the doc)
principles_tbl = None
for child in body:
    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
    if tag == 'tbl':
        principles_tbl = child
        break

if principles_tbl:
    rows = get_table_rows(principles_tbl)
    for row in rows:
        cells = get_cells(row)
        for cell in cells:
            txt = first_text(cell)
            if 'AC → Task ID' in txt or 'AC -> Task ID' in txt or 'AC → Test Case' in txt:
                set_cell_text(cell,
                    'Every test case maps: spec item (US{n}-AS{m} / FR-### / SC-###) '
                    '→ test task → test file → CI result.')
                print('  [1b] Updated traceability principle cell')

# ---------------------------------------------------------------------------
# 2. Section 2 — Artifacts table
# ---------------------------------------------------------------------------
# Find the artifacts table by looking for "tasks.md" and "spec.md" content
artifacts_tbl = None
for child in body:
    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
    if tag == 'tbl':
        txt = first_text(child)
        if 'constitution.md' in txt and 'tasks.md' in txt:
            artifacts_tbl = child
            break

if artifacts_tbl:
    rows = get_table_rows(artifacts_tbl)
    for row in rows:
        cells = get_cells(row)
        if not cells:
            continue
        row_text = first_text(cells[0])
        # tasks.md row — update QA responsibility
        if 'tasks.md' in row_text:
            if len(cells) >= 3:
                resp_text = first_text(cells[2])
                if 'T00x [P] pattern' in resp_text or 'test task' in resp_text.lower():
                    set_cell_text(cells[2],
                        'Run /speckit-test-tasksaudit (mandatory before_implement gate) to verify every '
                        'P1 spec item (US{n}-AS{m}, FR-###) has a unit/contract test task. '
                        'Use --write to add missing tasks. Test tasks are identified by '
                        '"### Tests for User Story N" subsection or test path — not by [P] marker.')
                    print('  [2a] Updated tasks.md artifact row')
    print('  [2] Artifacts table updated')

# ---------------------------------------------------------------------------
# 3. Section 3 — Step 3: Test Task Audit
# ---------------------------------------------------------------------------
step3_h = find_heading(body, 2, 'Step 3')
if step3_h:
    # Update trigger paragraph (first non-empty para after heading)
    p = next_sibling(body, step3_h)
    if p is not None:
        txt = first_text(p)
        if '/speckit.tasks has run' in txt or 'Trigger' in txt:
            replace_text_in(p,
                txt,
                'Trigger: /speckit.tasks has run. Run /speckit-test-tasksaudit — '
                'the MANDATORY before_implement gate. Every P1 Acceptance Scenario '
                '(US{n}-AS{m}) and Functional Requirement (FR-###) must have a unit/contract '
                '(TDD, fail-first) test task in tasks.md before /speckit-implement runs. '
                'Developer runs /speckit-test-tasksaudit (audit-only, read-only); '
                'then /speckit-test-tasksaudit --write to add missing tasks; reviews and re-runs implement.')
            print('  [3a] Updated Step 3 trigger paragraph')

    # Update Step 3 audit table
    step3_tbl = next_table_after(body, step3_h)
    if step3_tbl:
        rows = get_table_rows(step3_tbl)
        for row in rows:
            cells = get_cells(row)
            if not cells:
                continue
            c0 = first_text(cells[0])
            c1 = first_text(cells[1]) if len(cells) > 1 else ''

            if 'AC → Test Task' in c0 or 'AC-N' in c0 or 'AC → test task' in c0.lower():
                set_cell_text(cells[0], 'Spec item → Test Task mapping')
                set_cell_text(cells[1] if len(cells) > 1 else cells[0],
                    'For every US{n}-AS{m} (P1) and FR-### in spec.md, a unit/contract test task must exist '
                    'in tasks.md. Run /speckit-test-tasksaudit (audit-only) to get the gate report; '
                    'run with --write to add missing task lines. '
                    'CI summary: SPECTEST AUDIT: [N] gated items, [M] with unit/contract tests, [G] gaps, [S] stubs — PASS|FAIL')
                print('  [3b] Updated Step 3 table row: spec item mapping')

            if '[P]' in c0 and ('test' in c0.lower() or 'automation' in c0.lower()):
                set_cell_text(cells[0], '[P] means parallelizable')
                if len(cells) > 1:
                    set_cell_text(cells[1],
                        '[P] = parallelizable (Spec Kit semantics, not a test marker). '
                        'Test tasks are found by "### Tests for User Story N" subsection or test path/description. '
                        '[MANUAL]/[AUTO]/[BOTH] automation tags are NOT required on task text; '
                        'automation type is inferred by reporting commands.')
                print('  [3c] Updated Step 3 table row: [P] marker')

            if 'testplan-NNN' in c1:
                replace_text_in(cells[1] if len(cells) > 1 else cells[0],
                    'testplan-NNN', 'FEATURE_DIR/test-plan.md (run /speckit-test-plan)')
                print('  [3d] Updated Step 3 table testplan reference')

    # Update Step 3 note paragraph
    children = list(body)
    step3_idx = children.index(step3_h)
    for p in children[step3_idx + 1:step3_idx + 15]:
        tag = p.tag.split('}')[-1] if '}' in p.tag else p.tag
        if tag != 'p':
            continue
        txt = first_text(p)
        if 'missing test tasks' in txt and ('blocking' in txt or 'QA' in txt or 'raise' in txt):
            replace_text_in(p, txt,
                'Note: The before_implement hook runs /speckit-test-tasksaudit automatically and BLOCKS '
                'if any P1 unit/contract tasks are missing. Developer runs /speckit-test-tasksaudit --write '
                'to add the missing tasks to tasks.md, reviews the additions, then re-runs /speckit-implement. '
                '/speckit-test-tasksaudit can also run after /speckit-tasks (advisory mode, surfaces gaps early).')
            print('  [3e] Updated Step 3 note paragraph')
            break

# ---------------------------------------------------------------------------
# 4. Section 3 — Step 4: Test Plan Creation
# ---------------------------------------------------------------------------
step4_h = find_heading(body, 2, 'Step 4')
if step4_h:
    replace_text_in(step4_h, first_text(step4_h),
        'Step 4 — Test Plan Creation (/speckit-test-plan)')
    print('  [4a] Updated Step 4 heading')

    # Update description paragraph
    p = next_sibling(body, step4_h)
    if p is not None:
        txt = first_text(p)
        if 'testplan' in txt or 'QA creates' in txt or 'Create' in txt:
            replace_text_in(p, txt,
                'QA runs /speckit-test-plan on the opened PR branch (1st QA command). '
                'Output: FEATURE_DIR/test-plan.md. '
                'Optional: FEATURE_DIR/checklists/test.md with --also-checklist flag. '
                'Flags: --audience qa|dev, --scope smoke|regression|full. '
                'Updates the file if it already exists.')
            print('  [4b] Updated Step 4 description')

    # Update Step 4 table
    step4_tbl = next_table_after(body, step4_h)
    if step4_tbl:
        rows = get_table_rows(step4_tbl)
        updates = [
            ('Feature', 'Feature Summary',
             'Feature name, spec.md link, branch, actor, date, status, test framework'),
            ('Test Objectives', 'Scope',
             'In-scope items (US{n}-AS{m}, FR-###, SC-###); out-of-scope from Assumptions; '
             '--scope smoke|regression|full'),
            ('AC Traceability', 'Traceability Matrix',
             'Table: US{n}-AS{m}/FR-###/SC-### → test layer → test cases → task ID → automation status → priority'),
            ('Test Types', 'Impact Analysis',
             'Affected modules, downstream impact, regression scope — derived from spec.md and plan.md'),
            ('Entry', 'Entry / Exit Criteria',
             'Entry: PR opened, spec items identified. Exit: all P1 items covered (Strong/Medium), /speckit-test-review APPROVED'),
            ('Test Environment', 'Test Layers',
             'Dev lane (unit/contract, pre-implement, TDD) vs. QA lane (integration/E2E/regression/perf/a11y, post-implement). '
             'Includes layer ownership, timing, framework, estimated cases.'),
            ('Risk', 'Risks and Mitigations',
             'Folds in all unresolved [NEEDS CLARIFICATION] from spec.md; lists mitigations'),
        ]
        for row in rows[1:]:  # skip header row
            cells = get_cells(row)
            if not cells:
                continue
            c0_txt = first_text(cells[0])
            for match_str, new_c0, new_c1 in updates:
                if match_str.lower() in c0_txt.lower():
                    set_cell_text(cells[0], new_c0)
                    if len(cells) > 1:
                        set_cell_text(cells[1], new_c1)
                    break
        print('  [4c] Updated Step 4 test-plan sections table')

# ---------------------------------------------------------------------------
# 5. Section 3 — Step 5: Test Case Generation → Test Scaffold Generation
# ---------------------------------------------------------------------------
step5_h = find_heading(body, 2, 'Step 5')
if step5_h:
    replace_text_in(step5_h, first_text(step5_h),
        'Step 5 — Test Scaffold Generation (/speckit-test-generate)')
    print('  [5a] Updated Step 5 heading')

    p = next_sibling(body, step5_h)
    if p is not None:
        txt = first_text(p)
        if txt and len(txt) > 10:
            replace_text_in(p, txt,
                'QA runs /speckit-test-generate on the opened PR branch (2nd QA command). '
                'Args: [US1-AS2 | FR-001 | SC-001] [unit|integration|e2e] [--dir tests/]. '
                'Auto-detects test framework from package.json (Jest/Vitest/Playwright), '
                'pyproject.toml (pytest), or go.mod (go test). '
                'Generates failing TDD scaffolds labelled with item IDs (e.g., "US1-AS1: ..."). '
                'Never overwrites existing test files. QA fills in assertion logic after implementation.')
            print('  [5b] Updated Step 5 description')

# ---------------------------------------------------------------------------
# 6. Section 3 — Step 6: Automated Test Generation/Maintenance
# ---------------------------------------------------------------------------
step6_h = find_heading(body, 2, 'Step 6')
if step6_h:
    replace_text_in(step6_h, first_text(step6_h),
        'Step 6 — Automated Test Maintenance')
    print('  [6a] Updated Step 6 heading')

# ---------------------------------------------------------------------------
# 7. Section 3 — Step 7: Pre-Merge Validation
# ---------------------------------------------------------------------------
step7_h = find_heading(body, 2, 'Step 7')
if step7_h:
    # Update intro paragraph
    p = next_sibling(body, step7_h)
    if p is not None:
        txt = first_text(p)
        if txt and ('PR' in txt or 'Before' in txt or 'validate' in txt.lower()):
            replace_text_in(p, txt,
                'QA runs /speckit-test-review on the opened PR branch (5th and final QA command). '
                'Flags: --strict, --skip-analyze, --base main, --feature specs/NNN-name. '
                'Checks: item→task mapping, stub scan, coverage spot-check, /speckit-analyze consistency, '
                'scope-drift, traceability chain, test-plan presence, constitution compliance. '
                'Outputs a Blocker/Major/Minor findings table. '
                'Final verdict: GATE: ✅ APPROVED / GATE: ❌ BLOCKED. '
                'CI summary: SPECTEST REVIEW: [B] blockers, [M] major, [N] minor — BLOCKED|APPROVED.')
            print('  [7a] Updated Step 7 intro')

    # Update Step 7 pre-merge checklist table
    step7_tbl = next_table_after(body, step7_h)
    if step7_tbl:
        rows = get_table_rows(step7_tbl)
        for row in rows[1:]:  # skip header
            cells = get_cells(row)
            if not cells:
                continue
            c0 = first_text(cells[0])
            c1 = first_text(cells[1]) if len(cells) > 1 else ''
            c2 = first_text(cells[2]) if len(cells) > 2 else ''

            if 'Every AC has a test task' in c0 or ('AC' in c0 and 'test task' in c0):
                set_cell_text(cells[0], 'Every P1 spec item has a unit/contract test task')
                if len(cells) > 1:
                    set_cell_text(cells[1],
                        '/speckit-test-tasksaudit gate was PASS; '
                        '/speckit-test-review confirms item→task mapping')
                print('  [7b] Updated Step 7: spec item test task row')

            if 'test task has a test file' in c0 or 'test file' in c0:
                if len(cells) > 1:
                    set_cell_text(cells[1],
                        'Grep for item ID (US{n}-AS{m}/FR-###) in test file labels; '
                        '/speckit-test-gaps Gap-B count = 0')
                print('  [7c] Updated Step 7: test file row')

            if 'stub' in c0.lower() or 'No stub' in c0:
                if len(cells) > 1:
                    set_cell_text(cells[1],
                        '/speckit-test-review stub scan; /speckit-test-coverage Stub-rated items = 0 on P1')
                print('  [7d] Updated Step 7: stub test row')

            if 'Manual tests executed' in c0 or 'Manual test' in c0:
                set_cell_text(cells[0], 'test-plan.md present and linked')
                if len(cells) > 1:
                    set_cell_text(cells[1],
                        'FEATURE_DIR/test-plan.md exists and is linked in PR description; '
                        'generated by /speckit-test-plan')
                print('  [7e] Updated Step 7: test-plan row')

            if 'speckit.analyze' in c0 or '/speckit-analyze' in c0 or 'analyze' in c0.lower():
                set_cell_text(cells[0], '/speckit-analyze run')
                if len(cells) > 1:
                    set_cell_text(cells[1],
                        'No unresolved findings from /speckit-analyze; '
                        '/speckit-test-review folds these in automatically')
                print('  [7f] Updated Step 7: speckit-analyze row')

            if 'Edge cases' in c0 or 'edge case' in c0.lower():
                if len(cells) > 1:
                    set_cell_text(cells[1],
                        '/speckit-test-gaps Gap-C (all-stub) critical count = 0; '
                        'empty state, error path, boundary inputs all tested')
                print('  [7g] Updated Step 7: edge cases row')

        print('  [7] Step 7 checklist table updated')

# ---------------------------------------------------------------------------
# 8. Section 4 — Constitution non-negotiables
# ---------------------------------------------------------------------------
sec4_h = find_heading(body, 1, '4.')
if not sec4_h:
    sec4_h = find_heading(body, 1, 'QA Requirements')
if sec4_h:
    children = list(body)
    sec4_idx = children.index(sec4_h)
    for p in children[sec4_idx + 1:sec4_idx + 20]:
        tag = p.tag.split('}')[-1] if '}' in p.tag else p.tag
        if tag != 'p':
            continue
        txt = first_text(p)
        if 'Every AC in spec.md maps' in txt or ('AC' in txt and 'test task' in txt and 'maps' in txt):
            replace_text_in(p, txt,
                'Every P1 spec item (US{n}-AS{m}, FR-###) in spec.md maps to at least one unit/contract '
                'test task in tasks.md. /speckit-test-tasksaudit enforces this as the mandatory '
                'before_implement gate. --advisory is an explicit, recorded opt-out.')
            print('  [8a] Updated constitution: AC mapping bullet')
        if 'T00x [P]' in txt or 'Test tasks follow' in txt:
            replace_text_in(p, txt,
                'Test tasks are identified by a "### Tests for User Story N" subsection or a test '
                'path/description in tasks.md. [P] means parallelizable — it is NOT a test marker. '
                '[MANUAL]/[AUTO]/[BOTH] tags are not required; automation type is inferred for reports.')
            print('  [8b] Updated constitution: test task pattern bullet')
        if 'testplan-NNN-feature.md' in txt and 'PR description' in txt:
            replace_text_in(p, 'testplan-NNN-feature.md', 'FEATURE_DIR/test-plan.md')
            print('  [8c] Updated constitution: testplan filename')

# ---------------------------------------------------------------------------
# 9. Section 5 — When SDD Applies: update AC references in table
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 10. Section 6 — Traceability Model
# ---------------------------------------------------------------------------
sec6_h = find_heading(body, 1, '6.')
if not sec6_h:
    sec6_h = find_heading(body, 1, 'Traceability')
if sec6_h:
    children = list(body)
    sec6_idx = children.index(sec6_h)
    for p in children[sec6_idx + 1:sec6_idx + 10]:
        tag = p.tag.split('}')[-1] if '}' in p.tag else p.tag
        if tag != 'p':
            continue
        txt = first_text(p)
        if 'spec.md AC-N' in txt or ('AC-N' in txt and 'test task' in txt):
            replace_text_in(p, txt,
                'spec item (US{n}-AS{m} / FR-### / SC-###)  '
                '→  tasks.md test task  '
                '→  test file (labelled with item ID)  '
                '→  CI result')
            print('  [9a] Updated traceability chain paragraph')
        if 'Enables' in txt or 'enables' in txt:
            if 'impact analysis' in txt:
                replace_text_in(p, txt,
                    'Enables: impact analysis when spec items change, '
                    'requirement-level coverage reporting (/speckit-test-coverage), '
                    'gap severity triage (/speckit-test-gaps), '
                    'reviewer navigation from spec to test, '
                    'and post-merge defect tracing to weak or missing test coverage.')
                print('  [9b] Updated traceability enables paragraph')

# ---------------------------------------------------------------------------
# 11. Section 8 — Quick Reference: checklist updates
# ---------------------------------------------------------------------------
sec8_h = find_heading(body, 1, '8.')
if not sec8_h:
    sec8_h = find_heading(body, 1, 'Quick Reference')
if sec8_h:
    children = list(body)
    sec8_idx = children.index(sec8_h)
    for p in children[sec8_idx + 1:sec8_idx + 50]:
        tag = p.tag.split('}')[-1] if '}' in p.tag else p.tag
        if tag != 'p':
            continue
        txt = first_text(p)
        if 'AC-N → T00x [P]' in txt or ('AC-N' in txt and 'T00x' in txt):
            replace_text_in(p, txt,
                'US{n}-AS{m}/FR-### → unit/contract test task mapping complete '
                '(run /speckit-test-tasksaudit)')
            print('  [10a] Updated Quick Reference: task mapping bullet')
        if '[MANUAL], [AUTO], or [BOTH]' in txt:
            replace_text_in(p, txt,
                '/speckit-test-tasksaudit --write gate PASS before running /speckit-implement')
            print('  [10b] Updated Quick Reference: automation tag bullet')
        if 'testplan-NNN-feature.md linked' in txt or ('testplan-NNN' in txt and 'PR' in txt):
            replace_text_in(p, 'testplan-NNN-feature.md', 'FEATURE_DIR/test-plan.md')
            print('  [10c] Updated Quick Reference: testplan filename in checklist')
        if 'Traceability chain' in txt and 'AC →' in txt:
            replace_text_in(p, txt,
                'Traceability chain complete: US{n}-AS{m}/FR-### '
                '→ test task → test file (ID labelled) → CI result')
            print('  [10d] Updated Quick Reference: traceability chain bullet')
        if 'speckit.analyze run' in txt or ('/speckit-analyze' in txt and 'unresolved' in txt):
            replace_text_in(p, txt,
                '/speckit-analyze run — no unresolved findings. '
                '/speckit-test-review GATE: ✅ APPROVED before merge.')
            print('  [10e] Updated Quick Reference: analyze bullet')

# ---------------------------------------------------------------------------
# 12. Global AC-N reference cleanup across the whole document
# ---------------------------------------------------------------------------
global_replace(body, [
    ('(AC-1)', '(US1-AS1)'),
    ('(AC-2)', '(US1-AS2)'),
    ('(AC-3)', '(US1-AS3)'),
    ('(AC-4)', '(US1-AS4)'),
    ('AC-1:', 'US1-AS1:'),
    ('AC-2:', 'US1-AS2:'),
    ('AC-1 ', 'US1-AS1 '),
    ('AC-2 ', 'US1-AS2 '),
])
print('  [12] Global AC-N example references updated')

print('\nPhase 1 complete. Applying insertions...')

# ===========================================================================
# PHASE 2: INSERTIONS (working bottom-to-top)
# ===========================================================================

# Refresh body reference
body = doc.element.body

# ---------------------------------------------------------------------------
# A. Glossary — append new rows (Section 9)
# ---------------------------------------------------------------------------
sec9_h = find_heading(body, 1, '9.')
if not sec9_h:
    sec9_h = find_heading(body, 1, 'Glossary')
if sec9_h:
    glossary_tbl = next_table_after(body, sec9_h)
    if glossary_tbl:
        rows = get_table_rows(glossary_tbl)
        # Update existing rows
        for row in rows:
            cells = get_cells(row)
            if not cells:
                continue
            term = first_text(cells[0])
            if 'AC' == term.strip() or term.strip() == 'AC':
                set_cell_text(cells[0], 'AC / Acceptance Scenario')
                if len(cells) > 1:
                    set_cell_text(cells[1],
                        'Acceptance Criterion (legacy term). Now superseded by Acceptance Scenario '
                        '(US{n}-AS{m}): a Given/When/Then testable statement in spec.md. '
                        'P1 scenarios are gated by /speckit-test-tasksaudit.')
                print('  [A1] Updated Glossary: AC row')
            if 'tasks.md' in term:
                if len(cells) > 1:
                    set_cell_text(cells[1],
                        'Atomic task breakdown T001…Tnnn. Test tasks identified by '
                        '"### Tests for User Story N" subsection or test path/description. '
                        '[P] = parallelizable (not a test marker). '
                        'constitution.md is the only Speckit file committed to git.')
                print('  [A2] Updated Glossary: tasks.md row')
            if 'Traceability chain' in term:
                if len(cells) > 1:
                    set_cell_text(cells[1],
                        'US{n}-AS{m}/FR-### → test task → test file (labelled with item ID) '
                        '→ CI result. Maintained end-to-end by the spectest-sdet commands '
                        '(/speckit-test-coverage, /speckit-test-gaps, /speckit-test-review).')
                print('  [A3] Updated Glossary: traceability chain row')

        # Get template row (second row = first data row)
        template_row = rows[1] if len(rows) > 1 else rows[0]
        new_entries = [
            ('Acceptance Scenario',
             'US{n}-AS{m} — a Given/When/Then scenario under a User Story in spec.md. '
             'P1 scenarios are gated: each must have a unit/contract test task '
             'in tasks.md before /speckit-implement.'),
            ('Functional Requirement',
             'FR-### — a MUST/SHOULD requirement in the Functional Requirements section '
             'of spec.md. P1 FRs are gated by /speckit-test-tasksaudit, like Acceptance Scenarios.'),
            ('Success Criterion',
             'SC-### — a measurable outcome in the Success Criteria section of spec.md '
             '(perf, security, availability). Advisory at the pre-implement gate; '
             'QA-owned post-implementation. Business KPI criteria are excluded entirely.'),
            ('spectest-sdet',
             'The speckit-test-extension v1.1.0 — the SDET testing layer for Spec Kit. '
             'Provides: /speckit-test-tasksaudit, /speckit-test-plan, /speckit-test-generate, '
             '/speckit-test-coverage, /speckit-test-gaps, /speckit-test-review. '
             'Requires Spec Kit ≥ 0.8.13.'),
            ('Confidence rating',
             'Coverage strength for a spec item: Strong (test label cites item ID), '
             'Medium (keyword match in label), Weak (file maps to story only, no ID/keywords), '
             'Stub (0% — test body always passes). Used by /speckit-test-coverage and '
             '/speckit-test-review.'),
            ('Blocker / Major / Minor',
             '/speckit-test-review severity levels. '
             'Blocker = must not merge (P1 stub, unit gate failed, Constitution MUST violated). '
             'Major = fix or justify in PR comment (scope drift, weak traceability, P2/P3 stub). '
             'Minor = should fix, may defer (label fix, terminology drift).'),
            ('test-plan.md',
             'QA-authored test plan at FEATURE_DIR/test-plan.md. Generated by /speckit-test-plan. '
             'Contains: feature summary, scope, impact analysis, traceability matrix, test layers, '
             'test cases, entry/exit criteria, environment, risks. Must be linked in the PR description.'),
        ]
        for term, definition in new_entries:
            new_row = copy_row_with_texts(template_row, [term, definition])
            glossary_tbl.append(new_row)
        print(f'  [A] Appended {len(new_entries)} rows to Glossary table')

# ---------------------------------------------------------------------------
# B. Tools table — append 6 new speckit-test rows (Section 7)
# ---------------------------------------------------------------------------
sec7_h = find_heading(body, 1, '7.')
if not sec7_h:
    sec7_h = find_heading(body, 1, 'QA Tools')
if sec7_h:
    tools_tbl = next_table_after(body, sec7_h)
    if tools_tbl:
        rows = get_table_rows(tools_tbl)
        template_row = rows[-1] if rows else None
        if template_row:
            new_tools = [
                ('/speckit-test-tasksaudit',
                 'Pre-implement TDD gate (Dev — mandatory before_implement hook)',
                 'Audits P1 US{n}-AS{m}/FR-### vs. unit/contract tasks. --write adds missing tasks. '
                 'SPECTEST AUDIT CI summary. Also runs advisory after /speckit-tasks.'),
                ('/speckit-test-plan',
                 'Test plan generation (QA — 1st PR command)',
                 'Writes FEATURE_DIR/test-plan.md: traceability matrix, impact analysis, test layers, '
                 'entry/exit criteria. --also-checklist seeds checklists/test.md.'),
                ('/speckit-test-generate',
                 'Test scaffold generation (QA — 2nd PR command)',
                 'Scaffolds failing TDD tests from spec items. Auto-detects Jest/Vitest/Playwright/pytest/go test. '
                 'Item ID in every label. Never overwrites existing files.'),
                ('/speckit-test-coverage',
                 'Coverage report (QA — 3rd PR command)',
                 'Maps items to test files. Confidence: Strong/Medium/Weak/Stub. '
                 '--min sets threshold. SPECTEST COVERAGE CI summary.'),
                ('/speckit-test-gaps',
                 'Gap analysis (QA — 4th PR command)',
                 'Finds untested items. Gap types A (no task)/B (no file)/C (all stubs)/D (no ID label). '
                 'Severity: Critical/Medium/Low/Warning. SPECTEST GAPS CI summary.'),
                ('/speckit-test-review',
                 'Pre-merge sign-off (QA — 5th PR command)',
                 'Full QA gate: item→task mapping, stub scan, coverage, /speckit-analyze, scope-drift, '
                 'traceability chain, constitution compliance. GATE: APPROVED/BLOCKED verdict.'),
            ]
            for tool_name, use_case, notes in new_tools:
                new_row = copy_row_with_texts(template_row, [tool_name, use_case, notes])
                tools_tbl.append(new_row)
            print(f'  [B] Appended {len(new_tools)} rows to Tools table')

# ---------------------------------------------------------------------------
# C. Insert new Steps 5b and 5c before Step 6 heading
# ---------------------------------------------------------------------------
step6_h = find_heading(body, 2, 'Step 6')
if step6_h:
    # Step 5c — /speckit-test-gaps (insert first so 5b ends up above 5c)
    gaps_desc = make_paragraph('',
        'QA runs /speckit-test-gaps on the opened PR branch (4th QA command). '
        'Flags: --critical-only, --story US1, --json|--checklist. '
        'Gap types: A (no test task), B (task exists but no file), '
        'C (test file exists but all bodies are stubs), D (no item ID in test label). '
        'Severity: Critical (P1 missing/stub, or auth/payment/security item), '
        'Medium (user-facing P1/P2), Low (P3 or cosmetic), Warning (weak traceability). '
        'CI summary: SPECTEST GAPS: [C] critical, [M] medium, [L] low, [W] warnings — PASS|FAIL')
    gaps_h = make_paragraph('Heading2', 'Step 5c — Gap Analysis (/speckit-test-gaps)')
    insert_before(body, step6_h, gaps_desc)
    insert_before(body, gaps_desc, gaps_h)
    print('  [C1] Inserted Step 5c (Gap Analysis)')

    # Step 5b — /speckit-test-coverage (insert before Step 5c heading)
    cov_desc = make_paragraph('',
        'QA runs /speckit-test-coverage on the opened PR branch (3rd QA command). '
        'Flags: --item FR-001, --summary, --json, --min 90. '
        'Confidence ratings: Strong (test label cites exact item ID), '
        'Medium (label matches item keywords), Weak (file maps to story, no ID/keywords), '
        'Stub (test body always passes — counts as 0% coverage). '
        'Outputs a coverage map and per-category summary. '
        'CI summary: SPECTEST COVERAGE: [N] items — [M] covered ([%]), [S] no tests, [T] stubs — PASS|BELOW THRESHOLD')
    cov_h = make_paragraph('Heading2', 'Step 5b — Coverage Report (/speckit-test-coverage)')
    insert_before(body, gaps_h, cov_desc)
    insert_before(body, cov_desc, cov_h)
    print('  [C2] Inserted Step 5b (Coverage Report)')

# ---------------------------------------------------------------------------
# D. Add new "TDD Gate" row to principles table (Section 1)
# ---------------------------------------------------------------------------
principles_tbl = None
for child in body:
    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
    if tag == 'tbl':
        txt = first_text(child)
        if 'Shift Left' in txt or 'Contract-Based' in txt:
            principles_tbl = child
            break

if principles_tbl:
    rows = get_table_rows(principles_tbl)
    if len(rows) >= 2:
        template_row = rows[1]
        tdd_row = copy_row_with_texts(template_row, [
            'TDD Gate',
            '/speckit-test-tasksaudit runs as a mandatory before_implement hook: '
            'every P1 Acceptance Scenario (US{n}-AS{m}) and Functional Requirement (FR-###) '
            'must have a unit/contract (fail-first) test task in tasks.md before '
            '/speckit-implement runs. Developers run --write to add missing tasks; '
            'they review and re-run implement.'
        ])
        principles_tbl.append(tdd_row)
        print('  [D] Added TDD Gate row to principles table')

# ---------------------------------------------------------------------------
# E. Add test-plan.md artifact row to artifacts table (Section 2)
# ---------------------------------------------------------------------------
artifacts_tbl = None
for child in body:
    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
    if tag == 'tbl':
        txt = first_text(child)
        if 'constitution.md' in txt and 'tasks.md' in txt and 'spec.md' in txt:
            artifacts_tbl = child
            break

if artifacts_tbl:
    rows = get_table_rows(artifacts_tbl)
    # Find tasks.md row to use as template and insert position
    tasks_row = None
    for row in rows:
        cells = get_cells(row)
        if cells and 'tasks.md' in first_text(cells[0]):
            tasks_row = row
            break
    if tasks_row:
        new_row = copy_row_with_texts(tasks_row, [
            'test-plan.md',
            '/speckit-test-plan',
            'QA-authored test plan with traceability matrix, impact analysis, test layers, '
            'entry/exit criteria, risks. Generated by /speckit-test-plan on the PR branch. '
            'Must be linked in PR description.',
            'After PR opened'
        ])
        # Insert after tasks_row
        tbl_children = list(artifacts_tbl)
        tasks_idx = tbl_children.index(tasks_row)
        artifacts_tbl.insert(tasks_idx + 1, new_row)
        print('  [E] Inserted test-plan.md row into Artifacts table')

# ---------------------------------------------------------------------------
# F. Insert "PR Inspection" checklist in Section 8
# ---------------------------------------------------------------------------
# Find the "Tasks Audit" heading in Section 8 and insert a new checklist after it
tasks_audit_h3 = None
for child in body:
    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
    if tag != 'p':
        continue
    pPr = child.find(qn('w:pPr'))
    if pPr is None:
        continue
    pStyle = pPr.find(qn('w:pStyle'))
    if pStyle is None:
        continue
    val = pStyle.get(qn('w:val'), '')
    if 'Heading3' in val or 'heading3' in val.lower():
        txt = first_text(child)
        if 'Tasks Audit' in txt or 'Step 3' in txt:
            tasks_audit_h3 = child
            break

# Also look for the Pre-Merge Sign-off heading in Section 8
premerge_h3 = None
for child in body:
    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
    if tag != 'p':
        continue
    pPr = child.find(qn('w:pPr'))
    if pPr is None:
        continue
    pStyle = pPr.find(qn('w:pStyle'))
    if pStyle is None:
        continue
    val = pStyle.get(qn('w:val'), '')
    if 'Heading3' in val or 'heading3' in val.lower():
        txt = first_text(child)
        if 'Pre-Merge' in txt or 'Sign-off' in txt or 'Step 7' in txt:
            premerge_h3 = child
            break

# Insert PR Inspection checklist before Pre-Merge heading
if premerge_h3:
    pr_items = [
        '/speckit-test-plan — FEATURE_DIR/test-plan.md generated with traceability matrix, '
        'impact analysis, and test layers',
        '/speckit-test-generate — QA-layer test scaffolds generated and reviewed (no stubs)',
        '/speckit-test-coverage — all P1 items rated Strong or Medium (zero P1 Stubs)',
        '/speckit-test-gaps — zero Critical gaps (Gap A/B/C on P1 items)',
        '/speckit-test-review — GATE: ✅ APPROVED, no Blocker findings',
    ]
    # Insert items in reverse order so they end up in correct order
    for item_text in reversed(pr_items):
        bullet = make_list_para(item_text)
        insert_before(body, premerge_h3, bullet)

    # Insert the heading before the first bullet
    pr_h3 = make_paragraph('Heading3', 'PR Inspection — QA Commands (Steps 4–7)')
    # Find first inserted bullet
    children = list(body)
    premerge_idx = children.index(premerge_h3)
    # The bullets are right before premerge_h3
    first_bullet_idx = premerge_idx - len(pr_items)
    body.insert(first_bullet_idx, pr_h3)
    print(f'  [F] Inserted PR Inspection checklist ({len(pr_items)} items) before Pre-Merge section')

# Add /speckit-test-review bullet to Pre-Merge checklist if not already present
if premerge_h3:
    children = list(body)
    premerge_idx = children.index(premerge_h3)
    # Find last bullet after premerge heading (within next 15 paras)
    last_bullet = None
    for p in children[premerge_idx + 1:premerge_idx + 16]:
        tag = p.tag.split('}')[-1] if '}' in p.tag else p.tag
        if tag != 'p':
            break
        txt = first_text(p)
        if txt.strip():
            last_bullet = p
    if last_bullet and '/speckit-test-review' not in first_text(last_bullet):
        review_bullet = make_list_para(
            '/speckit-test-review GATE: ✅ APPROVED — no Blockers, no unresolved Major findings')
        insert_after(body, last_bullet, review_bullet)
        print('  [F2] Added /speckit-test-review bullet to Pre-Merge checklist')

# ===========================================================================
# SAVE
# ===========================================================================
doc.save(OUTPUT_PATH)
print(f'\nDone! Saved to: {OUTPUT_PATH}')
