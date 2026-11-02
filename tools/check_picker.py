"""Pick the checks a change needs from what changed (page unchanged, v2026.10.31.7; the owner's "yes please" to the review's
"choose the level from the changed files, not by hand"). Used by run_checks.py --auto; on its own:

    python3 -I tools/check_picker.py [--since OLD_COPY_OF_THE_REPO]   -> the tier, the areas, and why

What changed: `git diff HEAD` plus new files when the repo has a .git folder, or every file that differs from --since (a copy of
the repo as last delivered). index.html is one big file, so its changed LINES are mapped, not the file:
  * inside a PYFA CORE section, or in the engine's code and tables -> the calculation chain (tier calc) and the calc page checks;
  * in a function or table of one area (its name's prefix: it* Intel, sa* System Analyzer, pd* the dossier, ...) -> that area;
  * otherwise the area of the section it sits in (REGIONS, in file order); shared code (escapeHtml, the cards, the analyzers'
    common drawing) -> everything;
  * CSS: by its class names (.it-* Intel, ...); a class no area owns -> every page check, but not the chain (CSS can't change a
    number); comments and blank lines -> nothing.
Other files: the calculation's inputs (regression_suite/, the pyfa core manifest, the table generators, tools/independent_checks/,
the pyfa tools) -> tier calc; a page check -> its areas and the checks that build on it; docs and the lints -> the fast lints only;
anything not listed -> everything. Every 5th delivery (four ledger rows since the last full run) -> everything.
"""
import os, re, sys, subprocess, difflib, fnmatch

ALL, PAGES, CHAIN = 'all', 'pages', 'chain'   # everything; every page check (no chain); the calculation chain (tier calc)

# A top-level name's prefix -> areas. Only prefixes that mean one thing everywhere in the file (case matters: DMG_* are engine
# constants, dmg* the damage chart).
PREFIX = {
    'it': ['intel'], 'IT': ['intel'], 'INTEL': ['intel'],
    'sa': ['system'], 'SA': ['system'], 'side': ['system'], 'SIDE': ['system'], 'stand': ['system'], 'STAND': ['system'],
    'std': ['system'], 'org': ['system', 'pilot', 'intel'],
    'scan': ['system'], 'SCAN': ['system'], 'CYNO': ['system'],   # v2026.11.02.2: the Ships on Scan rail
    'pd': ['pilot'], 'PD': ['pilot'], 'lk': ['pilot'], 'LK': ['pilot'], 'pa': ['pilot'], 'PA': ['pilot'],
    'zkb': ['pilot', 'intel'], 'ZKB': ['pilot', 'intel'],
    'fk': ['pilot', 'system', 'intel'], 'FK': ['pilot', 'system', 'intel'], 'fleet': ['pilot', 'system', 'intel'], 'FLEET': ['pilot', 'system', 'intel'],
    'my': ['myship'], 'MY': ['myship'], 'mys': ['myship'], 'MYS': ['myship'],
    'dmg': ['myship', 'calc'], 'ttk': ['myship', 'calc'], 'TTK': ['myship', 'calc'], 'wp': [CHAIN, 'myship', 'calc'], 'WP': [CHAIN, 'myship', 'calc'],
    'chg': ['fit'], 'CHG': ['fit'],
    'pyfa': [CHAIN, 'calc'], 'PYFA': [CHAIN, 'calc'], 'MAX': [CHAIN, 'calc'],
}
# Regions of index.html's script, in file order: a line takes the areas of the last region start above it. A start is a section
# banner or a top-level name (a name keeps working when lines move).
REGIONS = [
    (r'^const ESI\b', [ALL]),                                   # shared: card names and info, the zKillboard gate, error codes
    (r'^const DMG\b', [CHAIN, 'calc']),                         # the engine's constants and effect tables
    (r'^// ==== BUSY INDICATOR', [ALL]),                         # the analyzers' shared code: parsing, lookups, the cards
    (r'^// ==== PILOT DOSSIER', ['pilot']),
    (r'^async function speculateShip\b', [ALL]),                      # loss tallies, EFT parsing, the Fit Analyzer's run
    (r'^const SHIP_SENSOR_ATTR_EFFECTS\b', [CHAIN, 'calc']),    # the engine: module states, estimateHpAndDps
    (r'^function capWeakGaugeHtml\b', [ALL]),                   # cards shared by the Pilot and Fit Analyzers
    (r'^// ==== FIT LAYOUT TABLE', ['fit', 'pilot', 'layout']),  # the Fit card: ring, racks, bays, module states
    (r'^// ==== THEIR DAMAGE ON YOU', ['myship', 'calc']),
    (r'^// ==== MATCHUP STRIP', ['myship', 'calc']),
    (r'^// ==== WEAKNESS PICKS', [CHAIN, 'myship', 'calc']),
    (r'^// ==== ASSUMED CHARGES', [CHAIN, 'fit', 'calc']),
    (r'^// ==== MY SHIP', ['myship']),
    (r'^// ==== FIGHT STRIP', ['myship', 'calc']),
    (r'^// ==== SYSTEM ANALYZER', ['system']),
    (r'^// ---- PILOT AFFILIATION', ['pilot', 'system']),
    (r'^// ==== FLEET FROM A KILL', ['pilot', 'system', 'intel']),
    (r'^// ---- INTEL TABLES', ['intel']),
    (r'^// ==== INTEL ', ['intel']),
]
# CSS / markup class and id prefixes -> areas (the first part of the name, before - or _ or a capital)
CSS = {
    'it': ['intel'], 'nb': ['intel'], 'nbx': ['intel'], 'fe': ['intel'], 'fj': ['intel'], 'fsys': ['intel'], 'ftg': ['intel'],
    'intel': ['intel'], 'intelPanel': ['intel'], 'intelSw': ['intel'], 'tabIntel': ['intel'],
    'sa': ['system'], 'side': ['system'], 'std': ['system'], 'vs': ['system', 'myship'], 'ds': ['system'], 'contacts': ['system'],
    'candidate': ['system'], 'candidates': ['system'], 'saResults': ['system'], 'tabDscan': ['system'],
    'sr': ['system'], 'scanRail': ['system'], 'scanCard': ['system'],
    'pd': ['pilot'], 'pdk': ['pilot'], 'fsz': ['pilot', 'intel'], 'lk': ['pilot'], 'lastkill': ['pilot'], 'pa': ['pilot'],
    'zk': ['pilot', 'intel'], 'zkb': ['pilot'], 'attacker': ['pilot'], 'finalblow': ['pilot'], 'lossrow': ['pilot'], 'tabPilot': ['pilot'],
    'pilotSideTag': ['pilot'], 'lastKillInfo': ['pilot'], 'lkPivotBtn': ['pilot'],
    'fk': ['pilot', 'system', 'intel'],
    'mys': ['myship'], 'dmg': ['myship'], 'wp': ['myship'], 'weak': ['myship', 'fit', 'pilot'], 'wk': ['myship', 'fit', 'pilot'],
    'ttk': ['myship'], 'fs': ['myship'], 'mt': ['myship'],
    'chg': ['fit'], 'fit': ['fit', 'pilot'], 'fititem': ['fit'], 'fitgroup': ['fit'], 'ring': ['fit'], 'rack': ['fit'], 'bay': ['fit'],
    'ms': ['fit'], 'td': ['fit'], 'fl': ['fit', 'layout'], 'fitResults': ['fit'], 'fitCandidates': ['fit'], 'fitAnalyzerResults': ['fit'],
    'resistance': ['fit', 'pilot'], 'repairs': ['fit', 'pilot'], 'ewar': ['fit', 'pilot'], 'cap': ['fit', 'pilot'],
    'firepower': ['fit', 'pilot'], 'nav': ['fit', 'pilot'], 'rec': ['fit', 'pilot', 'myship'], 'drone': ['fit', 'pilot'],
}
# Keyed text tables (card names, info panels, error codes): a changed entry belongs to its key's area (text can't change a number)
TABLES = re.compile(r'^const (CARD_NAMES|CARD_INFO|ERROR_CODES)\b')
KEYS = {
    'intel': ['intel'], 'itnear': ['intel'], 'itfeed': ['intel'], 'INTEL': ['intel'],
    'sysan': ['system'], 'side': ['system'], 'hostile': ['system', 'intel'], 'neutral': ['system', 'intel'], 'friendly': ['system', 'intel'],
    'onscan': ['system'], 'pilots': ['system'], 'vs': ['system', 'myship'], 'SA': ['system'], 'SIDE': ['system'], 'DSCAN': ['system'],
    'aff': ['pilot'], 'dossier': ['pilot'], 'lastkill': ['pilot'], 'ZKB': ['pilot', 'intel'], 'SHARE': ['pilot', 'extension'],
    'fleet': ['pilot', 'system', 'intel'], 'fksum': ['pilot', 'system', 'intel'], 'fkvictim': ['pilot', 'system', 'intel'],
    'fkpilots': ['pilot', 'system', 'intel'], 'fkvs': ['pilot', 'system', 'intel'], 'FK': ['pilot', 'system', 'intel'],
    'dmg': ['myship'], 'board': ['myship'], 'perspective': ['myship'], 'myshippage': ['myship'], 'MYSHIP': ['myship'],
    'weak': ['fit', 'pilot', 'myship'], 'ewar': ['fit', 'pilot'], 'fp': ['fit', 'pilot'], 'rs': ['fit', 'pilot'], 'nav': ['fit', 'pilot'],
    'cp': ['fit', 'pilot'], 'fit': ['fit', 'pilot'], 'tdmode': ['fit', 'pilot'], 'FIT': ['fit'], 'EFT': ['fit'],
    'ESI': ['pilot', 'system', 'fit'],
}
SKIP_LINE = re.compile(r'class="build-tag"')   # the version tag changes every delivery

# Files other than index.html: (glob, areas), first match wins
FILES = [
    ('index.html', None),
    ('tools/page_checks/*', 'pagecheck'),
    ('regression_suite/*', [CHAIN, 'calc']),
    ('tools/independent_checks/*', [CHAIN, 'calc']),
    ('tools/pyfa_*', [CHAIN, 'calc']), ('tools/cap_sim_oracle.py', [CHAIN, 'calc']), ('tools/audit_*', [CHAIN, 'calc']),
    ('tools/gen_intel_tables.py', ['intel']), ('tools/jump_table_update.py', ['intel']),
    ('tools/gen_errors_md.py', []), ('tools/gen_*', [CHAIN, 'calc']),
    ('tools/check_pyfa_core.mjs', [CHAIN, 'calc']), ('tools/check_py_round.mjs', [CHAIN, 'calc']), ('tools/dump_*', [CHAIN, 'calc']),
    ('tools/speed_prop_effects.sha256', [CHAIN, 'calc']), ('tools/select_class_presets.py', [CHAIN, 'calc']),
    ('tools/refresh_golden_fixtures.py', [CHAIN, 'calc']),
    ('tools/check_*', []), ('tools/run_checks.py', []), ('tools/README.md', []), ('tools/pii_*', []),
    ('tools/git-hooks/*', []),
    ('browser-extension/*', ['extension']),
    ('img/*', ['layout']),
    ('*.md', []), ('dscan-tool-history/*', []), ('roadmap/*', []), ('Claude outputs/*', []), ('todo-inbox/*', []),
    ('.github/*', []), ('.gitignore', []), ('.gitattributes', []), ('*.local.txt', []),
]
IGNORE_DIRS = {'.git', '__pycache__', 'node_modules'}


def _line_info(lines):
    """Per line: (kind, areas) where kind is 'skip' (blank, comment, version tag) or 'code'."""
    out, mode, in_cmt, region, sym_areas, core, last_sel, table, key_areas = [], 'html', False, [ALL], None, False, '', False, [PAGES]
    for l in lines:
        s = l.strip()
        if re.search(r'<style\b', l): mode = 'css'
        elif re.search(r'<script\b', l) and 'src=' not in l: mode = 'js'
        info = ('skip', [])
        if mode == 'js':
            for rx, areas in REGIONS:
                if re.match(rx, l): region = areas
            m = re.match(r'(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)|(?:const|let|var|class)\s+([A-Za-z_$][\w$]*)', l)
            if m:
                name = m.group(1) or m.group(2)
                p = re.match(r'[a-z]+|[A-Z][A-Z0-9]*(?=_|$)|[A-Z][a-z]+', name)
                sym_areas = PREFIX.get(p.group(0)) if p else None
                table = bool(TABLES.match(l)); key_areas = [PAGES]
            if table:
                k = re.match(r'^ "([^"]+)"\s*:', l)
                if k: key_areas = KEYS.get(re.split(r'[#.\-]', k.group(1))[0], [PAGES])
            if 'PYFA CORE BEGIN' in l: core = True
            cmt = in_cmt or s.startswith('//') or s.startswith('/*') or s.startswith('*')
            if s.startswith('/*') and '*/' not in s: in_cmt = True
            if in_cmt and '*/' in s: in_cmt = False
            if s and not cmt: info = ('code', [CHAIN, 'calc'] if core else key_areas if table else (sym_areas or region))
            if 'PYFA CORE END' in l: core = False
        elif mode == 'css':
            was = in_cmt
            if '/*' in s and '*/' not in s.split('/*', 1)[1]: in_cmt = True
            if in_cmt and '*/' in s: in_cmt = False
            code = re.sub(r'/\*.*?\*/', '', s).strip()
            sel = last_sel
            if '{' in code:
                head, rest = code.split('{', 1)
                if head.lstrip().startswith('@'):   # @media (...){ .it-x{...} }: the rule inside, if any
                    sel = rest.split('{')[0] if '{' in rest else None
                else: sel = head
                if sel is not None: last_sel = sel
            if code and not was and sel is not None and not re.fullmatch(r'[{}\s]*', code) and not code.startswith('<'):
                info = ('code', _css_areas(sel))
        else:   # markup
            if s and not SKIP_LINE.search(l) and not s.startswith('<!--'):
                toks = re.findall(r'(?:id|class)="([^"]+)"', l)
                info = ('code', _css_areas(' '.join('.' + t for t in ' '.join(toks).split())) if toks else [PAGES])
        if SKIP_LINE.search(l): info = ('skip', [])
        out.append(info)
        if '</style>' in l or '</script>' in l: mode = 'html'
    return out


def _css_areas(sel):
    areas = set()
    for t in re.findall(r'[.#]([A-Za-z][\w-]*)', sel):
        for key in (t, re.split(r'[-_]|(?<=[a-z])(?=[A-Z])', t)[0]):
            if key in CSS: areas.update(CSS[key]); break
    return sorted(areas) or [PAGES]


def map_html(old, new):
    """Areas for the lines that differ between two versions of index.html, and a few examples of why."""
    a, b = old.split('\n'), new.split('\n')
    ia, ib = _line_info(a), _line_info(b)
    areas, why = set(), {}
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal': continue
        for info, lines, rng in ((ia, a, range(i1, i2)), (ib, b, range(j1, j2))):
            for i in rng:
                kind, ar = info[i]
                if kind != 'code': continue
                areas.update(ar)
                for x in ar: why.setdefault(x, f'index.html line {i + 1}: {lines[i].strip()[:70]}')
    return areas, why


def _page_check_areas(root, stem, AREAS):
    areas = set(AREAS.get(stem, []))
    pc = os.path.join(root, 'tools', 'page_checks')
    for f in os.listdir(pc):   # the checks that build on this one (they read its source or import it)
        if f.endswith('_check.py') and f[:-3] != stem and stem in open(os.path.join(pc, f), encoding='utf-8', errors='replace').read():
            areas.update(AREAS.get(f[:-3], []))
    return areas or {PAGES}


def changed_files(root, since=None):
    """[(path, old_text_or_None, new_text_or_None)] relative to the repo root."""
    out = []
    def rd(p):
        try: return open(p, encoding='utf-8', errors='replace').read()
        except (FileNotFoundError, IsADirectoryError): return None
    if since:
        def walk(base):
            r = set()
            for d, ds, fs in os.walk(base):
                ds[:] = [x for x in ds if x not in IGNORE_DIRS]
                for f in fs: r.add(os.path.relpath(os.path.join(d, f), base).replace(os.sep, '/'))
            return r
        for p in sorted(walk(root) | walk(since)):
            o, n = os.path.join(since, p), os.path.join(root, p)
            ob = open(o, 'rb').read() if os.path.isfile(o) else None
            nb = open(n, 'rb').read() if os.path.isfile(n) else None
            if ob != nb: out.append((p, rd(o), rd(n)))
        return out
    if not os.path.isdir(os.path.join(root, '.git')):
        raise SystemExit('check_picker: no .git folder here; give --since <a copy of the repo as last delivered>')
    g = lambda *a: subprocess.run(['git', '-C', root, *a], capture_output=True, text=True).stdout
    names = set(g('diff', '--name-only', 'HEAD').split()) | set(g('ls-files', '--others', '--exclude-standard').split())
    for p in sorted(names):
        old = subprocess.run(['git', '-C', root, 'show', f'HEAD:{p}'], capture_output=True, text=True)
        out.append((p, old.stdout if old.returncode == 0 else None, rd(os.path.join(root, p))))
    return out


def deliveries_since_full(root):
    try: rows = [l for l in open(os.path.join(root, 'tools', 'check_ledger.md'), encoding='utf-8') if re.match(r'\| \d{4}-\d\d-\d\d \|', l)]
    except FileNotFoundError: return 0
    n = 0
    for r in reversed(rows):
        run = r.split('|')[3].strip()
        if re.match(r'(auto: )?all\b', run): break
        n += 1
    return n


def pick(root, since=None, AREAS=None, names=None):
    """-> (tier, areas, reasons)"""
    areas, why = set(), {}
    for p, old, new in changed_files(root, since):
        rule = next((r for g, r in FILES if fnmatch.fnmatch(p, g)), [ALL])
        if p == 'index.html':
            if old is None or new is None: got, w = {ALL}, {ALL: 'index.html added or removed'}
            else: got, w = map_html(old, new)
            areas |= got
            for k, v in w.items(): why.setdefault(k, v)
            continue
        got = _page_check_areas(root, os.path.basename(p)[:-3], AREAS) if rule == 'pagecheck' and p.endswith('.py') else set(rule if rule != 'pagecheck' else [PAGES])
        areas |= got
        for x in got: why.setdefault(x, p)
        if not got: why.setdefault('fast', p)
    n = deliveries_since_full(root)
    if ALL in areas: tier = 'all'
    elif n >= 4: tier = 'all'; why[ALL] = f'every 5th delivery: {n} ledger rows since the last full run'
    elif CHAIN in areas: tier = 'calc'
    elif areas: tier = 'area'
    else: tier = 'fast'
    if tier == 'all': return tier, [], why
    if PAGES in areas: areas = set(names or [])
    return tier, sorted(areas - {ALL, CHAIN, PAGES}), why


def self_test(root):
    """Made-up one-line edits of the real index.html, each with the areas it must map to; every region start found once."""
    html = open(os.path.join(root, 'index.html'), encoding='utf-8').read(); L = html.split('\n'); problems = []
    for rx, _ in REGIONS:
        n = sum(1 for l in L if re.match(rx, l))
        if n != 1: problems.append(f'region start {rx!r} matches {n} lines (rename it here when the section moves)')
    def at(rx, after=None, skip=0):
        start = next((i for i, l in enumerate(L) if after and re.search(after, l)), 0) if after else 0
        hits = [i for i, l in enumerate(L) if i >= start and re.search(rx, l)]
        return hits[skip] if len(hits) > skip else None
    cases = [   # (what, where: (regex, after), expected areas or ALL / nothing)
        ('an Intel function', (r'^function itAnalyzeHtml\b', None), {'intel'}),
        ('a pyfa core line', (r'pyfaPenalizedProduct', r'PYFA CORE BEGIN stacking-penalty'), {CHAIN, 'calc'}),
        ('the engine', (r'^async function estimateHpAndDps\b', None), {CHAIN, 'calc'}),
        ('a System Analyzer function', (r'^function sa[A-Z]', None), {'system'}),
        ('the dossier', (r'^function pdHtml\b', None), {'pilot'}),
        ('shared code', (r'^function escapeHtml\b', None), {ALL}),
        ('Intel CSS', (r'^\s*\.it-nb\.dd\{', None), {'intel'}),
        ('a shared CSS token', (r'--tag-fill:', None), {PAGES}),
        ('the Intel info text', (r'^ "intel": \[', r'^const CARD_INFO\b'), {'intel'}),
        ('a comment', (r'^// ==== INTEL ', None), set()),
        ('the version tag', (r'class="build-tag"', None), set()),
    ]
    for what, (rx, after), want in cases:
        i = at(rx, after)
        if i is None: problems.append(f'{what}: no line matches {rx!r}'); continue
        j = i + 1 if what == 'the Intel info text' else i   # the entry's text, not its key
        new = L[:j] + [L[j] + ' /*x*/ 1'] + L[j + 1:] if what not in ('a comment', 'the version tag') else L[:j] + [L[j] + ' x'] + L[j + 1:]
        got, _ = map_html(html, '\n'.join(new))
        if got != want: problems.append(f'{what} (line {j + 1}): {sorted(got)}, expected {sorted(want)}')
    for p in problems: print('PROBLEM', p)
    print(f'CHECK PICKER: {len(REGIONS)} regions, {len(cases)} made-up edits; {len(problems)} problems')
    return 1 if problems else 0


if __name__ == '__main__':
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from run_checks import AREAS, NAMES
    argv = sys.argv[1:]
    if '--self-test' in argv: sys.exit(self_test(root))
    since = argv[argv.index('--since') + 1] if '--since' in argv else None
    tier, areas, why = pick(root, since, AREAS, NAMES)
    print(f'PICKED: tier {tier}' + (f' --area {",".join(areas)}' if areas else ''))
    for k, v in sorted(why.items()): print(f'  {k}: {v}')
