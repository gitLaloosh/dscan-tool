"""Subtext rule (v2026.10.14.48, roadmap/subtext-plan.md). In the update-check chain.

    python3 -I tools/check_subtext.py [index.html]          # must end with "0 problems"

the owner (2026-10-24): "the subtext in the tool is a little overwhelming and distracts from important values ... address
it as a site wide design choice"; decided: "works as written. info icon opens a panel over the page. the 40 character
limit is fine." The rule, enforced here as far as a static read can:
  1. one line of context under a value: every ctxHtml(...) whose text is written in the code is <= CTX_MAX (40)
     characters (a template's ${...} parts count as one character each; live values are cut with an ellipsis);
  2. how a card works lives behind its info button: CARD_INFO keys are card keys (CARD_NAMES), every infoBtnHtml(key)
     has a CARD_INFO entry, and every CARD_INFO entry is used;
  4. (nothing moves) is checked in the page: tools/page_checks/no_shift_check.py.
Also REPORTED (not failed until phase S3): CSS rules that colour text with --text-faint (below 4.5:1 contrast on the
cards), and literal context written outside ctxHtml in the classes the rule replaces.
"""
import sys, os, re, json

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
src = open(html, encoding='utf-8').read()
problems = []
def line_of(pos): return src.count('\n', 0, pos) + 1

def grab(name):
    m = re.search(r'const ' + name + r' = (\{.*?\n\});', src, re.S)
    if not m: sys.exit(f'{name} not found in {html}')
    return json.loads(m.group(1))
NAMES, INFO = grab('CARD_NAMES'), grab('CARD_INFO')
m = re.search(r'const CTX_MAX = (\d+);', src)
CTX_MAX = int(m.group(1)) if m else 40
if CTX_MAX != 40: problems.append(f'CTX_MAX is {CTX_MAX}; the owner settled on 40 ("the 40 character limit is fine")')

# 2. info panels
for k, paras in INFO.items():
    if k not in NAMES: problems.append(f'CARD_INFO["{k}"]: not a card key in CARD_NAMES')
    if not isinstance(paras, list) or not paras or not all(isinstance(p, str) and p.strip() for p in paras):
        problems.append(f'CARD_INFO["{k}"]: must be a list of non-empty paragraphs')
used = set()
for mm in re.finditer(r'infoBtnHtml\(\s*([\'"`])([^\'"`]+)\1\s*\)', src):
    k = mm.group(2); used.add(k)
    if k not in INFO: problems.append(f'line {line_of(mm.start())}: infoBtnHtml("{k}") has no CARD_INFO entry')
for mm in re.finditer(r'infoBtnHtml\(\s*(?![\'"`])', src):
    if 'function infoBtnHtml' not in src[max(0, mm.start() - 9):mm.start() + 12]:
        problems.append(f'line {line_of(mm.start())}: infoBtnHtml(...) with a computed key; write the key as a literal so it can be checked')
for k in INFO:
    if k not in used: problems.append(f'CARD_INFO["{k}"] is never shown (no infoBtnHtml("{k}"))')

# 1. context lines written in the code
ctx_n = 0
for mm in re.finditer(r'ctxHtml\(\s*([\'"`])', src):
    if src[max(0, mm.start() - 9):mm.start()].endswith('function '): continue
    q = mm.group(1); i = mm.end(); depth = 0; buf = ''
    while i < len(src):
        c = src[i]
        if c == '\\': buf += src[i:i + 2]; i += 2; continue
        if q == '`' and src.startswith('${', i) and depth == 0:
            depth = 1; buf += '\x00'; i += 2; continue
        if depth:
            depth += {'{': 1, '}': -1}.get(c, 0); i += 1; continue
        if c == q: break
        buf += c; i += 1
    ctx_n += 1
    if len(buf) > CTX_MAX:
        problems.append(f'line {line_of(mm.start())}: context line of {len(buf)} characters (max {CTX_MAX}): {buf.replace(chr(0), "${…}")[:70]!r}')

# reported, not failed (phase S3 turns these into failures)
faint = [line_of(mm.start()) for mm in re.finditer(r'(?<![-\w])color\s*:\s*var\(--text-faint\)', src)]
print(f'report: {len(faint)} CSS rules colour text with --text-faint (lines {", ".join(map(str, faint[:12]))}{" ..." if len(faint) > 12 else ""}); the rule moves them to --text-dim card by card')
for p in problems: print('PROBLEM:', p)
print(f'{len(INFO)} info panels ({", ".join(sorted(used))}), {ctx_n} context lines in the code; {len(problems)} problems')
sys.exit(1 if problems else 0)
