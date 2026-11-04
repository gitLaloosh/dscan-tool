"""tools/jump_table_update.py (the GitHub Action's jump-table check, v2026.10.29.5) on made-up copies of CCP's data.

    python3 -I tools/independent_checks/check_jump_table_update.py [index.html]   -> 'JUMP TABLE UPDATE: N problems' (must be 0)

The Action can't be run here (CCP's site isn't reachable from the cloud workspace), so its script is run on CCP's file
layout built from the page's own table: mapStargates.jsonl (one record per gate, each connection as two gates with
solarSystemID and destination.solarSystemID, as in CCP's file), mapSolarSystems.jsonl (names), latest.jsonl (the build).
  * the same gates on a newer build: "matches", changed=false, the page untouched, exit 0 (--check too);
  * one connection removed and one added (to a new system): changed=true and the build as step outputs, the two
    named in the pull request's text, the page's table rewritten; read back it has exactly the new connections and the
    same encoding as tools/gen_intel_tables.py (sys/edges round-trip); --check then exits 1 on the old page;
  * the rewritten page passes the check against the same data (nothing to do the next time).
v2026.11.02.4 (the Intel map): mapSolarSystems.jsonl also carries position2D, securityStatus and regionID, and mapRegions.jsonl the
region names, made from the page's own INTEL_MAP, so:
  * with the same data the map matches too; after a gate change INTEL_MAP is rewritten with INTEL_JUMPS, aligned to its new
    fingerprint and systems (a new system gets its position);
  * one system moved on CCP's map with no gate changed: changed=true, the pull request says the map changed, only INTEL_MAP
    rewritten (that system's position, nothing else), --check exits 1 before and 0 after.
v2026.11.04.1 (light-years in the map's hover): mapSolarSystems.jsonl also carries each system's geographic position (3D,
metres), made here from the page's own INTEL_MAP.p3 with CCP's light-year (9.46e15 m) written out in this check, so:
  * the same data still matches (a script using another light-year, or another unit, fails here);
  * one system moved in space only (position2D unchanged): changed=true, only that system's x, y, z rewritten (3 values);
  * a page from before (INTEL_MAP without p3): changed=true, the positions added, every other value of INTEL_MAP unchanged;
  * a system with no position in CCP's data: the script stops (exit not 0) and the page is untouched.
"""
import sys, os, re, json, base64, struct, subprocess, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
HTML = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
SCRIPT = os.path.join(ROOT, 'tools', 'jump_table_update.py')
problems = []
def check(ok, msg):
    print(('OK   ' if ok else 'FAIL ') + msg)
    if not ok: problems.append(msg)

def table(path):
    s = open(path, encoding='utf-8').read()
    return json.loads(re.search(r'^const INTEL_JUMPS = (.*);$', s, re.M).group(1))
def conns_of(J):
    d = struct.unpack('<%dH' % (len(base64.b64decode(J['sys'])) // 2), base64.b64decode(J['sys']))
    e = struct.unpack('<%dH' % (len(base64.b64decode(J['edges'])) // 2), base64.b64decode(J['edges']))
    S, p = [], 30000000
    for x in d: p += x; S.append(p)
    return {(S[e[i]], S[e[i + 1]]) for i in range(0, len(e), 2)}, S
def mtable(path):
    s = open(path, encoding='utf-8').read(); m = re.search(r'^const INTEL_MAP = (.*);$', s, re.M)
    return json.loads(m.group(1)) if m else None
M0 = mtable(HTML)
LY_M, P3U = 9.46e15, 0.0001   # CCP's light-year (developers.eveonline.com map-data guide), the table's unit (the plan)
def p3_of(M):   # INTEL_MAP.p3 -> [x..., y..., z...] (int24 LE, signed), independently of the script
    b = base64.b64decode(M['p3']); return [int.from_bytes(b[i:i + 3], 'little', signed=True) for i in range(0, len(b), 3)]
def m_rows(M, S):   # system id -> (x, y, sec100, region index, (px, py, pz) in 0.0001 LY), from the page's INTEL_MAP aligned to S
    dec = lambda k, f: struct.unpack('<%d%s' % (M['systems'], f), base64.b64decode(M[k]))
    n = M['systems']; P = p3_of(M) if M.get('p3') else [0] * (3 * n)
    return {s: v + ((P[k], P[n + k], P[2 * n + k]),) for k, (s, v) in enumerate(zip(S, zip(dec('x', 'h'), dec('y', 'h'), dec('sec', 'b'), dec('reg', 'B'))))}
def sde(folder, conns, systems, build, rows=None, regions=None, nopos=()):
    os.makedirs(folder, exist_ok=True); L, g = [], 50000000
    for a, c in sorted(conns):
        L.append(json.dumps({'_key': g, 'destination': {'solarSystemID': c, 'stargateID': g + 1}, 'solarSystemID': a, 'typeID': 16}))
        L.append(json.dumps({'_key': g + 1, 'destination': {'solarSystemID': a, 'stargateID': g}, 'solarSystemID': c, 'typeID': 16})); g += 2
    open(os.path.join(folder, 'mapStargates.jsonl'), 'w', encoding='utf-8').write('\r\n'.join(L) + '\r\n')   # CRLF, as CCP's latest.jsonl
    rows = rows or {}; regions = regions or ['Region A']
    def rec(s):
        x, y, sec, rg, p = rows.get(s, (0, 0, 50, 0, (0, 0, 0)))
        o = {'_key': s, 'name': {'en': f'SYS-{s - 30000000}'}, 'position2D': {'x': x * 1e14, 'y': y * 1e14}, 'securityStatus': sec / 100, 'regionID': 10000001 + rg}
        if s not in nopos: o['position'] = {a: v * P3U * LY_M for a, v in zip('xyz', p)}   # metres, as CCP's file
        return o
    open(os.path.join(folder, 'mapSolarSystems.jsonl'), 'w', encoding='utf-8').write('\n'.join(json.dumps(rec(s)) for s in sorted(systems)) + '\n')
    open(os.path.join(folder, 'mapRegions.jsonl'), 'w', encoding='utf-8').write('\n'.join(json.dumps({'_key': 10000001 + k, 'name': {'en': r}}) for k, r in enumerate(regions)) + '\n')
    open(os.path.join(folder, 'latest.jsonl'), 'w', encoding='utf-8').write(json.dumps({'_key': 'sde', 'buildNumber': build, 'releaseDate': '2026-10-29T11:10:30Z'}) + '\r\n')
def run(page, folder, *extra, env=None):
    e = dict(os.environ); e.pop('GITHUB_OUTPUT', None); e.pop('GITHUB_STEP_SUMMARY', None); e.update(env or {})
    r = subprocess.run([sys.executable, '-I', SCRIPT, page, '--sde', folder, *extra], capture_output=True, text=True, env=e)
    return r.returncode, r.stdout + r.stderr

J0 = table(HTML); C0, S0 = conns_of(J0)
tmp = tempfile.mkdtemp(prefix='jtu-')
try:
    same, changed = os.path.join(tmp, 'same'), os.path.join(tmp, 'changed')
    R0 = m_rows(M0, S0) if M0 else {}; REG = M0['regions'] if M0 else None
    check(M0 is not None and M0['jumps'] == J0['md5'] and M0['systems'] == len(S0), "the page's INTEL_MAP is aligned to its INTEL_JUMPS")
    check(M0 is not None and M0.get('p3u') == P3U and len(p3_of(M0)) == 3 * len(S0) and max(abs(v) for v in p3_of(M0)) < 1 << 23 and len({R0[s][4] for s in S0}) > len(S0) - 5,
          f"the page's INTEL_MAP holds every system's position in space (p3, units {M0 and M0.get('p3u')} LY, {len(p3_of(M0)) if M0 and M0.get('p3') else 0} values)")
    sde(same, C0, S0, J0['build'] + 5063, R0, REG)
    gone = sorted(C0)[0]; new_sys = 30100000; added = (S0[5], new_sys)
    C1 = (C0 - {gone}) | {added}
    sde(changed, C1, set(S0) | {new_sys}, J0['build'] + 5100, R0, REG)
    moved = os.path.join(tmp, 'moved'); mv = S0[7]; R2 = dict(R0); R2[mv] = (R0[mv][0] + 3, R0[mv][1] - 2, R0[mv][2], R0[mv][3], R0[mv][4])
    sde(moved, C0, S0, J0['build'] + 5200, R2, REG)
    page = os.path.join(tmp, 'index.html'); shutil.copy(HTML, page); before = open(page, encoding='utf-8').read()
    out_f, sum_f, body = os.path.join(tmp, 'out.txt'), os.path.join(tmp, 'summary.md'), os.path.join(tmp, 'pr.md')

    rc, o = run(page, same, '--write', '--body', body, env={'GITHUB_OUTPUT': out_f, 'GITHUB_STEP_SUMMARY': sum_f})
    outs = open(out_f).read() if os.path.exists(out_f) else ''
    check(rc == 0 and o.strip().splitlines()[-1].startswith('jump table matches') and 'changed=false' in outs and open(page, encoding='utf-8').read() == before and not os.path.exists(body),
          f'the same gates on a newer build: matches, changed=false, the page untouched, no pull request text ({o.strip().splitlines()[-1]!r}; {outs.split()})')
    rc2, _ = run(page, same, '--check')
    check(rc2 == 0, f'--check on the same gates exits 0 ({rc2})')

    rc3, _ = run(page, changed, '--check')
    check(rc3 == 1, f'--check with a gate changed exits 1 ({rc3})')
    open(out_f, 'w').close()
    rc4, o4 = run(page, changed, '--write', '--body', body, env={'GITHUB_OUTPUT': out_f, 'GITHUB_STEP_SUMMARY': sum_f})
    outs = open(out_f).read(); txt = open(body, encoding='utf-8').read() if os.path.exists(body) else ''
    check(rc4 == 0 and 'changed=true' in outs and f'build={J0["build"] + 5100}' in outs, f'a gate changed: changed=true and the build as step outputs {outs.split()}')
    check(f'- added: SYS-{S0[5] - 30000000} – SYS-100000' in txt and f'- removed: SYS-{gone[0] - 30000000} – SYS-{gone[1] - 30000000}' in txt and 'git pull' in txt,
          f"the pull request's text names the connection added and the one removed {txt.splitlines()[2:4]}")
    J1 = table(page); C1r, _ = conns_of(J1)
    check(C1r == C1 and J1['build'] == J0['build'] + 5100 and J1['n'] == len(C1) and J1['systems'] == len({s for c in C1 for s in c}),
          f"the page's table rewritten: exactly the new connections, the new build ({J1['n']} connections, {J1['systems']} systems, build {J1['build']})")
    after = open(page, encoding='utf-8').read()
    strip = lambda s: re.sub(r'^const INTEL_(JUMPS|MAP) = .*;$', '', s, flags=re.M)
    M1 = mtable(page); S1 = conns_of(J1)[1]; R1 = m_rows(M1, S1)
    check(strip(after) == strip(before) and M1['jumps'] == J1['md5'] and M1['systems'] == J1['systems'] and R1[new_sys] == R0.get(new_sys, (0, 0, 50, 0, (0, 0, 0))) and all(R1[s] == R0[s] for s in S0 if s in R1),
          'only INTEL_JUMPS and INTEL_MAP changed in the page; the map re-aligned to the new table (every system keeps its own place)')
    rc5, o5 = run(page, changed, '--check')
    check(rc5 == 0 and 'matches' in o5, f'the rewritten page against the same data: nothing to do ({rc5})')
    # one system moved on CCP's map, no gate changed
    page2 = os.path.join(tmp, 'index2.html'); shutil.copy(HTML, page2)
    rc6, _ = run(page2, moved, '--check')
    open(out_f, 'w').close(); os.path.exists(body) and os.remove(body)
    rc7, o7 = run(page2, moved, '--write', '--body', body, env={'GITHUB_OUTPUT': out_f, 'GITHUB_STEP_SUMMARY': sum_f})
    outs = open(out_f).read(); txt = open(body, encoding='utf-8').read() if os.path.exists(body) else ''
    a2 = open(page2, encoding='utf-8').read(); M2 = mtable(page2); R2r = m_rows(M2, S0)
    check(rc6 == 1 and rc7 == 0 and 'changed=true' in outs and 'map table: 2 value(s) differ' in txt and 'map' in txt.splitlines()[0],
          f'a system moved on the map, no gate changed: --check exits 1, changed=true, the pull request says the map changed ({rc6}, {outs.split()}, {[l for l in txt.splitlines() if "map" in l][:2]})')
    check(re.sub(r'^const INTEL_MAP = .*;$', '', a2, flags=re.M) == re.sub(r'^const INTEL_MAP = .*;$', '', open(HTML, encoding='utf-8').read(), flags=re.M) and R2r == R2,
          'only INTEL_MAP rewritten: that system moved, nothing else')
    rc8, o8 = run(page2, moved, '--check')
    check(rc8 == 0, f'the rewritten page against the same data: nothing to do ({rc8})')
    # v2026.11.04.1: one system moved in space only (its flat-map place unchanged)
    sp = os.path.join(tmp, 'space'); sv = S0[11]; R3 = dict(R0); x3, y3, z3 = R0[sv][4]; R3[sv] = R0[sv][:4] + ((x3 + 17, y3 - 4, z3 + 250),)
    sde(sp, C0, S0, J0['build'] + 5300, R3, REG)
    page3 = os.path.join(tmp, 'index3.html'); shutil.copy(HTML, page3); open(out_f, 'w').close(); os.path.exists(body) and os.remove(body)
    rc9, _ = run(page3, sp, '--check')
    rc10, o10 = run(page3, sp, '--write', '--body', body, env={'GITHUB_OUTPUT': out_f, 'GITHUB_STEP_SUMMARY': sum_f})
    M3 = mtable(page3); R3r = m_rows(M3, S0)
    check(rc9 == 1 and rc10 == 0 and 'map table: 3 value(s) differ' in o10 and R3r == R3 and all(M3[k] == M0[k] for k in ('x', 'y', 'sec', 'reg', 'regions')),
          f'a system moved in space only: --check exits 1, its x, y, z rewritten (3 values), nothing else ({rc9}, {rc10}, {[l for l in o10.splitlines() if "map table" in l][:1]})')
    # a page from before v2026.11.04.1: no positions yet
    page4 = os.path.join(tmp, 'index4.html'); old = dict(M0); old.pop('p3'); old.pop('p3u')
    open(page4, 'w', encoding='utf-8').write(re.sub(r'^const INTEL_MAP = .*;$', lambda m_: 'const INTEL_MAP = ' + json.dumps(old, ensure_ascii=False, separators=(',', ':')) + ';', open(HTML, encoding='utf-8').read(), count=1, flags=re.M))
    rc11, _ = run(page4, same, '--check'); rc12, _ = run(page4, same, '--write'); M4 = mtable(page4)
    check(rc11 == 1 and rc12 == 0 and M4.get('p3') == M0['p3'] and M4.get('p3u') == P3U and all(M4[k] == M0[k] for k in ('x', 'y', 'sec', 'reg', 'regions', 'jumps', 'systems')),
          f'a page without positions: --check exits 1, --write adds them (equal to the page\'s own), nothing else changes ({rc11}, {rc12})')
    # a system with no position in CCP's data: stop, the page untouched
    nop = os.path.join(tmp, 'nopos'); sde(nop, C0, S0, J0['build'] + 5400, R0, REG, nopos={S0[3]})
    page5 = os.path.join(tmp, 'index5.html'); shutil.copy(HTML, page5)
    rc13, o13 = run(page5, nop, '--write')
    check(rc13 != 0 and 'without a position' in o13 and open(page5, encoding='utf-8').read() == open(HTML, encoding='utf-8').read(),
          f'a system without a position in CCP\'s data: the script stops, the page untouched ({rc13})')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print(f'JUMP TABLE UPDATE: {len(problems)} problems')
sys.exit(1 if problems else 0)
