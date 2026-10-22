"""Pasted names with either kind of apostrophe still resolve (v2026.10.14.29).

    PYFA_SRC=... python3 -I tools/independent_checks/check_apostrophe_names.py [index.html]   -> 'N misses'

CCP's names use both kinds: the October 2026 data (client build 3624425) renamed Sarikusa's / Horm's / Zorya's
officer modules from a curly ’ to a straight ', while e.g. ‘Vigilant’ Shield Command Burst and Tenzin’s Modified
Guidance Disruptor still use curly quotes. index.html's apostropheVariants(name) gives the extra spellings that
resolveNamesToIdsFlexible sends to ESI with the typed one.

For every published SDE name containing ' ‘ or ’ this types it three ways (as CCP spells it, with every quote
straightened, with every straight quote replaced by ’) and requires CCP's spelling to be among the typed string and its
variants. The page function is run as is (extracted from index.html), not retyped.
"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pyfa_sde import types, name

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
names = sorted({name(t) for t, v in types.items() if v.get('published') and name(t) and any(c in name(t) for c in "'‘’")})
js = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const m = src.match(/function apostropheVariants\(n\)\{[\s\S]*?\n\}/);
if(!m){ console.log('apostropheVariants not found in index.html'); process.exit(1); }
const apostropheVariants = new Function(m[0] + '; return apostropheVariants;')();
const names = JSON.parse(fs.readFileSync(0, 'utf8'));
const straighten = s => s.replace(/[‘’]/g, "'");
let bad = 0;
for(const x of names) for(const typed of [x, straighten(x), x.replace(/'/g, '’')]){
  const c = new Set([typed, ...apostropheVariants(typed)]);
  if(!c.has(x)){ bad++; if(bad < 20) console.log(`MISS typed ${JSON.stringify(typed)} -> ${JSON.stringify([...c])}, CCP spells it ${JSON.stringify(x)}`); }
}
console.log(`${bad} misses (${names.length} published names with an apostrophe, 3 spellings each)`);
"""
r = subprocess.run(['node', '-e', js, html], input=json.dumps(names), capture_output=True, text=True)
sys.stdout.write(r.stdout); sys.stderr.write(r.stderr)
sys.exit(r.returncode)
