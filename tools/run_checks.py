"""Run the checks a change needs, not all of them every time (v2026.10.30.2; the owner: "yep, do it").

    PYFA_SRC=/path/to/pyfa python3 -I tools/run_checks.py --tier fast                    # the quick lints (seconds)
    PYFA_SRC=/path/to/pyfa python3 -I tools/run_checks.py --tier area --area intel,layout  # + the page checks of those areas
    PYFA_SRC=/path/to/pyfa python3 -I tools/run_checks.py --tier calc [--area fit]          # + the pyfa chain + the calc page checks
    PYFA_SRC=/path/to/pyfa python3 -I tools/run_checks.py --tier all                     # everything
    python3 -I tools/run_checks.py --list            # the areas and their page checks
    python3 -I tools/run_checks.py --check-tags      # every page check has an area (a chain step)
    add --ledger to append the run to tools/check_ledger.md; --jobs N (default 6); an index.html path to check another copy

Which tier (CLAUDE.md "Checks"): a calculation change -> calc (+ the areas that show it); page or Intel work -> area with the
areas touched (add `layout` when shared CSS changed); before a release, after a pyfa update, or every 5th delivery -> all.
The fast lints always run. A page check that fails is run again on its own once: passing then, it is reported as flaky
(timing under load), not as a pass. Ends with "RUN CHECKS: N failed" (0 to deliver).
"""
import sys, os, re, time, subprocess, datetime
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
PC = os.path.join(ROOT, 'tools', 'page_checks')

# Each page check and the areas whose changes it guards. A new page check must be added here (--check-tags fails otherwise).
AREAS = {
    'affiliation_check': ['pilot'], 'assumed_charge_check': ['fit', 'calc'], 'busy_check': ['pilot'],
    'card_width_check': ['layout'], 'charges_check': ['fit', 'calc'], 'damage_chart_check': ['myship', 'calc'],
    'dossier_check': ['pilot'], 'dossier_kills_check': ['pilot'], 'extension_check': ['pilot', 'extension'],
    'fight_strip_check': ['myship', 'calc'], 'fighter_application_check': ['fit', 'calc'], 'fighter_bay_check': ['fit', 'calc'],
    'fighter_bombs_check': ['fit', 'calc'], 'fighter_picks_check': ['myship', 'calc'], 'fighter_tile_check': ['myship', 'calc'],
    'fleet_kill_check': ['pilot', 'system'], 'fleet_view_check': ['system'], 'header_check': ['layout', 'intel'],
    'intel_assess_check': ['intel', 'system'], 'intel_check': ['intel'], 'intel_kills_check': ['intel'], 'intel_layout_check': ['intel'],
    'intel_place_check': ['intel'], 'intel_words_check': ['intel'], 'intel_guard_check': ['intel'], 'intel_fleet_check': ['intel', 'pilot'], 'outside_links_check': ['pilot', 'intel', 'layout'], 'fleet_vs_check': ['pilot', 'system', 'myship'], 'last_kill_check': ['pilot'], 'layout_check': ['layout'], 'matchup_strip_check': ['myship', 'calc'],
    'mine_damage_check': ['myship', 'calc'], 'missile_picks_check': ['myship', 'calc'], 'missing_charges_check': ['fit', 'calc'],
    'module_charges_check': ['fit', 'calc'], 'my_ship_check': ['myship'], 'my_ships_check': ['myship'], 'no_shift_check': ['layout'],
    'pilot_rows_check': ['system'], 'request_gates_check': ['intel', 'pilot'], 'ring_track_check': ['fit'], 'sa_size_check': ['system'],
    'scan_contacts_check': ['system'], 'shared_kill_check': ['pilot'], 'ship_class_check': ['fit', 'system'],
    'support_fighters_check': ['fit', 'calc'], 'system_analyzer_check': ['system'], 'ttk_why_check': ['myship', 'calc'],
    'ui_rules_check': ['layout'], 'unload_check': ['fit'], 'vs_check': ['system', 'myship'], 'weakness_picks_check': ['myship', 'calc'],
    'zkb_outage_check': ['pilot'],
}
NAMES = sorted({a for v in AREAS.values() for a in v})

def fast(html):
    q = lambda f: f'python3 -I tools/{f} {html}'
    return [   # (label, command, pass test on the last line); the same commands as the chain's steps
        ('every page check has an area', 'python3 -I tools/run_checks.py --check-tags', lambda l: l.endswith(' 0 problems')),
        ('personal data (LESSON #90)', 'python3 -I tools/check_pii.py .', lambda l: bool(re.search(r' 0 problems($|[;( ])', l))),
        ('UI rules', q('check_ui_rules.py'), lambda l: l.endswith(' 0 problems')),
        ('subtext rule', q('check_subtext.py'), lambda l: l.endswith(' 0 problems')),
        ('card names', q('check_card_names.py'), lambda l: l.endswith(' 0 problems')),
        ('zKillboard request gates', q('check_request_gates.py'), lambda l: l.endswith(' 0 problems')),
        ('error codes and ERRORS.md', q('gen_errors_md.py'), lambda l: l.endswith('ERRORS.md is up to date')),
        ('LESSONS index', 'python3 -I tools/check_lessons_index.py', lambda l: l.endswith(' 0 problems')),
    ]

def sh(cmd, timeout):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True, timeout=timeout)
        out = (p.stderr.strip() + '\n' + p.stdout.strip()).strip()   # stdout last: a warning on stderr can't hide the result line
    except subprocess.TimeoutExpired:
        out = f'TIMEOUT after {timeout} s'
    return out, time.time() - t0

def last(out): return (out.splitlines() or [''])[-1].strip()

def check_tags():
    files = {f[:-3] for f in os.listdir(PC) if f.endswith('_check.py')}
    problems = [f'{f}.py: no area in AREAS (tools/run_checks.py)' for f in sorted(files - AREAS.keys())]
    problems += [f'{f}: in AREAS but tools/page_checks/{f}.py is gone' for f in sorted(AREAS.keys() - files)]
    for p in problems: print('PROBLEM', p)
    print(f'PAGE CHECK AREAS: {len(files)} page checks, {len(NAMES)} areas ({", ".join(NAMES)}); {len(problems)} problems')
    return 1 if problems else 0

def version(html):
    m = re.search(r'class="build-tag"[^>]*>(v[\d.]+)<', open(os.path.join(ROOT, html), encoding='utf-8').read())
    return m.group(1) if m else '?'

def main(argv):
    if '--check-tags' in argv: return check_tags()
    if '--list' in argv:
        for a in NAMES: print(f'{a}: ' + ', '.join(k for k, v in sorted(AREAS.items()) if a in v))
        return 0
    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default
    tier = opt('--tier', 'fast')
    areas = [a for a in (opt('--area', '') or '').split(',') if a]
    jobs = int(opt('--jobs', '6'))
    skip = {opt(x) for x in ('--tier', '--area', '--jobs')}
    html = next((a for a in argv if not a.startswith('--') and a not in skip), 'index.html')
    bad = [a for a in areas if a not in NAMES]
    if tier not in ('fast', 'area', 'calc', 'all') or bad or (tier == 'area' and not areas):
        print(f'usage: --tier fast|area|calc|all, --area one or more of {",".join(NAMES)} (needed with --tier area)'); return 2
    t0 = time.time(); failed, flaky, lines = [], [], []
    for label, cmd, ok in fast(html):
        out, dt = sh(cmd, 600); good = ok(last(out))
        lines.append(f'{"OK  " if good else "FAIL"} {label} ({dt:.0f} s): {last(out)[:160]}')
        if not good: failed.append(label)
    if tier in ('calc', 'all'):
        out, dt = sh(f'python3 -I tools/pyfa_update_check.py --run', 3600)
        bad_steps = [l for l in out.splitlines() if l.strip().startswith('FAIL')]
        good = 'UP TO DATE' in out and not bad_steps and ' OK ' in out
        lines.append(f'{"OK  " if good else "FAIL"} the pyfa chain ({dt / 60:.0f} min): {len(bad_steps)} steps failed')
        lines += ['     ' + l.strip()[:200] for l in bad_steps]
        if not good: failed.append('pyfa chain')
    want = sorted(AREAS) if tier == 'all' else sorted(k for k, v in AREAS.items() if set(v) & (set(areas) | ({'calc'} if tier == 'calc' else set())))
    env = '' if os.environ.get('PYFA_SRC') else '(PYFA_SRC not set: page checks that need pyfa will fail) '
    def run(name): out, dt = sh(f'python3 -I tools/page_checks/{name}.py {html}', 900); return name, out, dt
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as ex: res = list(ex.map(run, want))
    for name, out, dt in res:
        if last(out) == 'FAILURES: 0': lines.append(f'OK   {name} ({dt:.0f} s)'); continue
        out2, dt2 = sh(f'python3 -I tools/page_checks/{name}.py {html}', 900)   # once more, on its own
        if last(out2) == 'FAILURES: 0':
            flaky.append(name); lines.append(f'FLKY {name}: {last(out)} under load, passed alone ({dt2:.0f} s)')
            lines += ['     ' + l[:200] for l in out.splitlines() if l.startswith('FAIL ')][:3]
        else:
            failed.append(name); lines.append(f'FAIL {name}: {last(out2)}')
            lines += ['     ' + l[:200] for l in out2.splitlines() if l.startswith('FAIL ') or 'Error' in l][:6]
    mins = (time.time() - t0) / 60
    for l in lines: print(l)
    run_desc = tier + (f' ({",".join(areas)})' if areas else '')
    print(f'{env}{version(html)}, tier {run_desc}: {len(fast(html))} lints{" + the pyfa chain" if tier in ("calc", "all") else ""} + {len(want)} page checks in {mins:.0f} min; {len(flaky)} flaky')
    if '--ledger' in argv:
        led = os.path.join(ROOT, 'tools', 'check_ledger.md')
        row = (f'| {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d} | {version(html)} | {run_desc} | {len(want)} | {mins:.0f} | '
               f'{", ".join(failed) or "none"} | {", ".join(flaky) or "none"} | (fill in) |\n')
        with open(led, 'a', encoding='utf-8') as f: f.write(row)
        print(f'ledger: appended to tools/check_ledger.md; fill in "Caught" before delivering')
    print(f'RUN CHECKS: {len(failed)} failed' + (f' ({", ".join(failed)})' if failed else ''))
    return 1 if failed else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
