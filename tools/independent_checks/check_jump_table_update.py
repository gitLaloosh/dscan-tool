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
def sde(folder, conns, systems, build):
    os.makedirs(folder, exist_ok=True); L, g = [], 50000000
    for a, c in sorted(conns):
        L.append(json.dumps({'_key': g, 'destination': {'solarSystemID': c, 'stargateID': g + 1}, 'solarSystemID': a, 'typeID': 16}))
        L.append(json.dumps({'_key': g + 1, 'destination': {'solarSystemID': a, 'stargateID': g}, 'solarSystemID': c, 'typeID': 16})); g += 2
    open(os.path.join(folder, 'mapStargates.jsonl'), 'w', encoding='utf-8').write('\r\n'.join(L) + '\r\n')   # CRLF, as CCP's latest.jsonl
    open(os.path.join(folder, 'mapSolarSystems.jsonl'), 'w', encoding='utf-8').write('\n'.join(json.dumps({'_key': s, 'name': {'en': f'SYS-{s - 30000000}'}}) for s in sorted(systems)) + '\n')
    open(os.path.join(folder, 'latest.jsonl'), 'w', encoding='utf-8').write(json.dumps({'_key': 'sde', 'buildNumber': build, 'releaseDate': '2026-10-29T11:10:30Z'}) + '\r\n')
def run(page, folder, *extra, env=None):
    e = dict(os.environ); e.pop('GITHUB_OUTPUT', None); e.pop('GITHUB_STEP_SUMMARY', None); e.update(env or {})
    r = subprocess.run([sys.executable, '-I', SCRIPT, page, '--sde', folder, *extra], capture_output=True, text=True, env=e)
    return r.returncode, r.stdout + r.stderr

J0 = table(HTML); C0, S0 = conns_of(J0)
tmp = tempfile.mkdtemp(prefix='jtu-')
try:
    same, changed = os.path.join(tmp, 'same'), os.path.join(tmp, 'changed')
    sde(same, C0, S0, J0['build'] + 5063)
    gone = sorted(C0)[0]; new_sys = 30100000; added = (S0[5], new_sys)
    C1 = (C0 - {gone}) | {added}
    sde(changed, C1, set(S0) | {new_sys}, J0['build'] + 5100)
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
    check(after.replace(re.search(r'^const INTEL_JUMPS = .*;$', after, re.M).group(0), '') == before.replace(re.search(r'^const INTEL_JUMPS = .*;$', before, re.M).group(0), ''),
          'only INTEL_JUMPS changed in the page')
    rc5, o5 = run(page, changed, '--check')
    check(rc5 == 0 and 'matches' in o5, f'the rewritten page against the same data: nothing to do ({rc5})')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print(f'JUMP TABLE UPDATE: {len(problems)} problems')
sys.exit(1 if problems else 0)
