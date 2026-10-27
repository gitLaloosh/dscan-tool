"""ERRORS.md from index.html's ERROR_CODES registry (v2026.10.14.32), plus a consistency check.

    python3 -I tools/gen_errors_md.py [index.html]           # check: must print "ERRORS.md is up to date"
    python3 -I tools/gen_errors_md.py [index.html] --write   # rewrite ERRORS.md

Every error message the page writes ends with a short code, e.g. "... (ZKB-01)". ERROR_CODES in index.html is
the one place a code is defined. This script fails when:
  * a code is used in index.html (codedError('X-01', ...), withCode(..., 'X-01'), code: 'X-01', or a literal
    "(X-01)" in a message) but isn't in ERROR_CODES;
  * a code in ERROR_CODES is never used (except APP-01, the fallback for errors without a code, and rows marked
    "status": "retired");
  * ERRORS.md differs from what the registry generates.
Rules (also in ERRORS.md): never reuse or renumber a code; a retired error keeps its row with "status": "retired".
"""
import sys, os, re, json

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
src = open(html, encoding='utf-8').read()
m = re.search(r'const ERROR_CODES = (\{.*?\n\});', src, re.S)
if not m: sys.exit('ERROR_CODES not found in ' + html)
reg = json.loads(m.group(1))
rest = src[:m.start()] + src[m.end():]
# v2026.10.14.45: fields name page parts as {card:key}; the names come from CARD_NAMES (roadmap/card-names.md).
cn = re.search(r'const CARD_NAMES = (\{.*?\n\});', src, re.S)
CARD_NAMES = json.loads(cn.group(1)) if cn else {}

CODE = r'[A-Z]+-\d\d'
used = set(re.findall(r"['\"](" + CODE + r")['\"]", rest)) | set(re.findall(r'\((' + CODE + r')\)', rest))
used.discard('APP-01')   # referenced through errorCodeOf()'s fallback
problems = []
for c in sorted(used - set(reg)): problems.append(f'{c} is used in index.html but not in ERROR_CODES')
for c, r in sorted(reg.items()):
    if c != 'APP-01' and r.get('status') != 'retired' and c not in used:
        problems.append(f'{c} is in ERROR_CODES but never used (mark it "status": "retired" instead of deleting it)')
    for k in ('title', 'where', 'trigger', 'check', 'since'):
        if not r.get(k): problems.append(f'{c}: missing "{k}"')
    if not re.fullmatch(CODE, c): problems.append(f'{c}: code must look like ABC-01')
    for k, v in r.items():
        for key in re.findall(r'\{card:([\w.]+)\}', v if isinstance(v, str) else ''):
            if key not in CARD_NAMES: problems.append(f'{c}.{k}: {{card:{key}}} is not in CARD_NAMES')

def names(t): return re.sub(r'\{card:([\w.]+)\}', lambda mm: CARD_NAMES.get(mm.group(1), mm.group(0)), t or '')
def cell(t): return names(t).replace('|', '\\|').replace('\n', ' ')
groups = {'APP': 'The page itself', 'ESI': 'ESI (CCP\'s API)', 'ZKB': 'zKillboard', 'DSCAN': 'System Analyzer: the D-Scan box', 'SYS': 'System Analyzer: Local', 'SIDE': 'Your Side',
          'PILOT': 'Pilot Analyzer', 'FIT': 'Fit Analyzer', 'MYSHIP': 'My Ship'}
order = list(groups)
out = ['# Error codes', '',
       'Every error EVE Threat Assessment shows ends with a code, for example "... (ZKB-01)". To report a problem,',
       'give the code and the version tag at the top right of the page.', '',
       'Generated from `ERROR_CODES` in `index.html` by `tools/gen_errors_md.py`; do not edit by hand. Rules: a code is',
       'never reused or renumbered; a retired error keeps its row, marked retired. Prompts for an empty box ("Enter a',
       'pilot name.", "Paste a fit first.") carry no code: they are instructions, not errors.', '']
for pre in sorted({c.split('-')[0] for c in reg}, key=lambda p: (order.index(p) if p in order else 99, p)):
    out += [f'## {groups.get(pre, pre)}', '', '| Code | What | Where | Cause | What to check | Why it exists | Since |', '|---|---|---|---|---|---|---|']
    for c in sorted(k for k in reg if k.split('-')[0] == pre):
        r = reg[c]
        since = r['since'] + (f" ([{r['doc']}](dscan-tool-history/{r['doc']}))" if r.get('doc') else '')
        title = r['title'] + (' **(retired)**' if r.get('status') == 'retired' else '')
        out.append(f"| {c} | {cell(title)} | {cell(r['where'])} | {cell(r['trigger'])} | {cell(r['check'])} | {cell(r.get('why'))} | {cell(since)} |")
    out.append('')
text = '\n'.join(out)
md = os.path.join(ROOT, 'ERRORS.md')
if '--write' in sys.argv and not problems:
    open(md, 'w', encoding='utf-8').write(text); print('wrote', md)
else:
    cur = open(md, encoding='utf-8').read() if os.path.exists(md) else None
    if cur != text: problems.append('ERRORS.md is out of date (run with --write)')
for p in problems: print('PROBLEM:', p)
print(f'{len(reg)} codes, {len(used) + 1} in use; ' + ('ERRORS.md is up to date' if not problems else f'{len(problems)} problems'))
sys.exit(1 if problems else 0)
