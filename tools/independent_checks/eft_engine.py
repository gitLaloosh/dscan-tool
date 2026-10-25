"""Run EFT fits through the tool's real engine (index.html's buildFitFromEft) in Node, ESI answered from the SDE
(v2026.10.14.36). Network-free; the same records the page checks serve (tools/page_checks/esi_from_sde.py).

    from eft_engine import run_efts
    res = run_efts('index.html', {'a': '[Navitas, x]\\n\\n5MN Microwarpdrive II'}, fields=['projectedTarget', 'speed'])
    res['a']['speed']

Every type the fits name (and every type and group the engine then asks for) is answered from the SDE through a
local request loop: Node asks, Python answers, until the engine finishes.
"""
import os, sys, json, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', 'page_checks'))
from refresh_golden_fixtures import sde_type
from pyfa_sde import types, groups, _en

BYNAME = {}
for k, v in types.items(): BYNAME.setdefault(_en(v.get('typeName') or v.get('name')), int(k))
def group_rec(g):
    gr = groups[str(g)]
    return {'group_id': int(g), 'name': _en(gr['groupName']), 'category_id': gr['categoryID'], 'published': True, 'types': []}

NODE = r'''
const fs = require('fs'), vm = require('vm'), readline = require('readline');
const [htmlPath, inPath] = process.argv.slice(2);
const code = [...fs.readFileSync(htmlPath, 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const rl = readline.createInterface({input: process.stdin});
const waiting = [];
rl.on('line', (l) => { const w = waiting.shift(); w(JSON.parse(l)); });
const ask = (q) => new Promise((res) => { waiting.push(res); process.stdout.write('Q ' + JSON.stringify(q) + '\n'); });
const fakeEl = () => ({addEventListener(){}, get style(){return {};}, querySelectorAll(){return [];}, appendChild(){}, innerHTML: ''});
const fetchFn = async (url, opts) => {
  const t = url.match(/\/universe\/types\/(\d+)\//), g = url.match(/\/universe\/groups\/(\d+)\//);
  let r;
  if (t) r = await ask({type: Number(t[1])});
  else if (g) r = await ask({group: Number(g[1])});
  else if (url.includes('/universe/ids/')) r = await ask({names: JSON.parse(opts.body)});
  else r = null;
  return r ? {ok: true, status: 200, json: async () => r} : {ok: false, status: 404, json: async () => ({})};
};
const sb = {fetch: fetchFn, document: {getElementById: fakeEl, createElement: fakeEl}, console: {log(){}, warn(){}, error(){}},
  Promise, Map, Set, Infinity, Math, JSON, Object, Array, Number, String, setTimeout, clearTimeout};
vm.createContext(sb); vm.runInContext(code, sb);
(async () => {
  const {fits, fields} = JSON.parse(fs.readFileSync(inPath, 'utf8'));
  const out = {};
  for (const [k, text] of Object.entries(fits)) {
    // v2026.10.14.61: a key starting "km:" runs the fit as a killmail would (no {fitSource: 'eft'}: charges not seen are assumed)
    try { let e;
      if (k.startsWith('km:')) { const p = await sb.parseEftFit(text); e = JSON.parse(JSON.stringify(await sb.estimateHpAndDps(p.shipTypeId, p.tally, p.cargoItemIds, p.highSlotByFlag, 'sharpshooter', p.midSlotByFlag))); }
      else { const {f} = await sb.buildFitFromEft(text); e = JSON.parse(JSON.stringify(f.estimate)); }
      out[k] = fields ? Object.fromEntries(fields.map(x => [x, e[x]])) : e; }
    catch (e) { out[k] = {error: String(e && e.message || e)}; }
  }
  // v2026.10.14.61: exit only once the result is written. A pipe write is asynchronous in Node, and process.exit() right
  // after it cut the line at 64 KB once the check ran more fits (JSONDecodeError "Unterminated string").
  process.stdout.write('R ' + JSON.stringify(out) + '\n', () => process.exit(0));
})();
'''

def run_efts(html, fits, fields=None):
    tmp = tempfile.mkdtemp(); inp = os.path.join(tmp, 'in.json'); js = os.path.join(tmp, 'run.js')
    json.dump({'fits': fits, 'fields': fields}, open(inp, 'w')); open(js, 'w').write(NODE)
    p = subprocess.Popen(['node', js, html, inp], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    for line in p.stdout:
        if line.startswith('R '): p.wait(); return json.loads(line[2:])
        q = json.loads(line[2:])
        if 'type' in q: a = sde_type(str(q['type'])) if str(q['type']) in types else None
        elif 'group' in q: a = group_rec(q['group']) if str(q['group']) in groups else None
        else: a = {'inventory_types': [{'id': BYNAME[n], 'name': n} for n in q['names'] if n in BYNAME]}
        p.stdin.write(json.dumps(a) + '\n'); p.stdin.flush()
    raise RuntimeError('engine run ended without a result')

if __name__ == '__main__':
    print(json.dumps(run_efts(sys.argv[1], {'t': open(sys.argv[2]).read()}, sys.argv[3].split(',') if len(sys.argv) > 3 else None))[:3000])
