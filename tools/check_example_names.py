"""The Intel example's made-up names (v2026.11.07.7, build queue 017; Project doc roadmap/intel-example-plan.md section 3; the owner:
"make sure none of the pilot names or tickers match a real pilot name").

    python3 -I tools/check_example_names.py [index.html]          -> 'EXAMPLE NAMES: ... 0 problems' (offline; a fast lint)
    python3 -I tools/check_example_names.py --live [index.html]   -> also asks ESI once (POST /universe/ids/, every name in one request)

Offline it reads IT_EXAMPLE from the page (with node) and checks its shape: every id negative and used once (ESI never hands out a
negative id, and the page never sends these anywhere); every pilot's corporation and every corporation's alliance in the list; tickers
3-5 capitals, none twice and none of the checks' made-up ones; no name from tools/page_checks/sa_mocks.py (those stay test-only) or
from the private names list (tools/pii_terms.local.txt, when it is there); every system named in IT_EXAMPLE.sys is in the page's jump
table. It never makes a request.

--live is run once by hand before delivering a change to the names, never inside the regular checks (CLAUDE.md, LESSON #93's spirit:
no live requests from the checks): ESI must find no character, corporation or alliance by any of the names. ESI can't look up tickers,
so the tickers are printed for the owner to check once on zKillboard's search before merging.
"""
import sys, os, re, json, subprocess, base64, struct
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CHECK_TICKERS = {'RLH', 'CRTS', 'EXMPL', 'EXA', 'NGLS', 'VOIDR'}   # the mockup's, from the checks' made-up data


def example(html):
    m = re.search(r'\nconst IT_EXAMPLE = (\{.*?\n\});', html, re.S)
    if not m: return None
    out = subprocess.run(['node', '-e', 'const X = ' + m.group(1) + '; process.stdout.write(JSON.stringify(X));'], capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout) if out.returncode == 0 else None


def mock_names():
    p = os.path.join(ROOT, 'tools', 'page_checks', 'sa_mocks.py')
    src = open(p, encoding='utf-8').read() if os.path.exists(p) else ''
    return {w.lower() for w in re.findall(r"'([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)+)'", src)} | {w.lower() for w in re.findall(r"'([A-Z][a-z]+)'", src)}


def private_terms():
    p = os.path.join(ROOT, 'tools', 'pii_terms.local.txt')
    if not os.path.exists(p): return None
    return [l.strip().lower() for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')]


def jump_ids(html):
    J = json.loads(re.search(r'const INTEL_JUMPS = (\{.*?\});', html).group(1))
    b = base64.b64decode(J['sys']); d = struct.unpack('<%dH' % (len(b) // 2), b); ids = set(); p = 30000000
    for v in d: p += v; ids.add(p)
    return ids


def problems(X, html):
    bad = []
    if not X: return ['IT_EXAMPLE not found in the page (or node could not read it)']
    ids = [o[0] for o in X['orgs']] + [p[0] for p in X['pilots']]
    if any(not isinstance(i, int) or i >= 0 for i in ids): bad.append('an example id is not negative (they must never be a real id)')
    if len(ids) != len(set(ids)): bad.append('an example id is used twice')
    orgs = {o[0]: o for o in X['orgs']}
    for o in X['orgs']:
        if o[4] is not None and (o[4] not in orgs or orgs[o[4]][1] != 'alliance'): bad.append(f'{o[2]}: its alliance {o[4]} is not in the list')
    for p in X['pilots']:
        if p[2] not in orgs or orgs[p[2]][1] != 'corporation': bad.append(f'{p[1]}: its corporation {p[2]} is not in the list')
    tk = [o[3] for o in X['orgs']]
    for t in tk:
        if not re.fullmatch(r'[A-Z]{3,5}', t): bad.append(f'ticker {t!r}: not 3-5 capitals')
        if t in CHECK_TICKERS: bad.append(f'ticker {t}: one of the checks\' made-up tickers')
    if len(tk) != len(set(tk)): bad.append('a ticker is used twice')
    names = [o[2] for o in X['orgs']] + [p[1] for p in X['pilots']]
    mocks = mock_names()
    for n in names:
        if n.lower() in mocks: bad.append(f'{n}: a name from sa_mocks.py (test-only names)')
    priv = private_terms()
    if priv is not None:
        for n in names + tk:
            if any(t and (t in n.lower() or n.lower() in t) for t in priv): bad.append('an example name or ticker matches the private names list (not printed)')
    if len(names) != len({n.lower() for n in names}): bad.append('a name is used twice')
    for sid in X['sys']:
        if int(sid) not in jump_ids(html): bad.append(f'system {sid} is not in the jump table')
    for k in ('home', 'you'):
        if k not in X: bad.append(f'IT_EXAMPLE.{k} is missing')
    return bad


def live(X):
    import urllib.request
    names = [o[2] for o in X['orgs']] + [p[1] for p in X['pilots']]
    req = urllib.request.Request('https://esi.evetech.net/latest/universe/ids/?datasource=tranquility', data=json.dumps(names).encode(),
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'threatvector check_example_names (one request, by hand)'}, method='POST')
    with urllib.request.urlopen(req, timeout=30) as r:
        got = json.loads(r.read() or b'{}')
    hits = [(k, x['name']) for k in ('characters', 'corporations', 'alliances') for x in got.get(k, [])]
    for k, n in hits: print(f'EXAMPLE NAMES LIVE: ESI has a {k[:-1]} named {n!r}: pick another name')
    print(f'EXAMPLE NAMES LIVE: {len(names)} names asked of ESI in one request; {len(hits)} found (must be 0)')
    print('EXAMPLE NAMES LIVE: tickers for the owner to check once on zKillboard\'s search: ' + ', '.join(o[3] for o in X['orgs']))
    return 1 if hits else 0


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    path = args[0] if args else os.path.join(ROOT, 'index.html')
    html = open(path, encoding='utf-8').read()
    X = example(html)
    bad = problems(X, html)
    for b in bad: print('EXAMPLE NAMES', b)
    priv = 'checked' if private_terms() is not None else 'not here (copy it in from the Project)'
    print(f'EXAMPLE NAMES: {len(X["pilots"]) if X else 0} pilots, {len(X["orgs"]) if X else 0} groups; the private names list {priv}; {len(bad)} problems')
    rc = 1 if bad else 0
    if '--live' in argv and X and not bad: rc |= live(X)
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
