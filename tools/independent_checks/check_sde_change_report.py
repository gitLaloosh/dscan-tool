"""tools/sde_change_report.py on made-up copies of CCP's data (v2026.11.04.3, build queue 008). No network: a local web server
in this process stands in for CCP's static-data site (with and without range requests).

    python3 -I tools/independent_checks/check_sde_change_report.py [index.html]    -> 'SDE CHANGE REPORT: 0 problems'

Made up: build 3624000 (at or before the verified build, the manifest's clientBuild 3624425) and build 3700000, with a
changes chain 3700000 -> 3650000 -> 3624000. Between them: a new ship with an effect pyfa has (4) and one it doesn't
(990001, a new effect ID); a module's attribute 10 -> 12; a module newly published; a charge unchanged; a SKIN (out of
scope) changed; a drone removed. Expected list: the new ship, the changed module, the published module.
"""
import os, sys, io, re, json, shutil, zipfile, tempfile, threading, subprocess, http.server, base64, struct

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
HTML = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
TOOL = os.path.join(ROOT, 'tools', 'sde_change_report.py')
OLD, MID, NEW = 3624000, 3650000, 3700000
problems = []
def check(ok, msg):
    if not ok: problems.append(msg)

def jl(rows): return '\n'.join(json.dumps(r) for r in rows) + '\n'
def name(s): return {'en': s, 'de': s}
GROUPS = [{'_key': 25, 'categoryID': 6, 'name': name('Frigate')}, {'_key': 60, 'categoryID': 7, 'name': name('Damage Control')},
          {'_key': 83, 'categoryID': 8, 'name': name('Projectile Ammo')}, {'_key': 100, 'categoryID': 18, 'name': name('Combat Drone')},
          {'_key': 1950, 'categoryID': 91, 'name': name('Permanent SKIN')}]
ATTRS = [{'_key': 9, 'name': 'hp'}, {'_key': 30, 'name': 'power'}, {'_key': 50, 'name': 'cpu'}]
def types(new):
    t = [{'_key': 900001, 'groupID': 25, 'name': name('Testfrig'), 'published': True, 'mass': 1000000.0},
         {'_key': 900101, 'groupID': 60, 'name': name('Test Damage Control'), 'published': True, 'mass': 1.0},
         {'_key': 900102, 'groupID': 60, 'name': name('Test Hidden Module'), 'published': new},
         {'_key': 900301, 'groupID': 83, 'name': name('Test Ammo S'), 'published': True},
         {'_key': 900201, 'groupID': 1950, 'name': name('Testfrig SKIN' + (' v2' if new else '')), 'published': True}]
    if new: t.append({'_key': 900002, 'groupID': 25, 'name': name('Test Navy Frigate'), 'published': True, 'mass': 1200000.0})
    else: t.append({'_key': 900401, 'groupID': 100, 'name': name('Test Drone'), 'published': True})
    return t
def dogma(new):
    d = [{'_key': 900001, 'dogmaAttributes': [{'attributeID': 9, 'value': 400.0}], 'dogmaEffects': [{'effectID': 4, 'isDefault': False}]},
         {'_key': 900101, 'dogmaAttributes': [{'attributeID': 30, 'value': 12.0 if new else 10.0}, {'attributeID': 50, 'value': 20.0}]},
         {'_key': 900301, 'dogmaAttributes': [{'attributeID': 9, 'value': 1.0}]}]
    if new: d.append({'_key': 900002, 'dogmaAttributes': [{'attributeID': 9, 'value': 450.0}], 'dogmaEffects': [{'effectID': 4, 'isDefault': False}, {'effectID': 990001, 'isDefault': False}]})
    return d
def effects(new): return [{'_key': 4, 'name': 'shieldBoosting'}] + ([{'_key': 990001, 'name': 'shipBonusTestNavy'}] if new else [])
def files(new): return {'types.jsonl': jl(types(new)), 'groups.jsonl': jl(GROUPS), 'typeDogma.jsonl': jl(dogma(new)),
                        'dogmaEffects.jsonl': jl(effects(new)), 'dogmaAttributes.jsonl': jl(ATTRS), 'mapStargates.jsonl': ''}

tmp = tempfile.mkdtemp(prefix='sdecr-')
try:
    for b, new in ((OLD, False), (NEW, True)):
        d = os.path.join(tmp, f'sde{b}'); os.makedirs(d)
        for n, t in files(new).items(): open(os.path.join(d, n), 'w').write(t)
    site = os.path.join(tmp, 'site'); os.makedirs(os.path.join(site, 'changes'))
    def zipit(b, new):
        with zipfile.ZipFile(os.path.join(site, f'eve-online-static-data-{b}-jsonl.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
            for n, t in files(new).items(): z.writestr(n, t)
    zipit(NEW, True)
    open(os.path.join(site, 'latest.jsonl'), 'w').write(jl([{'_key': 'sde', 'buildNumber': NEW, 'releaseDate': '2026-11-10T11:08:00Z'}]))
    open(os.path.join(site, 'changes', f'{NEW}.jsonl'), 'w').write(jl([{'_key': '_meta', 'buildNumber': NEW, 'lastBuildNumber': MID},
        {'_key': 'types', 'added': [900002], 'changed': [900102, 900201]}, {'_key': 'typeDogma', 'added': [900002]}, {'_key': 'dogmaEffects', 'added': [990001]}]))
    open(os.path.join(site, 'changes', f'{MID}.jsonl'), 'w').write(jl([{'_key': '_meta', 'buildNumber': MID, 'lastBuildNumber': OLD},
        {'_key': 'typeDogma', 'changed': [900101]}, {'_key': 'types', 'removed': [900401], 'changedLocalization': [900301]}]))
    pa, pb = os.path.join(tmp, 'pyfaA'), os.path.join(tmp, 'pyfaB')
    for p, extra in ((pa, ''), (pb, 'class Effect990001(BaseEffect):\n    pass\n')):
        os.makedirs(os.path.join(p, 'eos')); open(os.path.join(p, 'version.yml'), 'w').write('version: v9.9.9\n')
        open(os.path.join(p, 'eos', 'effects.py'), 'w').write('class Effect4(BaseEffect):\n    pass\n' + extra)

    RANGES = {'on': True}
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k): super().__init__(*a, directory=site, **k)
        def log_message(self, *a): pass
        def send_head(self):
            rng = self.headers.get('Range')
            path = self.translate_path(self.path)
            if not (RANGES['on'] and rng and os.path.isfile(path)): return super().send_head()
            a, b = (int(x) for x in re.match(r'bytes=(\d+)-(\d+)', rng).groups())
            data = open(path, 'rb').read()[a:b + 1]
            self.send_response(206); self.send_header('Content-Length', str(len(data))); self.end_headers()
            return io.BytesIO(data)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{srv.server_address[1]}'

    def run(*extra, html=None):
        page = html or os.path.join(tmp, 'index.html')
        if not html: shutil.copy(HTML, page)
        env = {k: v for k, v in os.environ.items() if k not in ('PYFA_SRC', 'GITHUB_OUTPUT')}
        p = subprocess.run([sys.executable, '-I', TOOL, page, '--base', base, *extra], capture_output=True, text=True, env=env, timeout=120)
        return p.returncode, p.stdout + p.stderr, page
    def pending(page):
        m = re.search(r"^const GAME_DATA_PENDING = \{verified: (\d+), build: (\d+), types: '([^']*)'\};", open(page, encoding='utf-8').read(), re.M)
        b = base64.b64decode(m.group(3)); return int(m.group(2)), set(struct.unpack('>%dI' % (len(b) // 4), b))
    WANT = {900002, 900101, 900102}
    local = ('--sde-old', os.path.join(tmp, f'sde{OLD}'), '--old-build', str(OLD), '--sde-new', os.path.join(tmp, f'sde{NEW}'), '--new-build', str(NEW))

    # 1. local folders, pyfa without the new effect's class
    rc, o, page = run(*local, '--pyfa', pa, '--write', '--body', os.path.join(tmp, 'body.md'))
    check(rc == 0, f'local run failed: {o[-400:]}')
    check('build 3624000 -> 3700000' in o and 'method: full' in o and 'pyfa v9.9.9' in o, 'local: header (builds, method, pyfa version) missing')
    check('### New ships (1)' in o and '**Test Navy Frigate** (900002): new' in o, 'local: the new ship is not listed under New ships')
    check('power 10 -> 12' in o, 'local: the module\'s attribute change (power 10 -> 12) is missing')
    check('Test Hidden Module** (900102): changed' in o and '  - published' in o, 'local: the newly published module is missing')
    check('shipBonusTestNavy (990001) **(no pyfa handler)**' in o, 'local: the new effect pyfa lacks is not flagged')
    check('effect added: shieldBoosting (4)' in o and 'shieldBoosting (4) **(no pyfa handler)**' not in o, 'local: an effect pyfa has is flagged')
    check('SKIN' not in o and 'Test Ammo' not in o, 'local: an out-of-scope or unchanged item is listed')
    check('Test Drone** (900401): removed' in o, 'local: the removed drone is not listed')
    check(pending(page) == (NEW, WANT), f'local --write: list {pending(page)} (want build {NEW}, {sorted(WANT)})')
    check(os.path.exists(os.path.join(tmp, 'body.md')) and 'Test Navy Frigate' in open(os.path.join(tmp, 'body.md')).read(), 'local: the pull request text was not written')
    # the list check passes on what --write wrote (a copy beside the tools, for the manifest)
    lint = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'tools', 'check_game_data_pending.py'), page], capture_output=True, text=True)
    check(lint.stdout.strip().endswith('3 item(s) listed; 0 problems'), f'check_game_data_pending on the written page: {lint.stdout.strip()[-200:]}')

    # 2. the same again: the page already lists them -> no change, nothing written
    before = open(page, encoding='utf-8').read()
    gh = os.path.join(tmp, 'gh_out'); open(gh, 'w').close()
    env_out = dict(os.environ, GITHUB_OUTPUT=gh)
    p = subprocess.run([sys.executable, '-I', TOOL, page, '--base', base, *local, '--pyfa', pa, '--write'], capture_output=True, text=True, env=env_out, timeout=120)
    check('(the page lists the same)' in p.stdout and open(page, encoding='utf-8').read() == before, 'local again: the list was rewritten though nothing changed')
    check('changed=false' in open(gh).read(), 'local again: the step output is not changed=false')

    # 3. pyfa with the class: nothing flagged
    rc, o, _ = run(*local, '--pyfa', pb)
    check('no pyfa handler' not in o, 'pyfa B (has Effect990001): a handler is still reported missing')

    # 4. over "the web": latest.jsonl, the chain back past the verified build, both zips by range requests
    zipit(OLD, False)
    rc, o, page = run('--pyfa', pa, '--write')
    check(rc == 0 and 'method: full' in o and 'build 3624000 -> 3700000' in o, f'web, range requests: {o[-300:]}')
    check(pending(page) == (NEW, WANT), f'web, range requests: list {pending(page)}')
    # 5. a server without range requests: whole zips, same answer
    RANGES['on'] = False
    rc, o2, page = run('--pyfa', pa)
    check(rc == 0 and o2.split('pending list')[0] == o.split('pending list')[0], f'web, no range requests: a different report:\n{o2[:600]}\n---\n{o[:600]}')
    RANGES['on'] = True
    # 6. the older zip no longer published: the changes files say which items changed
    os.remove(os.path.join(site, f'eve-online-static-data-{OLD}-jsonl.zip'))
    rc, o, page = run('--pyfa', pa, '--write')
    check(rc == 0 and 'method: changes' in o, f'web, old zip gone: not the changes method: {o[-300:]}')
    check('changed (old values not published)' in o and 'shipBonusTestNavy (990001) **(no pyfa handler)**' in o, 'web, old zip gone: the changed items or the missing handler are not listed')
    b, ids = pending(page)
    check(b == NEW and {900002, 900101, 900102} <= ids and 900201 not in ids, f'web, old zip gone: list {sorted(ids)}')
    # 7. the page's list is already for the newest build: nothing downloaded, nothing new
    rc, o, page2 = run('--pyfa', pa, html=page)
    check('nothing new' in o, 'the page\'s list already for the newest build: not "nothing new"')
    # 8. a build with no item data changes at all: no download (the changes files say so)
    shutil.copy(HTML, os.path.join(tmp, 'index.html'))
    for b, last in ((NEW, MID), (MID, OLD)):
        open(os.path.join(site, 'changes', f'{b}.jsonl'), 'w').write(jl([{'_key': '_meta', 'buildNumber': b, 'lastBuildNumber': last}, {'_key': 'icons', 'added': [1]}]))
    os.remove(os.path.join(site, f'eve-online-static-data-{NEW}-jsonl.zip'))   # would fail if it were downloaded
    rc, o, _ = run('--pyfa', pa, html=os.path.join(tmp, 'index.html'))
    check(rc == 0 and 'no item data changed' in o, f'no item changes in the chain: {o[-300:]}')
    srv.shutdown()

    # 9. the list check catches a hand edit: unsorted, repeated, a verified build not the manifest's, items without a build
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    from check_game_data_pending import encode
    vb = json.load(open(os.path.join(ROOT, 'tools', 'pyfa_core_manifest.json')))['pyfa']['clientBuild']
    lint_dir = os.path.join(tmp, 'lint'); os.makedirs(os.path.join(lint_dir, 'tools'))
    shutil.copy(os.path.join(ROOT, 'tools', 'pyfa_core_manifest.json'), os.path.join(lint_dir, 'tools'))
    src = open(HTML, encoding='utf-8').read()
    rx = re.compile(r"^const GAME_DATA_PENDING = .*;$", re.M)
    raw = lambda ids: base64.b64encode(struct.pack('>%dI' % len(ids), *ids)).decode()
    for label, ln, bad in (('sorted', f"const GAME_DATA_PENDING = {{verified: {vb}, build: {NEW}, types: '{encode([5, 9])}'}};", False),
                           ('unsorted', f"const GAME_DATA_PENDING = {{verified: {vb}, build: {NEW}, types: '{raw([9, 5])}'}};", True),
                           ('repeated', f"const GAME_DATA_PENDING = {{verified: {vb}, build: {NEW}, types: '{raw([5, 5])}'}};", True),
                           ('verified not the manifest\'s', f"const GAME_DATA_PENDING = {{verified: {vb - 1}, build: {NEW}, types: ''}};", True),
                           ('items without a later build', f"const GAME_DATA_PENDING = {{verified: {vb}, build: 0, types: '{encode([5])}'}};", True),
                           ('not base64 of whole numbers', f"const GAME_DATA_PENDING = {{verified: {vb}, build: {NEW}, types: 'AAA='}};", True)):
        page = os.path.join(lint_dir, 'index.html'); open(page, 'w', encoding='utf-8').write(rx.sub(ln.replace('\\', '\\\\'), src, count=1))
        o = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'tools', 'check_game_data_pending.py'), page], capture_output=True, text=True).stdout
        check(o.splitlines()[0].endswith(' 0 problems') != bad, f'the list check, {label}: {o.splitlines()[0] if o else "no output"}')
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f'SDE CHANGE REPORT: {len(problems)} problems')
for p in problems: print('  ' + p)
sys.exit(1 if problems else 0)
