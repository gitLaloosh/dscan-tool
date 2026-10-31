"""Card and page-part names come from one list (v2026.10.14.45, roadmap/card-names.md).

    python3 -I tools/check_card_names.py [index.html]        # must end with "0 problems"
    python3 -I tools/check_card_names.py [index.html] --list # also print every string that names a part

The owner (2026-10-23): "i see a recurring issue with not having definitive names for each card. it results in subtext
and explanatory info referencing card titles that should be interchangeable." So CARD_NAMES in index.html is the one
place a card or page part is named; titles, collapsed rows, notes and tooltips call cardName('key'), and ERROR_CODES
writes {card:key}, which gen_errors_md.py resolves. Renaming a card is then one edit.

What this reads: every string the page can show -- JavaScript string and template-literal text (comments skipped,
${...} expressions skipped), the HTML outside <script>/<style> (text and attribute values, HTML comments skipped),
and every ERROR_CODES field. Comments are for programmers and keep old names freely.

It fails when:
  1. a name from CARD_NAMES is typed by hand: a name of two or more words (or "Matchup") wherever it appears, also
     with other capitals ("Navigation & targeting") as long as it starts with a capital -- lower-case "their last
     kill" or "damage application" is ordinary prose; a one-word name only as "<Name> card" or in quotes, because
     "Fit", "Capacitor" or "Firepower" are also ordinary words;
  2. text calls something "<Capitalized words> card" -- a card named by hand, listed or not;
  3. an old name from RETIRED below is still shown;
  4. cardName / cardLabelHtml / collapsedCardHtml or an ERROR_CODES {card:key} uses a key not in CARD_NAMES, or
     cardLabelHtml / collapsedCardHtml is handed a title (the old signature);
  5. CARD_NAMES and roadmap/card-names.md disagree.
"""
import sys, os, re, json

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
src = open(html, encoding='utf-8').read()

m = re.search(r'const CARD_NAMES = (\{.*?\n\});', src, re.S)
if not m: sys.exit('CARD_NAMES not found in ' + html)
NAMES = json.loads(m.group(1))
names_span = (m.start(), m.end())
e = re.search(r'const ERROR_CODES = (\{.*?\n\});', src, re.S)
ERR = json.loads(e.group(1)) if e else {}
err_span = (e.start(), e.end()) if e else (0, 0)

# Old names (the owner's renames, 2026-10-23). Matched case-insensitively.
RETIRED = {
    'their damage on you': "the Damage Application card (cardName('dmg'))",
    'your damage on them': "'damage applied to them' (a later chart's wording)",
    'their dps on you': "'DPS applied to you'",
    'last-kill box': "cardName('lastkill')",
    'threat view': "cardName('perspective.threat')",
    'my ship view': "cardName('perspective.mine')",
    'my ship switch': "cardName('board') (the Matchup)",
    'dps on you': "'DPS applied to you'",
    'dps on them': "'DPS applied to them'",
}
# Retired names matched as written (capitals and all): their lower-case words stay ordinary prose.
RETIRED_EXACT = {
    'Your Side': "cardName('side') (Standings, v2026.10.14.95)",
    'Against This Fleet': "removed in v2026.10.31.1: no time-to-kill for a whole fleet (LESSON #108); its ranges are in cardName('fksum') and cardName('fkpilots')",
}

def line_of(pos): return src.count('\n', 0, pos) + 1

# ---- JavaScript: string / template text, with positions -------------------------------------------------------
REGEX_PREV = set('(,=:[!&|?{};+-*%<>~^') | {''}
def js_strings(a, b):
    """Yield (pos, text) for each string literal / template chunk in src[a:b], skipping comments and regexes."""
    i, prev = a, ''
    stack = []   # template nesting: each entry = brace depth inside ${ }
    while i < b:
        c = src[i]
        if stack and c == '}' and stack[-1] == 0:
            stack.pop(); i += 1
            yield from template(i, b, stack); i = template.end; prev = '`'; continue
        if stack and c == '{': stack[-1] += 1
        if stack and c == '}': stack[-1] -= 1
        if c == '/' and src.startswith('//', i):
            j = src.find('\n', i); i = b if j < 0 else j; continue
        if c == '/' and src.startswith('/*', i):
            j = src.find('*/', i + 2); i = b if j < 0 else j + 2; continue
        if c == '/' and (prev in REGEX_PREV or re.search(r'(?:return|typeof|case|in|of)\s*$', src[max(a, i - 8):i])):
            j, cls = i + 1, False
            while j < b and src[j] != '\n':
                if src[j] == '\\': j += 2; continue
                if src[j] == '[': cls = True
                elif src[j] == ']': cls = False
                elif src[j] == '/' and not cls: break
                j += 1
            i = j + 1; prev = 'r'; continue
        if c in '\'"':
            j, buf = i + 1, []
            while j < b and src[j] != c:
                if src[j] == '\\': buf.append(src[j:j + 2]); j += 2; continue
                buf.append(src[j]); j += 1
            if '${cardName(' in ''.join(buf): quoted_template.append(i)   # '...${cardName(..)}...' never runs
            yield i, ''.join(buf); i = j + 1; prev = 's'; continue
        if c == '`':
            yield from template(i + 1, b, stack); i = template.end; prev = '`'; continue
        if not c.isspace(): prev = c if not (c.isalnum() or c in '_$') else 'w'
        i += 1

def template(i, b, stack):
    buf, start = [], i
    while i < b:
        if src[i] == '\\': buf.append(src[i:i + 2]); i += 2; continue
        if src[i] == '`':
            template.end = i + 1
            if buf: yield start, ''.join(buf)
            return
        if src.startswith('${', i):
            if buf: yield start, ''.join(buf)
            stack.append(0); template.end = i + 2
            return
        buf.append(src[i]); i += 1
    template.end = b

quoted_template = []
frags = []
for sm in re.finditer(r'<script[^>]*>(.*?)</script>', src, re.S):
    a, b = sm.start(1), sm.end(1)
    for pos, text in js_strings(a, b):
        if names_span[0] <= pos < names_span[1] or err_span[0] <= pos < err_span[1]: continue
        frags.append((line_of(pos), text))
# ---- HTML outside script/style ----
body = src
for pat in (r'<script[^>]*>.*?</script>', r'<style[^>]*>.*?</style>', r'<!--.*?-->'):
    body = re.sub(pat, lambda mm: '\n' * mm.group(0).count('\n'), body, flags=re.S)
for ln, line in enumerate(body.split('\n'), 1):
    for t in re.findall(r'>([^<]+)<', line) + re.findall(r'(?:title|aria-label|placeholder|alt)="([^"]*)"', line):
        if t.strip(): frags.append((ln, t))
# ---- ERROR_CODES fields ----
for code, r in ERR.items():
    for k, v in r.items():
        if isinstance(v, str) and k not in ('since', 'doc', 'status'): frags.append((f'ERROR_CODES {code}.{k}', v))

problems = []
flat = {k: v for k, v in NAMES.items()}
multi = {k: v for k, v in flat.items() if ' ' in v or '/' in v or not v.isalpha() or v == 'Matchup'}
single = {k: v for k, v in flat.items() if k not in multi}
named = []
for where, t in frags:
    if len(t) > 400 and not re.search(r'\s', t): continue   # v.96: data, not words (INTEL_JUMPS' base64: the card-word pattern backtracks for minutes on it)
    t1 = re.sub(r'\{card:[\w.]+\}', '', t)
    hit = False
    for k, v in multi.items():
        for mm in re.finditer(r'(?<![\w])' + re.escape(v) + r'(?![\w])', t1, re.I):
            got = mm.group(0)
            if got == v: problems.append(f"{where}: '{v}' typed by hand; use cardName('{k}')"); hit = True
            elif got[0].isupper(): problems.append(f"{where}: '{got}' is '{v}' spelled differently; use cardName('{k}')"); hit = True
            # a lower-case start ("their last kill", "damage application") is ordinary prose, not the name
    for k, v in single.items():
        if re.search(r'(?<![\w])' + re.escape(v) + r'(?: card\b|["”])', t1) or re.search(r'["“]' + re.escape(v) + r'["”]', t1):
            problems.append(f"{where}: '{v}' typed by hand; use cardName('{k}')"); hit = True
    for mm in re.finditer(r'\b((?:[A-Z][\w&/]*\s?)+?) card\b', t1):
        nm = mm.group(1).strip()
        if nm not in flat.values():
            problems.append(f"{where}: '{nm} card' names a card that isn't in CARD_NAMES"); hit = True
    tl = t1.lower()
    for old, new in RETIRED.items():
        if old in tl: problems.append(f"{where}: old name '{old}' -- now {new}"); hit = True
    for old, new in RETIRED_EXACT.items():   # v.95: names whose lower-case words are ordinary prose ("your side's losses")
        if old in t1: problems.append(f"{where}: old name '{old}' -- now {new}"); hit = True
    if '{card:' in t or 'cardName' in t: named.append((where, t))
    if hit: named.append((where, t))
for pos in quoted_template: problems.append(f"line {line_of(pos)}: ${{cardName(...)}} inside a '...' or \"...\" string (needs backticks)")
# ---- keys ----
for kind, pat in (('cardName', r"cardName\(\s*'([^']+)'"), ('cardLabelHtml', r"cardLabelHtml\(\s*'([^']+)'"),
                  ('collapsedCardHtml', r"collapsedCardHtml\(\s*'([^']+)'")):
    for mm in re.finditer(pat, src):
        if mm.group(1) not in flat: problems.append(f"line {line_of(mm.start())}: {kind}('{mm.group(1)}') -- no such key in CARD_NAMES")
for code, r in ERR.items():
    for k, v in r.items():
        for key in re.findall(r'\{card:([\w.]+)\}', v if isinstance(v, str) else ''):
            if key not in flat: problems.append(f'ERROR_CODES {code}.{k}: {{card:{key}}} -- no such key')
# The helpers take no title (v2026.10.14.45); a string second argument that is a name means the old signature.
for mm in re.finditer(r"(cardLabelHtml|collapsedCardHtml)\(\s*'([^']+)'\s*,\s*'([^']*)'", src):
    if mm.group(3) in flat.values() or mm.group(3).lower() in (v.lower() for v in flat.values()):
        problems.append(f"line {line_of(mm.start())}: {mm.group(1)}('{mm.group(2)}', '{mm.group(3)}') passes a title; the title comes from CARD_NAMES")
# ---- roadmap/card-names.md agrees ----
doc = os.path.join(ROOT, 'roadmap', 'card-names.md')
if os.path.exists(doc):
    rows = dict(re.findall(r'^\| `([\w.]+)` \| ([^|]+?) \|', open(doc, encoding='utf-8').read(), re.M))
    if rows != flat:
        for k in sorted(set(rows) | set(flat)):
            if rows.get(k) != flat.get(k): problems.append(f"roadmap/card-names.md says {k} = {rows.get(k)!r}, CARD_NAMES says {flat.get(k)!r}")
else:
    problems.append('roadmap/card-names.md is missing')

if '--list' in sys.argv:
    for where, t in named: print(f'  {where}: {t[:140]}')
for p in problems: print('PROBLEM:', p)
print(f'{len(flat)} names, {len(frags)} strings read; {len(problems)} problems')
sys.exit(1 if problems else 0)
