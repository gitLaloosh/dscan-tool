"""Every golden fit: the tool's unrounded resonances vs pyfa's own handlers (pyfa_fit_oracle).
    PYFA_SRC=... python3 -I tools/independent_checks/compare_resists.py [index.html]
Prints each fit that differs by more than 1e-9 and ends with 'N of M fits differ' (must be 0).
Module states: the tool's documented defaults (golden_oracle.py). v2026.10.14.5."""
import sys, os, json, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from golden_oracle import oracle_for, resonances, GOLDEN
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
html = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'index.html')
tmp = os.path.join(tempfile.mkdtemp(), 'reso.json')
subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, tmp, 'resonance'], check=True, stdout=subprocess.DEVNULL)
tool = json.load(open(tmp)); G = json.load(open(GOLDEN)); bad = 0
for k in G:
    t = (tool.get(k) or {}).get('resonance')
    if not t: print('NO TOOL RESULT', k, tool.get(k)); bad += 1; continue
    r = resonances(oracle_for(k))
    diffs = [f'{l}.{d} pyfa {(1 - r[l][d]) * 100:.3f}% tool {(1 - t[l][d]) * 100:.3f}%' for l in r for d in r[l] if abs(r[l][d] - t[l][d]) > 1e-9]
    if diffs: bad += 1; print(k, '\n    ' + '; '.join(diffs))
print(f'{bad} of {len(G)} fits differ')
