"""Subtext rule (v2026.10.14.48, roadmap/subtext-plan.md). In the update-check chain.

    python3 -I tools/check_subtext.py [index.html]          # must end with "0 problems"

The owner (2026-10-24): "the subtext in the tool is a little overwhelming and distracts from important values ... address
it as a site wide design choice"; decided: "works as written. info icon opens a panel over the page. the 40 character
limit is fine." The rule, enforced here as far as a static read can:
  1. one line of context under a value: every ctxHtml(...) whose text is written in the code is <= CTX_MAX (40)
     characters (a template's ${...} parts count as one character each; live values are cut with an ellipsis);
  2. how a card works lives behind its info button: CARD_INFO keys are card keys (CARD_NAMES), or "<key>#<variant>"
     for a variant of a card's text (v2026.10.14.49), every infoBtnHtml(key) has a CARD_INFO entry, every CARD_INFO
     entry is used, and every {card:key} in the text is a CARD_NAMES key;
  4. (nothing moves) is checked in the page: tools/page_checks/no_shift_check.py.
  6. (since v2026.10.14.50) no text coloured --text-faint (below 4.5:1 contrast on the cards), except a disabled
     control marked "faint: disabled" on its line.
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
    # v2026.10.14.49: "<card key>#<variant>" is a variant of a card's text (the Anhinga's Mode: "tdmode#primary")
    if k.split('#')[0] not in NAMES: problems.append(f'CARD_INFO["{k}"]: not a card key in CARD_NAMES (a variant is "<card key>#<variant>")')
    if not isinstance(paras, list) or not paras or not all(isinstance(p, str) and p.strip() for p in paras):
        problems.append(f'CARD_INFO["{k}"]: must be a list of non-empty paragraphs')
        continue
    # other cards are named as {card:key} (infoBtnHtml fills the name in), so a rename stays one edit
    for p in paras:
        for ck in re.findall(r'\{card:([^}]*)\}', p):
            if ck not in NAMES: problems.append(f'CARD_INFO["{k}"]: {{card:{ck}}} is not a key in CARD_NAMES')
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

# 6. context text uses --text-dim (v2026.10.14.50, phase S3: a failure now). --text-faint (#4d5960) is under 4.5:1 on
# the cards, so text may use it only on a disabled control (exempt from the contrast rule), marked on its line with
# "faint: disabled". Borders (border-color) don't count.
faint_ok = 0
for mm in re.finditer(r'(?<![-\w])color\s*:\s*var\(--text-faint\)', src):
    ln = src[src.rfind('\n', 0, mm.start()) + 1:src.find('\n', mm.end())]
    if 'faint: disabled' in ln: faint_ok += 1; continue
    problems.append(f'line {line_of(mm.start())}: text coloured --text-faint (too faint to read; use --text-dim, or mark a disabled control "faint: disabled"): {ln.strip()[:80]!r}')
print(f'{faint_ok} disabled controls keep --text-faint')
for p in problems: print('PROBLEM:', p)
print(f'{len(INFO)} info panels ({", ".join(sorted(used))}), {ctx_n} context lines in the code; {len(problems)} problems')
sys.exit(1 if problems else 0)
