#!/usr/bin/env python3
"""Render the extract-rules workflow's result into BUSINESS_RULES.md and DATA_OBJECTS.md.

    python3 render_rules.py <system> [--workspace DIR] [--result FILE]

Reads analysis/<system>/rules_result.json (the object the workflow returned, saved by the
command) and writes analysis/<system>/BUSINESS_RULES.md and DATA_OBJECTS.md. Rules are
numbered RULE-001, RULE-002, ... in the order they appear (by category, then priority) and the heading is always
`### RULE-NNN: <name>`, the pattern later commands and the pane look for. Every value comes
from analysis of untrusted code, so it is written as plain text on one line where it is
a heading or a table cell. Standard library only.
"""
import json
import os
import re
import sys

CATEGORIES = ['Calculation', 'Validation', 'Lifecycle', 'Policy']
PRIORITY = {'P0': 0, 'P1': 1, 'P2': 2}


def one_line(value, limit=300):
    text = ' '.join(str(value if value is not None else '').split())
    text = text.replace('|', '/').replace('`', "'")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + '…'


CITATION = re.compile(r'^\s*`?([^\s`:,;()]+):(\d+)(?:\s*[-\u2013]\s*(\d+))?')


def split_citation(value):
    """One citation per rule: the first path:line[-line] in the text is it, and whatever follows
    (a second file, a note) comes back separately so later tools can rely on the citation alone."""
    text = ' '.join(str(value if value is not None else '').split())
    m = CITATION.match(text)
    if not m:
        return one_line(text, 200), ''
    primary = f'{m.group(1)}:{m.group(2)}' + (f'-{m.group(3)}' if m.group(3) else '')
    rest = re.sub(r'\s*;\s*also\s+', '; ', text[m.end():], flags=re.I)       # citations a consolidation appended
    rest = re.sub(r'^[\s;,.\-\u2013\u2014`]*(?:also\s+)?', '', rest, flags=re.I)
    return one_line(primary, 200), one_line(rest.strip(' \t;,.-\u2013\u2014`'), 300)


def block(value):
    """Multi-line text: keep the lines, but never let a value open a heading or a fence."""
    lines = []
    for raw in str(value if value is not None else '').splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith(('#', '```', '~~~')):
            line = '\\' + line.lstrip()
        lines.append(line)
    return '\n'.join(lines).strip()


def render_rule(number, rule):
    rid = f'RULE-{number:03d}'
    source, also = split_citation(rule.get('source'))
    out = [f"### {rid}: {one_line(rule.get('name'), 120)}",
           f"**Category:** {one_line(rule.get('category'), 20)}",
           f"**Priority:** {one_line(rule.get('priority'), 4)}",
           f"**Source:** `{source.replace(chr(39), '')}`"]
    if also:
        out.append(f'**Also cited:** {also}')
    out += [f"**Plain English:** {one_line(rule.get('plainEnglish'), 400)}",
           '**Specification:**',
           f"  Given {block(rule.get('given'))}",
           f"  When  {block(rule.get('when'))}",
           f"  Then  {block(rule.get('then'))}"]
    if rule.get('and'):
        out.append(f"  And   {block(rule['and'])}")
    if rule.get('parameters'):
        out.append(f"**Parameters:** {block(rule['parameters'])}")
    cases = rule.get('edgeCases') or []
    if cases:
        out.append('**Edge cases handled:** ' + '; '.join(one_line(c, 200) for c in cases))
    if rule.get('suspectedDefect'):
        out.append(f"**Suspected defect:** {block(rule['suspectedDefect'])}")
    confidence = one_line(rule.get('confidence'), 10)
    question = rule.get('smeQuestion')
    out.append(f"**Confidence:** {confidence}" + (f" — {one_line(question, 400)}" if question and confidence != 'High' else ''))
    return rid, '\n'.join(out)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith('--')]
    workspace, result_path = '.', None
    if '--workspace' in argv:
        workspace = argv[argv.index('--workspace') + 1]
        args = [a for a in args if a != workspace]
    if '--result' in argv:
        result_path = argv[argv.index('--result') + 1]
        args = [a for a in args if a != result_path]
    if not args:
        print('usage: render_rules.py <system> [--workspace DIR] [--result FILE]', file=sys.stderr)
        return 2
    system = args[0]
    base = os.path.join(workspace, 'analysis', system)
    result_path = result_path or os.path.join(base, 'rules_result.json')
    try:
        with open(result_path, encoding='utf-8') as handle:
            result = json.load(handle)
    except (OSError, ValueError) as error:
        print(f'Cannot read {result_path}: {error}', file=sys.stderr)
        return 1

    # Numbered in the order they appear in the document (by category, then priority), so RULE-001.. read in sequence.
    rules = sorted(result.get('confirmedRules') or [],
                   key=lambda r: (CATEGORIES.index(r['category']) if r.get('category') in CATEGORIES else 9,
                                  PRIORITY.get(r.get('priority'), 1),
                                  str(r.get('source'))))
    numbered = [(i + 1, r) for i, r in enumerate(rules)]
    rendered = {n: render_rule(n, r) for n, r in numbered}
    stats = result.get('stats') or {}

    doc = [f'# Business Rules — {one_line(system, 80)}', '',
           f"At extraction: {len(rules)} confirmed rules ({sum(1 for r in rules if r.get('priority') == 'P0')} P0); "
           f"later steps may add or correct rules below. "
           f"Each citation was checked by a second agent that read the cited lines; "
           f"{len(result.get('rejectedRules') or [])} candidate rules were refuted and left out.", '',
           '| ID | Name | Category | Priority | Source | Confidence |', '|---|---|---|---|---|---|']
    for n, r in numbered:
        doc.append(f"| RULE-{n:03d} | {one_line(r.get('name'), 80)} | {one_line(r.get('category'), 20)} | "
                   f"{one_line(r.get('priority'), 4)} | `{split_citation(r.get('source'))[0][:80].replace(chr(39), '')}` | {one_line(r.get('confidence'), 10)} |")
    doc.append('')
    for category in CATEGORIES + [None]:
        group = [n for n, r in numbered if (r.get('category') if r.get('category') in CATEGORIES else None) == category]
        if not group:
            continue
        doc += [f"## {category or 'Other'}", '']
        for n in group:
            doc += [rendered[n][1], '']
    sme = [(n, r) for n, r in numbered if r.get('confidence') != 'High']
    doc += ['## Rules requiring SME confirmation', '']
    if sme:
        for n, r in sme:
            doc.append(f"- **RULE-{n:03d}** ({one_line(r.get('confidence'), 10)}): "
                       f"{one_line(r.get('smeQuestion') or 'Confirm this rule with someone who knows the system.', 400)}")
    else:
        doc.append('None: every confirmed rule has High confidence.')
    doc.append('')

    flags = result.get('injectionFlags') or []
    if flags:
        doc += ['## ⚠ Instruction-shaped content found in source', '',
                'These lines of the source tried to steer automated analysis. A person should look at them.', '']
        doc += [f'- {one_line(f, 300)}' for f in flags]
        doc.append('')

    folded = [f for f in (result.get('foldedRules') or []) if isinstance(f, dict)]
    if folded:
        doc += ['## Rules folded into another', '',
                'These rules described the same behavior as another rule in a different place, so they were merged into it '
                '(the kept rule lists their locations under "Also cited"):', '']
        doc += [f"- {one_line(f.get('name'), 100)} ({one_line(f.get('source'), 100)}) into {one_line(f.get('into'), 100)}" for f in folded[:100]]
        if len(folded) > 100:
            doc.append(f'- … and {len(folded) - 100} more')
        doc.append('')

    gaps = [('never attempted (token budget or agent cap)', stats.get('skippedModules')),
            ('extractor returned nothing', stats.get('failedModules')),
            ('malformed entries, fix by hand', stats.get('droppedModules')),
            ('phases cut short', stats.get('skippedPhases')),
            ('candidate rules no referee judged (not in the catalog)',
             [f"{one_line(u.get('name'), 80)} ({one_line(u.get('source'), 80)})" for u in (result.get('unverifiedRules') or [])])]
    gaps = [(label, items) for label, items in gaps if items]
    if gaps:
        doc += ['## Coverage gaps', '', 'These parts were NOT fully mined:', '']
        for label, items in gaps:
            doc.append(f"- **{len(items)} {label}:** " + ', '.join(one_line(i, 100) for i in items[:30]) + (' …' if len(items) > 30 else ''))
        if result.get('rerunModules'):
            doc.append(f"\nA follow-up run for the {len(result['rerunModules'])} affected shard(s) covers them.")
        doc.append('')

    with open(os.path.join(base, 'BUSINESS_RULES.md'), 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(doc))

    objects = result.get('dataObjects') or []
    dto = [f'# Data Objects — {one_line(system, 80)}', '']
    if not objects:
        dto.append('No data objects were cataloged.')
    for obj in objects:
        dto += [f"## {one_line(obj.get('name'), 100)}", f"Source: `{one_line(obj.get('source'), 160).replace(chr(39), '')}`", '',
                '| Field | Type | Note |', '|---|---|---|']
        for field in obj.get('fields') or []:
            dto.append(f"| {one_line(field.get('name'), 80)} | {one_line(field.get('type'), 60)} | {one_line(field.get('note'), 160)} |")
        used = obj.get('consumedBy') or []
        if used:
            dto += ['', 'Used by: ' + ', '.join(one_line(u, 80) for u in used)]
        dto.append('')
    with open(os.path.join(base, 'DATA_OBJECTS.md'), 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(dto))

    p0 = sum(1 for r in rules if r.get('priority') == 'P0')
    print(f"BUSINESS_RULES.md: {len(rules)} rules ({p0} P0, {len(sme)} need SME review); DATA_OBJECTS.md: {len(objects)} objects; "
          f"rejected {len(result.get('rejectedRules') or [])}, unverified {len(result.get('unverifiedRules') or [])}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
