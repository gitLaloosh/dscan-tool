"""The UI rules (v2026.10.29.7, CLAUDE.md "UI rules"). In the update-check chain.

    python3 -I tools/check_ui_rules.py [index.html]          # must end with "0 problems"

The owner approved the controls mockup on 2026-10-29 ("all of your recommendations seem good", then "looks good" on the
text-field mockup): one tag, one switch, one slider, one text field across the site. Checked in the page's <style> as
far as a static read can (the look itself: tools/page_checks/ui_rules_check.py):
  1. tags, not pills: a rule whose selector names a chip, pill or tag has corners of at most 4px (never round) and no
     dashed border (empty states are a faint fill with dim text);
  2. one switch: the switch classes (dmg-sw, mys-sw) are 36x20 with 3px corners, on = #1f6f80;
  3. one slider: the one global input[type=range] style (a 4px track filled to --p) and rangeFillSet in the script;
     no other rule restyles a slider's track or handle;
  4. one text field: a :focus rule on a text field, select or textarea sets the cyan border and the ring, never amber;
     a field rule's corners are 4px.
"""
import sys, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
src = open(html, encoding='utf-8').read()
problems = []
m = re.search(r'<style>(.*?)</style>', src, re.S)
if not m: sys.exit('no <style> block')
css_start, css = m.start(1), m.group(1)
def line_of(pos): return src.count('\n', 0, css_start + pos) + 1

rules = []   # (selector, body, line)
clean = re.sub(r'/\*.*?\*/', lambda x: ' ' * len(x.group(0)), css, flags=re.S)
for r in re.finditer(r'([^{}]+)\{([^{}]*)\}', clean):
    sel = ' '.join(r.group(1).split())
    if sel.startswith('@'): continue
    rules.append((sel, r.group(2), line_of(r.start(1) + len(r.group(1)) - len(r.group(1).lstrip()))))
def prop(body, name):
    v = None
    for mm in re.finditer(r'(?:^|;)\s*' + re.escape(name) + r'\s*:\s*([^;]+)', body): v = mm.group(1).strip()
    return v
def px(v):
    mm = re.match(r'^(\d+(?:\.\d+)?)px', v or '')
    return float(mm.group(1)) if mm else (999 if v and ('%' in v or v.startswith('999')) else None)

# 1. tags
TAG = re.compile(r'\.[\w-]*(chip|pill|tag)[\w-]*', re.I)
NOT_TAG = ('build-tag', 'mk-tag')   # the version label in the header; mockup-only
for sel, body, ln in rules:
    names = [t.group(0) for t in TAG.finditer(sel)]
    if not names or all(any(n.endswith(x) for x in NOT_TAG) for n in names): continue
    r = px(prop(body, 'border-radius'))
    if r is not None and r > 4: problems.append(f'line {ln}: {sel}: border-radius {prop(body, "border-radius")} (tags have 3-4px corners, never round)')
    if re.search(r'\bdashed\b', body): problems.append(f'line {ln}: {sel}: a dashed border (empty states are a faint fill with dim text)')

# 2. switches
seen_sw = set()
for sel, body, ln in rules:
    for part in sel.split(','):
        p = part.strip()
        if p in ('.dmg-sw', 'input.mys-sw'):
            seen_sw.add(p)
            got = (prop(body, 'width'), prop(body, 'height'), prop(body, 'border-radius'))
            if got != ('36px', '20px', '3px'): problems.append(f'line {ln}: {p}: {got} (one switch: 36px x 20px, 3px corners)')
        if p in ('.dmg-sw:checked', 'input.mys-sw:checked'):
            if (prop(body, 'background') or '').lower() != '#1f6f80': problems.append(f'line {ln}: {p}: on is #1f6f80')
for p in ('.dmg-sw', 'input.mys-sw'):
    if p not in seen_sw: problems.append(f'{p}: no base rule found')

# 3. sliders
glob = [b for s, b, _ in rules if s == 'input[type=range]::-webkit-slider-runnable-track']
if len(glob) != 1 or 'var(--p)' not in glob[0]: problems.append('the global slider track (input[type=range]::-webkit-slider-runnable-track, filled to var(--p)) is missing')
for sel, body, ln in rules:
    if re.search(r'(slider-runnable-track|slider-thumb|range-track|range-thumb|range-progress)', sel) and not sel.startswith('input[type=range]'):
        problems.append(f'line {ln}: {sel}: a slider restyled locally (one slider: the global input[type=range] rules)')
if not re.search(r'^function rangeFillSet\(', src, re.M): problems.append('rangeFillSet (fills a slider to its handle) is missing from the script')

# 4. text fields
FIELD = re.compile(r'(input\[type=(text|search)\]|(?<![\w-])select|textarea|\.it-fbar input|\.it-box select)')
for sel, body, ln in rules:
    for part in (x.strip() for x in sel.split(',')):
        if not FIELD.search(part) or 'range' in part: continue
        if part.endswith(':focus') or part.endswith(':focus-visible'):
            bc = prop(body, 'border-color') or ''
            if 'amber' in bc: problems.append(f'line {ln}: {part}: an amber focus border (one text field: cyan border and ring)')
            elif bc and bc != 'var(--cyan)': problems.append(f'line {ln}: {part}: focus border {bc} (one text field: var(--cyan))')
        r = prop(body, 'border-radius')
        if r and r not in ('4px',) and not re.search(r'\b(option|optgroup)\b', part): problems.append(f'line {ln}: {part}: border-radius {r} (text fields have 4px corners)')
need = ['input[type=search]:focus', '.it-fbar select:focus', '.it-box select:focus', 'textarea:focus']
for n in need:
    if not any(n in [x.strip() for x in s.split(',')] and 'var(--accent-ring)' in b for s, b, _ in rules):
        problems.append(f'{n}: no focus rule with the cyan ring')

for p in problems: print('PROBLEM', p)
print(f'UI RULES: {len(problems)} problems')
sys.exit(1 if problems else 0)
