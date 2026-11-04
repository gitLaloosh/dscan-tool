"""The page's list of items changed in EVE's last update and not yet checked against pyfa (GAME_DATA_PENDING, v2026.11.04.3).

    python3 -I tools/check_game_data_pending.py [index.html]     -> '... 0 problems' (exit 1 otherwise)

Build queue 008 (roadmap/game-data-update-plan.md section 3): the list is written only by tools/sde_change_report.py --write
(the workflow's pull request) and emptied by the pyfa update process (PYFA_CORE.md); never by hand. This checks what a hand
edit would get wrong: the line is there once; `types` is base64 of big-endian uint32 type IDs, sorted, no repeats; `build`
and `verified` are whole numbers; a non-empty list names the build it changed in, later than `verified`.
"""
import os, re, sys, json, base64, struct

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HTML = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
src = open(HTML, encoding='utf-8').read()
RX = re.compile(r"^const GAME_DATA_PENDING = \{verified: (\d+), build: (\d+), types: '([A-Za-z0-9+/=]*)'\};", re.M)

def decode(t):
    b = base64.b64decode(t, validate=True)
    if len(b) % 4: raise ValueError(f'{len(b)} bytes: not whole uint32 values')
    return list(struct.unpack('>%dI' % (len(b) // 4), b))

def encode(ids):   # also used by sde_change_report.py --write
    ids = sorted(set(int(i) for i in ids))
    return base64.b64encode(struct.pack('>%dI' % len(ids), *ids)).decode()

def line(verified, build, ids):
    return f"const GAME_DATA_PENDING = {{verified: {int(verified)}, build: {int(build)}, types: '{encode(ids)}'}};"

def main():
    problems = []
    found = RX.findall(src)
    if len(found) != 1:
        problems.append(f'GAME_DATA_PENDING: {len(found)} lines in the form the tools write (want 1)')
        ids = []
    else:
        verified, build, t = int(found[0][0]), int(found[0][1]), found[0][2]
        try: ids = decode(t)
        except Exception as e: problems.append(f"GAME_DATA_PENDING.types doesn't decode: {e}"); ids = []
        if ids != sorted(set(ids)): problems.append('GAME_DATA_PENDING.types is not sorted without repeats (written by hand?)')
        if any(i <= 0 for i in ids): problems.append('GAME_DATA_PENDING.types has a type ID of 0')
        if ids and build <= verified: problems.append(f'GAME_DATA_PENDING: {len(ids)} items but build {build} is not after verified {verified}')
        if ids and encode(ids) != t: problems.append('GAME_DATA_PENDING.types is not in the encoder\'s form')
        mf = os.path.join(os.path.dirname(os.path.abspath(HTML)), 'tools', 'pyfa_core_manifest.json')
        if os.path.exists(mf):
            cb = json.load(open(mf, encoding='utf-8'))['pyfa']['clientBuild']
            if verified != cb: problems.append(f"GAME_DATA_PENDING.verified {verified} is not the manifest's pyfa.clientBuild {cb} (the pyfa update process sets both)")
    print(f'GAME DATA PENDING: {len(ids)} item(s) listed; {len(problems)} problems')
    for p in problems: print('  ' + p)
    return 1 if problems else 0

if __name__ == '__main__':
    sys.exit(main())
