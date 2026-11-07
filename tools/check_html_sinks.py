"""No new unescaped text in the page's markup (v2026.11.07.3, build queue 023; Project doc roadmap/sso-hardening-plan.md step 4;
LESSON #144, #145).

    python3 -I tools/check_html_sinks.py [index.html]                 -> 'HTML SINKS: ... 0 problems'
    python3 -I tools/check_html_sinks.py --shrink [index.html]        -> drops baseline entries no longer in the page
    python3 -I tools/check_html_sinks.py --self-test                  -> made-up templates, each rule caught

A template literal that builds HTML (its text has a tag `<x` or an attribute `name="`) puts each ${...} into the page's markup. Such an
expression passes on its own when it is:
  * escapeHtml(...) (the whole expression);
  * a number: Math.*, Number(...), .toFixed(, toLocaleString(, .length, | 0, a numeric literal;
  * an ALL_CAPS constant;
  * a call to a function on BUILDERS below, or one whose name ends in `Html` (the page's convention: such a function returns HTML it
    built under these same rules; a new one is checked here like any other code).
Markup glued together with + (a plain string with a tag in it): what's added on either side must pass the same rules, be a string,
or be a template (whose own ${...} are checked where it is written). And a builder (a ...Html function or BUILDERS) must not return
one of its own arguments unchanged, in any branch: its callers pass this lint by its name, so it must build what it returns. (The
owner, 2026-11-07, "yes" to closing that gap in the name rule.)
Everything else that was in the page when this lint was written is in tools/html_sinks_baseline.json, keyed by the enclosing
function's name and the expression's text (not line numbers, so it survives edits). **The baseline only shrinks:**
  * a new ${...} that passes none of the above fails: escape it, or give it a builder;
  * an entry may be added to the baseline only with the owner's OK, written into the pull request (--add-baseline does it);
  * an entry the page no longer has fails until --shrink removes it, so the file stays exact.
It also fails on, anywhere in the page (markup, templates, strings): an inline event-handler attribute (on...="..."), which the CSP
refuses anyway; a single-quoted attribute whose value is built from ${...} (attributes are double-quoted, LESSON #144); and
innerHTML = / insertAdjacentHTML whose value is a bare variable (through the baseline, like the rest).
The JavaScript is read by a small tokenizer that knows strings, comments, template literals (nested too) and regex literals.
"""
import sys, os, re, json, collections

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html_sinks_baseline.json')
BUILDERS = {   # functions that return HTML they built, whose names don't end in Html; each with why it's safe to place
    'standIcon': 'the standing icon: a fixed SVG per standing kind (CLAUDE.md "Standing icon")',
    'standMark': 'the standing mark: a fixed SVG per standing kind',
    'zkLinkHtml': 'the zKillboard link (ends in Html; listed for the record)',
}
NUM_RX = re.compile(r'^(Math\.\w+\(|Number\(|\d[\d_.]*$|[\w.$\[\]()]+\.length$)|\.toFixed\(\d*\)$|toLocaleString\([^)]*\)$|\|\s*0\)?$')
KEYWORD_BEFORE_REGEX = {'return', 'typeof', 'case', 'do', 'else', 'in', 'of', 'new', 'delete', 'void', 'throw', 'instanceof', 'yield', 'await'}


def tokenize_templates(src, start=0):
    """Yields (literal text with \\x00 where each ${} was, [expressions], position) for every template literal in the code, nested ones
    too. Knows '...' and "..." strings, // and /* */ comments, regex literals (by what comes before the /), and ${ } nesting."""
    out = []

    def code(i, stop_brace):
        """Scans code from i; returns the index after the closing } when stop_brace (inside ${}), else the end."""
        n = len(src); depth = 0; prev = ''   # prev: the last significant token's kind, to tell a regex from a division
        while i < n:
            c = src[i]
            if c in ' \t\r\n': i += 1; continue
            if src.startswith('//', i): j = src.find('\n', i); i = n if j < 0 else j; continue
            if src.startswith('/*', i): j = src.find('*/', i + 2); i = n if j < 0 else j + 2; continue
            if c in '"\'':
                j = i + 1
                while j < n and src[j] != c:
                    j += 2 if src[j] == '\\' else 1
                i = j + 1; prev = 'v'; continue
            if c == '`': i = template(i); prev = 'v'; continue
            if c == '/':
                if prev in ('', 'op') :   # a regex literal
                    j = i + 1; cls = False
                    while j < n:
                        ch = src[j]
                        if ch == '\\': j += 2; continue
                        if ch == '[': cls = True
                        elif ch == ']': cls = False
                        elif ch == '/' and not cls: break
                        elif ch == '\n': break
                        j += 1
                    j += 1
                    while j < n and (src[j].isalpha()): j += 1
                    i = j; prev = 'v'; continue
                i += 1; prev = 'op'; continue
            if c == '{': depth += 1; i += 1; prev = 'op'; continue
            if c == '}':
                if stop_brace and depth == 0: return i + 1
                depth -= 1; i += 1; prev = 'op'; continue
            if c.isalnum() or c in '_$':
                j = i
                while j < n and (src[j].isalnum() or src[j] in '_$'): j += 1
                w = src[i:j]; prev = 'op' if w in KEYWORD_BEFORE_REGEX else 'v'; i = j; continue
            if c in ')]': prev = 'v'; i += 1; continue
            prev = 'op'; i += 1
        return i

    def template(i):
        """i at the opening backtick; records the template; returns the index after its closing backtick."""
        n = len(src); j = i + 1; lit = []; parts = []
        while j < n and src[j] != '`':
            if src[j] == '\\': lit.append(src[j:j + 2]); j += 2; continue
            if src.startswith('${', j):
                k = code(j + 2, True)
                parts.append(src[j + 2:k - 1]); lit.append('\x00'); j = k; continue
            lit.append(src[j]); j += 1
        out.append((''.join(lit), parts, i))
        return j + 1

    code(start, False)
    return out


def enclosing(src, pos, fn_starts):
    """The name of the function the position is in (the nearest function declaration or named arrow before it)."""
    lo, hi = 0, len(fn_starts)
    while lo < hi:
        mid = (lo + hi) // 2
        if fn_starts[mid][0] <= pos: lo = mid + 1
        else: hi = mid
    return fn_starts[lo - 1][1] if lo else '(top)'


def norm(e): return re.sub(r'\s+', ' ', e.strip())


def passes(e):
    e = e.strip()
    if re.match(r'^escapeHtml\(', e) and balanced_call(e): return True
    if NUM_RX.search(e): return True
    if re.fullmatch(r'[A-Z_][A-Z0-9_]*', e): return True
    m = re.match(r'^([A-Za-z_$][\w$]*)\(', e)
    if m and balanced_call(e) and (m.group(1) in BUILDERS or m.group(1).endswith('Html')): return True
    return False


def balanced_call(e):
    """True when e is one call: name(...) with the closing paren at the very end."""
    i = e.find('('); d = 0
    for k in range(i, len(e)):
        if e[k] == '(': d += 1
        elif e[k] == ')':
            d -= 1
            if d == 0: return k == len(e) - 1
    return False


def scan(html):
    m = re.search(r'<script\b[^>]*>(.*?)</script', html, re.S | re.I)
    src = m.group(1) if m else ''
    off = m.start(1) if m else 0
    fn_starts = sorted([(x.start(), x.group(1)) for x in re.finditer(r'\bfunction\s+([A-Za-z_$][\w$]*)\s*\(', src)]
                       + [(x.start(), x.group(1)) for x in re.finditer(r'\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>', src)])
    found = collections.Counter(); hard = []
    for lit, parts, pos in tokenize_templates(src):
        if not re.search(r'<[a-zA-Z]|[a-zA-Z-]+="', lit): continue
        fn = enclosing(src, pos, fn_starts)
        for e in parts:
            if not passes(e): found[(fn, norm(e))] += 1
        # a single-quoted attribute whose value is built from ${...}
        for a in re.finditer(r"[\s][a-zA-Z-]+='[^'<>]*\x00", lit):
            hard.append(f'{fn}: a single-quoted attribute built from ${{...}}: {a.group(0).strip()[:40]!r} (double-quote it, LESSON #144)')
        for a in re.finditer(r'[\s"\'](on[a-z]+)\s*=\s*["\\]', lit):
            hard.append(f'{fn}: an inline {a.group(1)}= handler in a template (the CSP refuses it; use data-imgfail or addEventListener)')
    # inline handlers anywhere in the markup outside the script, and in plain strings
    outside = html[:off] + html[off + len(src):]
    for a in re.finditer(r'<[a-zA-Z][^>]*\s(on[a-z]+)\s*=', outside):
        hard.append(f'markup: an inline {a.group(1)}= handler ({a.group(0)[:50]!r})')
    for a in re.finditer(r'(["\'])(?:(?!\1)[^\\\n]|\\.)*<[a-zA-Z][^\n]*?\s(on[a-z]+)=', src):
        hard.append(f'a string with an inline {a.group(2)}= handler: {a.group(0)[:60]!r}')
    # innerHTML = <bare variable> / insertAdjacentHTML(..., <bare variable>)
    for a in re.finditer(r'\.innerHTML\s*=\s*([A-Za-z_$][\w$.]*)\s*[;,)\n]', src):
        v = a.group(1)
        if v not in ('null', 'undefined') and not re.fullmatch(r'[A-Z_][A-Z0-9_]*', v):
            found[(enclosing(src, a.start(), fn_starts), 'innerHTML = ' + v)] += 1
    for a in re.finditer(r'\.insertAdjacentHTML\(\s*[^,]+,\s*([A-Za-z_$][\w$.]*)\s*\)', src):
        found[(enclosing(src, a.start(), fn_starts), 'insertAdjacentHTML ' + a.group(1))] += 1
    # (the owner, 2026-11-07, to closing the name rule's gap: "yes") markup glued with + : a plain string with a tag in it, and
    # what's added to it must pass the same rules as a ${...} (escapeHtml, a number, a constant, a builder) or be in the baseline
    code = blank_strings_and_comments(src)
    for a in re.finditer(r"""(['"])(?:(?!\1)[^\\\n]|\\.)*<[a-zA-Z/](?:(?!\1)[^\\\n]|\\.)*\1""", code):
        for side, e in (('after', operand_after(code, a.end())), ('before', operand_before(code, a.start()))):
            if e is None or passes_value(e): continue
            found[(enclosing(src, a.start(), fn_starts), f'+ {norm(e)}')] += 1
    # a builder (a ...Html function, or BUILDERS) must not hand back one of its own arguments unchanged: whatever the caller passed
    # would go into the page as markup, and the call would pass this lint by its name
    for m in re.finditer(r'\bfunction\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{', src):
        name = m.group(1)
        if not (name.endswith('Html') or name in BUILDERS): continue
        params = {p.strip().split('=')[0].strip(' .') for p in m.group(2).split(',') if p.strip()}
        body = brace_body(src, m.end() - 1)
        for r in re.finditer(r'\breturn\s+([^;\n]+)', body):
            for x in results(r.group(1).strip().rstrip(';')):
                if x in params: hard.append(f'{name}(): returns its argument {x!r} unchanged: a builder must build its markup (escapeHtml what it was given)')
    return found, hard


def split_top(e, seps):
    """Splits e at the first top-level separator from seps (not inside brackets, strings or templates): (left, sep, right) or None."""
    d = 0; q = None; i = 0
    while i < len(e):
        c = e[i]
        if q:
            if c == '\\': i += 2; continue
            if c == q: q = None
        elif c in '\'"`': q = c
        elif c in '([{': d += 1
        elif c in ')]}': d -= 1
        elif d == 0:
            for sp in seps:
                if e.startswith(sp, i): return e[:i], sp, e[i + len(sp):]
        i += 1
    return None


def strip_parens(e):
    e = e.strip()
    while e.startswith('(') and e.endswith(')') and split_top(e[1:-1], [')']) is None and e.count('(') == e.count(')'):
        inner = e[1:-1]; d = 0; ok = True
        for c in inner:
            d += c == '('; d -= c == ')'
            if d < 0: ok = False; break
        if not ok: break
        e = inner.strip()
    return e


def results(e):
    """The sub-expressions a value can come from: both results of a ternary, both sides of ||, the right of && (its left only
    gives a falsy value), recursively."""
    e = strip_parens(e)
    t = split_top(e, [' ? '])
    if t:
        r = split_top(t[2], [' : '])
        return results(r[0]) + results(r[2]) if r else [e]
    o = split_top(e, [' || '])
    if o: return results(o[0]) + results(o[2])
    a = split_top(e, [' && '])
    if a: return results(a[2])
    return [e]


def passes_value(e):
    """A value added to markup passes when every result it can come from passes, or is a string or template literal (a template's
    own ${...} are checked where it is written)."""
    return all(passes(x) or re.match(r"""^['"`]""", x) or x in ("''", '""') for x in results(e))


def blank_strings_and_comments(src):
    """The source with comments blanked to spaces (same length), strings and templates kept: used to skip a "string" that is
    really inside a comment."""
    return re.sub(r'/\*.*?\*/|(?<![:\\\'"`])//[^\n]*', lambda m: ' ' * len(m.group(0)), src, flags=re.S)


def operand_after(src, i):
    """The expression added after a string: ` + expr` up to the next + , ; ) ] } at depth 0; None when no + follows."""
    m = re.match(r'\s*\+\s*', src[i:])
    if not m: return None
    j = i + m.end(); d = 0; k = j
    while k < len(src):
        c = src[k]
        if c in '([{': d += 1
        elif c in ')]}':
            if d == 0: break
            d -= 1
        elif c in '\'"`' and k == j: return src[j:j + 1]   # another literal
        elif d == 0 and (c in ',;+\n' or src.startswith('?', k) or src.startswith(' : ', k)): break
        k += 1
    return src[j:k].strip() or None


def operand_before(src, i):
    """The expression added before a string: `expr + ` back to the previous + = ( , ; return at depth 0; None when no + precedes."""
    m = re.search(r'\+\s*$', src[max(0, i - 200):i])
    if not m: return None
    k = i - (len(src[max(0, i - 200):i]) - m.start()) - 1; d = 0; j = k
    while j >= 0:
        c = src[j]
        if c in ')]}': d += 1
        elif c in '([{':
            if d == 0: break
            d -= 1
        elif d == 0 and c in ',;+=\n?:': break
        j -= 1
    e = src[j + 1:k + 1].strip()
    e = re.sub(r'^(?:return\s+|>\s*)', '', e)   # after return, or after an arrow's =>
    return e or None


def brace_body(src, i):
    """The text of the {...} block starting at src[i] == '{'."""
    d = 0
    for j in range(i, len(src)):
        if src[j] == '{': d += 1
        elif src[j] == '}':
            d -= 1
            if not d: return src[i:j + 1]
    return src[i:]


def load_baseline():
    if not os.path.exists(BASELINE): return {}
    d = json.load(open(BASELINE, encoding='utf-8'))
    return {(k.split('␟')[0], k.split('␟')[1]): v for k, v in d['entries'].items()}


def save_baseline(entries):
    note = ('tools/check_html_sinks.py: ${...} in HTML templates that pass none of its rules, as the page had them on 2026-11-07 (v2026.11.07.3, '
            'build queue 023). Keyed by "function␟expression" with how many times. This file only shrinks: --shrink removes what the page '
            'no longer has; an entry is added only with the owner\'s OK in the pull request (--add-baseline).')
    d = {'note': note, 'entries': {f'{fn}␟{e}': n for (fn, e), n in sorted(entries.items())}}
    open(BASELINE, 'w', encoding='utf-8').write(json.dumps(d, indent=1, ensure_ascii=False) + '\n')


def check(html, base):
    found, hard = scan(html)
    probs = list(hard)
    for k, n in sorted(found.items()):
        if n > base.get(k, 0):
            probs.append(f'{k[0]}: ${{{k[1][:90]}}} is not escaped ({n - base.get(k, 0)} new): use escapeHtml(...), a number, a constant or a builder')
    gone = [k for k, n in base.items() if found.get(k, 0) < n]
    for k in gone[:20]:
        probs.append(f'baseline: {k[0]}: ${{{k[1][:70]}}} is no longer in the page as often: run python3 -I tools/check_html_sinks.py --shrink')
    if len(gone) > 20: probs.append(f'baseline: {len(gone) - 20} more entries to shrink')
    return found, probs


def self_test():
    T = lambda body: '<html><script>\n' + body + '\n</script></html>'
    base = {}
    cases = [
        ('function a(x){ return `<b title="${x}">${escapeHtml(x)}</b>`; }', 1, 'an unescaped ${x} in a title'),
        ('function a(x){ return `<b title="${escapeHtml(x)}">${x.length} ${Math.round(x)} ${N_MAX} ${rowHtml(x)}</b>`; }', 0, 'escaped, numbers, a constant, a builder'),
        ('function a(x){ return `<b onclick="go()">x</b>`; }', 1, 'an onclick= in a template'),
        ("function a(x){ return `<b title='${escapeHtml(x)}'>x</b>`; }", 1, 'a single-quoted attribute built from ${}'),
        ('function a(x){ const r = /["\'`]/g; return `<b>${escapeHtml(x)}</b>`; }', 0, 'a regex literal with quotes and a backtick'),
        ('function a(x){ return `<ul>${x.map(y => `<li>${y}</li>`).join("")}</ul>`; }', 2, 'a nested template: the inner ${y} and the outer map'),
        ('function a(el, h){ el.innerHTML = h; }', 1, 'innerHTML = a bare variable'),
        ('function a(x){ return "<img src=x onerror=boom()>"; }', 1, 'an onerror= in a plain string'),
        ('function a(x){ return `plain text ${x}`; }', 0, 'a template with no markup'),
        ("function a(n){ return '<b>' + n + '</b>'; }", 1, 'markup glued with + around an unescaped name (both sides: one problem, 2 new)'),
        ("function a(n){ return '<b>' + escapeHtml(n) + '</b>'; }", 0, 'markup glued with + around escaped text'),
        ("function a(n, k){ return '<i>' + (k ? `<b>${escapeHtml(n)}</b>` : '') + rowHtml(n); }", 0, 'a choice of templates and a builder after +'),
        ('function nameHtml(n){ return n; }', 1, 'a builder that hands back its argument'),
        ('function nameHtml(n, ok){ return ok ? `<b>${escapeHtml(n)}</b>` : n; }', 1, 'a builder that hands back its argument in one branch'),
        ('function nameHtml(r){ return r ? `<b>${escapeHtml(r.name)}</b>` : ""; }', 0, 'a builder whose argument is only the condition'),
    ]
    bad = []
    for body, want, what in cases:
        found, probs = check(T(body), base)
        if len(probs) != want: bad.append(f'{what}: {len(probs)} problems, wanted {want} {probs}')
    # the ratchet: an entry in the baseline passes; one more of it fails; a gone one fails until shrunk
    page = T('function a(x){ return `<b>${x}</b>`; }')
    f, _ = scan(page)
    if check(page, dict(f))[1]: bad.append('a baseline entry did not pass')
    if not check(T('function a(x){ return `<b>${x}</b><i>${x}</i>`; }'), dict(f))[1]: bad.append('a second copy of a baseline entry passed')
    if not check(T('function a(x){ return `<b>${escapeHtml(x)}</b>`; }'), dict(f))[1]: bad.append('a fixed entry left in the baseline passed')
    print('HTML SINKS SELF-TEST:', 'ok' if not bad else bad)
    return 1 if bad else 0


def main(argv):
    if '--self-test' in argv: return self_test()
    args = [a for a in argv if not a.startswith('--')]
    path = args[0] if args else os.path.join(ROOT, 'index.html')
    html = open(path, encoding='utf-8').read()
    base = load_baseline()
    if '--init-baseline' in argv:   # only when the lint is first written (023); afterwards the baseline only shrinks
        save_baseline(scan(html)[0]); print('HTML SINKS: baseline written'); return 0
    if '--shrink' in argv:
        found, _ = scan(html)
        new = {k: min(n, found.get(k, 0)) for k, n in base.items() if found.get(k, 0)}
        save_baseline(new); print(f'HTML SINKS: baseline {sum(base.values())} -> {sum(new.values())}')
        base = new
    if '--add-baseline' in argv:   # the owner's OK, in the pull request, for each entry this adds
        found, _ = scan(html)
        new = dict(base); added = []
        for k, n in found.items():
            if n > base.get(k, 0) and not passes(k[1]): new[k] = n; added.append(k)
        save_baseline(new); base = new
        for k in added: print('HTML SINKS added to the baseline (owner OK needed):', k[0], '|', k[1][:80])
    found, probs = check(html, base)
    for x in probs: print('HTML SINKS', x)
    print(f'HTML SINKS: {sum(found.values())} unescaped ${{...}} in HTML templates, all in the baseline ({sum(base.values())}); {len(probs)} problems')
    return 1 if probs else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
