"""Start-of-work pyfa check (PYFA_CORE.md). Run this BEFORE any calculation work.

    PYFA_SRC=/path/to/Pyfa python3 -I tools/pyfa_update_check.py          # compare versions
    PYFA_SRC=/path/to/Pyfa python3 -I tools/pyfa_update_check.py --run    # + run the whole verification chain

Compares three things:
  manifest  tools/pyfa_core_manifest.json -- the pyfa version, commit and SDE client
            build the PYFA CORE sections were last verified against
  local     the pyfa checkout at PYFA_SRC (version.yml, git HEAD, staticdata metadata)
  remote    github.com/pyfa-org/Pyfa: latest release tag and master HEAD (needs network)
If pyfa moved, update PYFA_SRC (git pull), rerun with --run, explain every change,
then update the manifest's "pyfa" block and fingerprints (check_pyfa_core.mjs --update).

Two different things change:
  * CCP game data (patches). The live page reads ESI, so it sees new values at once,
    but tables generated from pyfa/SDE can go stale (new hulls, new effects). pyfa's
    staticdata client build tracks this.
  * pyfa's own code (handlers, capSim, attribute rules). Only a pyfa update shows it.
Ask the owner for pyfa's Help -> About (version + EVE data version) when comparing screenshots.
"""
import sys, os, json, re, subprocess

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MAN = json.load(open(os.path.join(ROOT, 'tools', 'pyfa_core_manifest.json')))['pyfa']
SRC = os.environ.get('PYFA_SRC')

def sh(cmd, cwd=None, timeout=600):
    try:
        p = subprocess.run(cmd, cwd=cwd or ROOT, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, 'timeout'

local = {}
if SRC and os.path.isdir(SRC):
    try: local['version'] = re.search(r'version:\s*(\S+)', open(os.path.join(SRC, 'version.yml')).read()).group(1)
    except Exception: pass
    local['commit'] = sh('git rev-parse HEAD', cwd=SRC)[1]
    try:
        meta = json.load(open(os.path.join(SRC, 'staticdata', 'phobos', 'metadata.0.json')))
        local['clientBuild'] = next(x['field_value'] for x in meta if x['field_name'] == 'client_build')
    except Exception: pass
remote = {}
rc, out = sh('git ls-remote --tags https://github.com/pyfa-org/Pyfa', timeout=30)
if rc == 0:
    tags = re.findall(r'refs/tags/(v\d+(?:\.\d+)*)$', out, re.M)
    if tags: remote['version'] = sorted(tags, key=lambda v: [int(x) for x in v[1:].split('.')])[-1]
rc, out = sh('git ls-remote https://github.com/pyfa-org/Pyfa HEAD', timeout=30)
if rc == 0 and out: remote['commit'] = out.split()[0]

print(f"{'':10}{'version':10}{'commit':12}client build")
for label, d in (('manifest', MAN), ('local', local), ('remote', remote)):
    print(f"{label:10}{str(d.get('version', '?')):10}{str(d.get('commit', '?'))[:10]:12}{d.get('clientBuild', '-' if label == 'remote' else '?')}")
moved = []
if remote.get('version') and remote['version'] != MAN['version']: moved.append(f"new pyfa release {remote['version']} (verified against {MAN['version']})")
if remote.get('commit') and remote['commit'] != MAN['commit']: moved.append('pyfa master has new commits (check the changelog; data updates land here first)')
if local and local.get('commit') != MAN['commit']: moved.append('local PYFA_SRC is not the verified commit')
if local.get('clientBuild') and local['clientBuild'] != MAN['clientBuild']: moved.append(f"SDE client build {local['clientBuild']} != verified {MAN['clientBuild']}")
if not remote: moved.append('could not reach GitHub -- check pyfa releases by hand')
print('\n' + ('UP TO DATE: pyfa matches the verified version.' if not moved else 'ATTENTION:\n  ' + '\n  '.join(moved)))

if '--run' in sys.argv:
    if not SRC: sys.exit('--run needs PYFA_SRC')
    env = f'PYFA_SRC={SRC} '
    chain = [
        ('PYFA CORE lock', 'node tools/check_pyfa_core.mjs index.html', lambda o: 'match the manifest' in o),
        ('golden-fit data vs SDE', env + 'python3 -I tools/refresh_golden_fixtures.py', lambda o: o.startswith('0 of')),
        ('weapon-range table', env + 'python3 -I tools/gen_weapon_range_table.py index.html', lambda o: 'up to date' in o),
        ('hull damage table', env + 'python3 -I tools/gen_hull_damage_table.py index.html', lambda o: 'up to date' in o),
        ('resist tables', env + 'python3 -I tools/gen_resist_table.py index.html', lambda o: 'up to date' in o),
        ('mode table', env + 'python3 -I tools/gen_mode_table.py index.html', lambda o: 'up to date' in o),
        ('speed tables', env + 'python3 -I tools/gen_speed_table.py index.html', lambda o: 'up to date' in o),
        ('EWAR tables', env + 'python3 -I tools/gen_ewar_table.py index.html', lambda o: 'up to date' in o),
        ('implant / booster tables', env + 'python3 -I tools/gen_implant_table.py index.html', lambda o: 'up to date' in o),
        ('projected tables', env + 'python3 -I tools/gen_projected_table.py index.html', lambda o: 'up to date' in o),   # v2026.10.14.35
        ('module-state tables', env + 'python3 -I tools/gen_module_state_tables.py index.html', lambda o: o.count('matches pyfa + SDE') >= 3),
        ('effect tables audit', 'node tools/dump_effect_tables.mjs index.html > /tmp/_t.json && ' + env + 'python3 -I tools/audit_effect_tables.py /tmp/_t.json',
         lambda o: not re.search(r'MISSING|EXTRA|DIFF', o)),
        ('pyfa capacitor simulation', env + 'node regression_suite/compare_cap_sim.mjs index.html', lambda o: ' 0 mismatches' in o),
        ('regression suite', 'node regression_suite/run_regression.mjs index.html', lambda o: 'ALL PASS' in o),
        ('resists vs pyfa handlers', env + 'python3 -I tools/independent_checks/compare_resists.py index.html', lambda o: o.strip().endswith('fits differ') and o.strip().splitlines()[-1].startswith('0 of')),
        ('missile range vs pyfa', env + 'python3 -I tools/independent_checks/check_missile_range.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),
        ('speed vs pyfa handlers', env + 'python3 -I tools/independent_checks/compare_speed.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),
        ('EWAR vs pyfa handlers', env + 'python3 -I tools/independent_checks/compare_ewar.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),
        ('implants vs pyfa handlers', env + 'python3 -I tools/independent_checks/compare_implants.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),
        ('PANIC flag vs pyfa', env + 'python3 -I tools/independent_checks/check_panic.py', lambda o: o.strip().splitlines()[-1].startswith('0 problems')),
        ('modes vs pyfa handlers', env + 'python3 -I tools/independent_checks/compare_modes.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),
        ('every golden fit vs pyfa handlers', env + 'python3 -I tools/independent_checks/compare_fit_stats.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),
        ('display rounding vs Python round', 'node tools/check_py_round.mjs index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),
        ('damage application vs pyfa getApplicationPerKey', env + 'python3 -I tools/independent_checks/check_application.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),  # v2026.10.14.34
        ('projected webs / painters / scram vs pyfa', env + 'python3 -I tools/independent_checks/check_projected.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),  # v2026.10.14.35
        ('damage chart vs pyfa', env + 'python3 -I tools/independent_checks/check_damage_chart.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),  # v2026.10.14.36
        ('matchup strip vs pyfa', env + 'python3 -I tools/independent_checks/check_matchup.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),  # v2026.10.14.41
        ('Weaknesses picks vs pyfa', env + 'python3 -I tools/independent_checks/check_weakness_picks.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),  # v2026.10.14.42
        ('class presets (damage chart)', env + 'python3 -I tools/select_class_presets.py --check index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),  # v2026.10.14.36
        ('missile application skills + ranking', env + 'python3 -I tools/independent_checks/check_missile_application.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),
        ('drone recommendation rule', env + 'python3 -I tools/independent_checks/check_drone_recommendation.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 mismatches')),
        ('error codes registry and ERRORS.md', 'python3 -I tools/gen_errors_md.py index.html', lambda o: o.strip().splitlines()[-1].endswith('ERRORS.md is up to date')),
        ('card names from one list', 'python3 -I tools/check_card_names.py index.html', lambda o: o.strip().splitlines()[-1].endswith(' 0 problems')),  # v2026.10.14.45
        ('subtext rule (info panels, one-line context)', 'python3 -I tools/check_subtext.py index.html', lambda o: o.strip().splitlines()[-1].endswith(' 0 problems')),  # v2026.10.14.48
        ('pasted names, either apostrophe', env + 'python3 -I tools/independent_checks/check_apostrophe_names.py index.html', lambda o: o.strip().splitlines()[-1].startswith('0 misses')),
    ]
    bad = 0
    for name, cmd, good in chain:
        rc, out = sh(cmd)
        ok = rc == 0 and good(out)
        bad += not ok
        last = out.strip().splitlines()[-1] if out.strip() else ''
        print(f"  {'OK  ' if ok else 'FAIL'} {name}: {last[:110]}")
    # Firepower (hand-tables Phase 1, v2026.10.14.3): the hand fallback must only list hulls without pyfa damage effects.
    FP = 'SHIP_ROLE_BONUS,MODULE_DAMAGE_GROUP_CATEGORY,TURRET_SPECIALIZATION_SKILL_IDS,MISSILE_SPECIALIZATION_SKILL_IDS,DRONE_SIZE_CLASS_SKILL_IDS,DRONE_RACIAL_SPECIALIZATION_SKILL_IDS,SHIP_DRONE_CONTROL_RANGE_BONUS,SHIP_DRONE_CONTROL_RANGE_PENALTY_MULT'
    rc, out = sh(f'node tools/dump_effect_tables.mjs index.html {FP} > /tmp/_fp.json && ' + env + 'python3 -I tools/audit_firepower.py /tmp/_fp.json')
    ok = rc == 0 and 'should be 0): 0' in out
    bad += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} firepower fallback audit: {(out.splitlines() or [''])[0][:110]}")
    sys.exit(1 if bad else 0)
