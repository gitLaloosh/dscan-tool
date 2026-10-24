"""The Weaknesses picks, "your guns" / "their guns" (v2026.10.14.42; roadmap/my-ship-plan.md phase 2b, decisions B1-B4).

    PYFA_SRC=... python3 -I tools/independent_checks/check_weakness_picks.py [index.html] [--mutate NAME]   -> 'N mismatches'

For pairs of constructed fits (my ship, a threat), each carrying spare ammo in cargo and, for the drone boats, more
than one drone type, and a grid of the "Their damage on you" card's settings, compares the tool's own picks
(wpCandidates + wpRank on mysFight, index.html, both fits built from their EFT text by the real engine with ESI
answered from the SDE) with an independent build:
  * the candidates (B1), from the fit as written and pyfa's rule for a charge a weapon can load (eos Module.isValidCharge:
    the charge's group is one of the weapon's chargeGroup1-5, its chargeSize equals the weapon's when the weapon has
    one, and its volume fits the weapon's capacity), restricted to charges that deal damage; the drone types in the bay;
  * for each candidate charge, an oracle fit (tools/pyfa_fit_oracle.py: pyfa's own handlers) with that charge in
    EVERY copy of the weapon; for each drone type, an oracle fit with a flight of that type only (as many as the bay,
    5 drones and the ship's drone bandwidth allow), written again from that rule;
  * then pyfa's calc/projected.py (the attacker's CURRENT fit: its webs, painters and scram) and calc/application.py
    getApplicationPerKey, run unmodified (the harnesses of check_projected.py and check_application.py), at the
    strip's fight (B2): your guns on them at the mirror, their guns on you, exactly as check_matchup.py builds it;
  * the applied DPS of that weapon type's copies (or that drone type) by damage type, summed (the number shown);
  * the order: the strip's time to kill of the whole fit with that swap (the other weapons as loaded and the drones in
    space; a drone pick replaces the drones in space) against the target's resists, layer by layer with its reps while
    its capacitor lasts (check_matchup.ttk, written from P2), then the same against its buffer alone (no reps, no
    regen), then the charge already loaded.
Every candidate's DPS and both times must match (1e-6 relative, or both "holds"), and so must the order shown.
--mutate NAME re-runs the tool with a deliberate mistake, to show what each kind of mistake looks like.
"""
import sys, os, json, math, subprocess, tempfile, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', 'page_checks'))
import check_projected as CP
import check_application as CA
from check_matchup import typed_dps_mod, typed_dps_drone, TYPES, ttk
from pyfa_fit_oracle import OracleFit, resonances
from golden_oracle import td_mode
from pyfa_sde import T, types, td, groups, _en
from refresh_golden_fixtures import sde_type
from eft_engine import BYNAME, group_rec

# name, [(module, charge or None)] in slot order (lows, mids, highs, rigs), [(drone, bay qty)], [(cargo item, qty)]
FITS = {
  'vexor': ('Vexor', [('Damage Control II', None), ('Medium Armor Repairer II', None), ('Multispectrum Energized Membrane II', None), ('Drone Damage Amplifier II', None),
                      ('50MN Microwarpdrive II', None), ('Warp Scrambler II', None), ('Stasis Webifier II', None),
                      ('Heavy Neutron Blaster II', 'Void M'), ('Heavy Neutron Blaster II', 'Void M'), ('Heavy Neutron Blaster II', 'Void M'),
                      ('Medium Auxiliary Nano Pump I', None), ('Medium Auxiliary Nano Pump I', None), ('Medium Nanobot Accelerator I', None)],
            [('Hammerhead II', 5), ('Hobgoblin II', 5), ('Ogre II', 2)], [('Null M', 1000), ('Antimatter Charge M', 1000), ('Caldari Navy Antimatter Charge M', 500)]),
  'hecate': ('Hecate', [('Magnetic Field Stabilizer II', None), ('Magnetic Field Stabilizer II', None), ('Damage Control II', None),
                        ('5MN Microwarpdrive II', None), ('Warp Scrambler II', None), ('Stasis Webifier II', None),
                        ('Light Neutron Blaster II', 'Void S'), ('Light Neutron Blaster II', 'Void S'), ('Light Neutron Blaster II', 'Void S'), ('Light Neutron Blaster II', 'Void S'), ('Light Neutron Blaster II', 'Void S')],
             [], [('Null S', 1000), ('Antimatter Charge S', 500)]),
  'omen': ('Omen', [('Heat Sink II', None), ('Heat Sink II', None), ('Damage Control II', None), ('800mm Steel Plates II', None), ('Multispectrum Energized Membrane II', None),
                    ('10MN Afterburner II', None), ('Warp Scrambler II', None), ('Stasis Webifier II', None),
                    ('Focused Medium Pulse Laser II', 'Scorch M'), ('Focused Medium Pulse Laser II', 'Scorch M'), ('Focused Medium Pulse Laser II', 'Scorch M'), ('Focused Medium Pulse Laser II', 'Scorch M'), ('Focused Medium Pulse Laser II', 'Scorch M')],
           [('Warrior II', 5), ('Acolyte II', 5)], [('Conflagration M', 1), ('Multifrequency M', 1), ('Imperial Navy Multifrequency M', 1)]),
  'caracal': ('Caracal', [('Ballistic Control System II', None), ('Ballistic Control System II', None),
                          ('50MN Microwarpdrive II', None), ('Large Shield Extender II', None), ('Large Shield Extender II', None), ('Warp Disruptor II', None), ('Stasis Webifier II', None),
                          ('Heavy Missile Launcher II', 'Scourge Fury Heavy Missile'), ('Heavy Missile Launcher II', 'Scourge Fury Heavy Missile'), ('Heavy Missile Launcher II', 'Scourge Fury Heavy Missile'),
                          ('Heavy Missile Launcher II', 'Scourge Fury Heavy Missile'), ('Heavy Missile Launcher II', 'Scourge Fury Heavy Missile')],
              [('Hobgoblin II', 5)], [('Scourge Heavy Missile', 1000), ('Inferno Precision Heavy Missile', 1000), ('Mjolnir Heavy Missile', 1000), ('Scourge Heavy Assault Missile', 500)]),
  'rupture': ('Rupture', [('Gyrostabilizer II', None), ('Gyrostabilizer II', None), ('Damage Control II', None), ('800mm Steel Plates II', None),
                          ('10MN Afterburner II', None), ('Warp Scrambler II', None), ('Stasis Webifier II', None),
                          ('220mm Vulcan AutoCannon II', 'Barrage M'), ('220mm Vulcan AutoCannon II', 'Barrage M'), ('220mm Vulcan AutoCannon II', 'Hail M'), ('220mm Vulcan AutoCannon II', None)],
              [('Valkyrie II', 5), ('Warrior II', 5)], [('EMP M', 1000), ('Republic Fleet Phased Plasma M', 1000), ('Barrage S', 1000)]),
  'thrasher': ('Thrasher', [('Gyrostabilizer II', None), ('Gyrostabilizer II', None),
                            ('1MN Afterburner II', None), ('Small Shield Extender II', None),
                            ('280mm Howitzer Artillery II', 'Quake S'), ('280mm Howitzer Artillery II', 'Quake S'), ('280mm Howitzer Artillery II', 'Quake S'),
                            ('280mm Howitzer Artillery II', 'Tremor S'), ('280mm Howitzer Artillery II', 'Tremor S'), ('280mm Howitzer Artillery II', 'Tremor S'), ('280mm Howitzer Artillery II', None)],
               [], [('Republic Fleet EMP S', 1000)]),
  'ishtar': ('Ishtar', [('Drone Damage Amplifier II', None), ('Drone Damage Amplifier II', None), ('Damage Control II', None), ('Omnidirectional Tracking Enhancer II', None),
                        ('10MN Afterburner II', None), ('Large Shield Extender II', None), ('Large Shield Extender II', None), ('Omnidirectional Tracking Link II', None),
                        ('Drone Link Augmentor II', None), ('Drone Link Augmentor II', None)],
             [('Garde II', 5), ('Warden II', 5), ('Curator II', 5), ('Ogre II', 5), ('Hobgoblin II', 5)], []),
  'drake': ('Drake', [('Ballistic Control System II', None), ('Ballistic Control System II', None), ('Damage Control II', None),
                      ('10MN Afterburner II', None), ('Large Shield Extender II', None), ('Large Shield Extender II', None), ('Warp Scrambler II', None), ('Stasis Webifier II', None),
                      ('Heavy Assault Missile Launcher II', 'Scourge Rage Heavy Assault Missile'), ('Heavy Assault Missile Launcher II', 'Scourge Rage Heavy Assault Missile'),
                      ('Heavy Assault Missile Launcher II', 'Scourge Rage Heavy Assault Missile'), ('Heavy Assault Missile Launcher II', 'Scourge Rage Heavy Assault Missile'),
                      ('Heavy Assault Missile Launcher II', 'Scourge Rage Heavy Assault Missile'), ('Heavy Assault Missile Launcher II', 'Scourge Rage Heavy Assault Missile'),
                      ('Sisters Expanded Probe Launcher', 'Core Scanner Probe I')],   # v.43: a probe launcher is not a pick
            [('Hornet II', 5)], [('Scourge Javelin Heavy Assault Missile', 1000), ('Inferno Heavy Assault Missile', 1000), ('Scourge Heavy Missile', 100)]),
}
PAIRS = [('vexor', 'hecate'), ('hecate', 'vexor'), ('omen', 'caracal'), ('caracal', 'rupture'), ('rupture', 'thrasher'), ('thrasher', 'drake'), ('ishtar', 'drake'), ('drake', 'ishtar'), ('ishtar', 'omen')]
GRID = [dict(range=r, mode=mo, speedPct=100, prop=pr, sigPct=100, theirPct=tp, theirMode=tm, axis='distance')
        for r, mo, pr, (tp, tm) in itertools.product([1500, 5000, 12000, 30000, 60000], ['still', 'orbit', 'straight'], [True, False], [(0, 'toward'), (100, 'toward'), (100, 'orbit')])]

def eft(k):
    ship, mods, drones, cargo = FITS[k]
    lines = [f'[{ship}, {k}]'] + [f'{m}, {c}' if c else m for m, c in mods] + ['']
    lines += [f'{d} x{n}' for d, n in drones] + [''] + [f'{c} x{n}' for c, n in cargo]
    return '\n'.join(lines) + '\n'

# the tool: both fits built by the real engine; for every pair and setting, its own picks both ways
NODE = r'''
const fs = require('fs'), vm = require('vm'), readline = require('readline');
const [htmlPath, inPath, outPath] = process.argv.slice(2);
let code = [...fs.readFileSync(htmlPath, 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const {fits, pairs, grid, mutate} = JSON.parse(fs.readFileSync(inPath, 'utf8'));
for (const [a, b] of mutate) { if (!code.includes(a)) throw new Error('mutation text not found: ' + a); code = code.split(a).join(b); }
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
const sb = {fetch: fetchFn, document: {getElementById: fakeEl, createElement: fakeEl, querySelectorAll(){return [];}}, console: {log(){}, warn(){}, error(){}},
  Promise, Map, Set, WeakMap, Infinity, Math, JSON, Object, Array, Number, String, setTimeout, clearTimeout};
vm.createContext(sb); vm.runInContext(code, sb);
(async () => {
  const F = {}, est = {};
  for (const [k, text] of Object.entries(fits)) {
    const {f} = await sb.buildFitFromEft(text);
    F[k] = f;
    est[k] = JSON.parse(JSON.stringify({moduleStates: f.estimate.moduleStates, droneStates: f.estimate.droneStates, projectedTarget: f.estimate.projectedTarget, capacitor: {stable: f.estimate.capacitor.stable, timeToEmptyExactSec: f.estimate.capacitor.timeToEmptyExactSec}}));
  }
  const fin = (x) => x === Infinity ? 'inf' : x;
  const pack = (r) => ({groups: r.groups.map(g => ({w: g.weaponTypeId, qty: g.qty, opts: g.ranked.map(o => [o.chargeTypeId, o.dps, o.loaded, fin(o.ttk), fin(o.ttkBuffer)])})),
    drones: r.drones.map(d => [d.typeId, d.count, d.dps, fin(d.ttk), fin(d.ttkBuffer)])});
  const out = {};
  for (const [m, t] of pairs) {
    const cm = await sb.wpCandidates(F[m]), ct = await sb.wpCandidates(F[t]);
    out[m + '|' + t] = grid.map(st => {
      const X = sb.mysFight(F[t], F[m], st);
      return X && {yours: pack(sb.wpRank(cm, X.mApp, X.them, X.qOut, F[t].estimate)), theirs: pack(sb.wpRank(ct, X.tApp, X.me, X.qIn, F[m].estimate))};
    });
  }
  fs.writeFileSync(outPath, JSON.stringify({out, est})); process.stdout.write('R\n'); process.exit(0);
})().catch(e => { fs.writeFileSync(outPath, JSON.stringify({error: String(e && e.stack || e)})); process.stdout.write('R\n'); process.exit(0); });
'''

def run_tool(html, mutate):
    tmp = tempfile.mkdtemp(); inp = os.path.join(tmp, 'in.json'); js = os.path.join(tmp, 'run.js')
    json.dump({'fits': {k: eft(k) for k in FITS}, 'pairs': PAIRS, 'grid': GRID, 'mutate': mutate}, open(inp, 'w')); open(js, 'w').write(NODE)
    outp = os.path.join(tmp, 'out.json')
    p = subprocess.Popen(['node', js, html, inp, outp], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    for line in p.stdout:
        if line.startswith('R'): p.wait(); return json.load(open(outp))
        q = json.loads(line[2:])
        if 'type' in q: a = sde_type(str(q['type'])) if str(q['type']) in types else None
        elif 'group' in q: a = group_rec(q['group']) if str(q['group']) in groups else None
        else: a = {'inventory_types': [{'id': BYNAME[n], 'name': n} for n in q['names'] if n in BYNAME]}
        p.stdin.write(json.dumps(a) + '\n'); p.stdin.flush()
    raise RuntimeError('engine run ended without a result')

# ---- independent side ----
def A(t): return {a['attributeID']: a['value'] for a in (td.get(str(t)) or {}).get('dogmaAttributes', [])}
CHARGE_GROUP = (604, 605, 606, 609, 610); CHARGE_SIZE = 128; DMG_ATTR = (114, 116, 117, 118)
def valid_charge(w, c):
    """eos/saveddata/module.py Module.isValidCharge, on the SDE (no hull or skill changes chargeSize / chargeGroup)."""
    wv, cv = types[str(w)], types[str(c)]
    if cv.get('volume') is not None and wv.get('capacity') is not None and cv['volume'] > wv['capacity']: return False
    wa, ca = A(w), A(c)
    if (wa.get(CHARGE_SIZE) or 0) > 0 and ca.get(CHARGE_SIZE) != wa[CHARGE_SIZE]: return False
    return any(wa.get(x) and int(wa[x]) == types[str(c)]['groupID'] for x in CHARGE_GROUP)
deals = lambda c: any((A(c).get(x) or 0) > 0 for x in DMG_ATTR)
def oracle(k, states, drones, charge_for=None):
    """pyfa_fit_oracle on fit k with the tool's resolved states; charge_for: {weaponTypeId: chargeTypeId} for every copy."""
    ship, mods, _, _ = FITS[k]
    seen, ml = {}, []
    for m, c in mods:
        tid = int(T(m)); i = seen.get(tid, 0); seen[tid] = i + 1
        st = states.get(str(tid)) or {'active': 0, 'online': 1, 'offline': 0}
        s = 'active' if i < st['active'] else 'online' if i < st['active'] + st['online'] else 'offline'
        ml.append((tid, s, (charge_for or {}).get(tid, int(T(c)) if c else None)))
    sid = int(T(ship))   # the tool's default mode (resolveModeKey): Sharpshooter on a Tactical Destroyer, else the first mode
    return OracleFit(sid, ml, mode=td_mode(sid, 'sharpshooter') or td_mode(sid, 'primary'), drones=drones).calculate()

def flight(k, did, o):
    """a flight of one drone type: as many as the bay, 5 drones and the drone bandwidth allow (written from the rule)."""
    bay = dict((int(T(d)), n) for d, n in FITS[k][2])[did]
    bw = o.ship.get('droneBandwidth')
    each = A(did).get(1272) or 0   # droneBandwidthUsed
    n = min(bay, 5, int(math.floor((bw + 1e-9) / each)) if each > 0 and bw is not None else 5)
    return n

def close(a, b): return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))
def tclose(a, b):
    if a == math.inf or b == math.inf: return a == b
    return close(a, b)

if __name__ == '__main__':
    ROOT = os.path.join(HERE, '..', '..')
    args = [a for a in sys.argv[1:]]
    html = next((a for a in args if not a.startswith('--') and a.endswith('.html')), os.path.join(ROOT, 'index.html'))
    MUT = {
      'cargo_ignored': [("for(const id of cargo){\n      const c = cls.get(id);", "for(const id of []){\n      const c = cls.get(id);")],
      'loaded_stats_for_every_charge': [("const aw = ea.weapons.find(w => w.weaponTypeId === wid && w.ammoTypeId === c);", "const aw = (est.application.weapons.find(w => w.weaponTypeId === wid) && Object.assign({}, est.application.weapons.find(w => w.weaponTypeId === wid), {ammoTypeId: c}));")],
      'drone_flight_unclamped': [("const ad = (ea.drones || []).find(d => d.typeId === dk.typeId);", "const ad0 = (ea.drones || []).find(d => d.typeId === dk.typeId); const ad = ad0 && Object.assign({}, ad0, {typeDps: Object.fromEntries(Object.entries(ad0.typeDps).map(([kk, v]) => [kk, v / ad0.qty * Math.floor(dk.bayQty)])), qty: Math.floor(dk.bayQty)});")],
      'mirror_swapped': [("return X && {yours: pack(sb.wpRank(cm, X.mApp, X.them, X.qOut,", "return X && {yours: pack(sb.wpRank(cm, X.mApp, X.them, X.qIn,")],
      'raw_dps_order': [("const order = (a, b) => cmp(a.ttk, b.ttk) || cmp(a.ttkBuffer, b.ttkBuffer) ||", "const order = (a, b) => (b.dps - a.dps) ||")],
      'rest_of_fit_ignored': [("return Object.assign({}, g, {ranked: sorted(g.options.map(o => score(o, [...others, o.aw], dsAll, pt([o.aw], []))))});", "return Object.assign({}, g, {ranked: sorted(g.options.map(o => score(o, [o.aw], [], pt([o.aw], []))))});")],
    }
    mname = next((args[i + 1] for i, a in enumerate(args) if a == '--mutate'), None)
    mutate = MUT[mname] if mname else []
    # the harness's own line for the mirror mutation is applied to NODE, the rest to the page code

    page_mut = [m for m in mutate if 'sb.wpRank' not in m[0]]
    for a, b in mutate:
        if 'sb.wpRank' in a: NODE = NODE.replace(a, b)
    res = run_tool(html, page_mut)
    if 'error' in res: print('TOOL ERROR', res['error']); print('1 mismatches'); sys.exit(0)
    out, est = res['out'], res['est']
    states = {k: CP.tool_states(est[k]) for k in FITS}
    cache = {}
    def orc(k, prop=None, charge_for=None, drones=None):
        """prop: None = the tool's states; True / False = the prop module active / online (check_matchup.py orc)."""
        key = (k, prop, tuple(sorted((charge_for or {}).items())), tuple(drones) if drones is not None else None)
        if key not in cache:
            st, dr = states[k]
            v = est[k]['projectedTarget']['variants']
            if prop is not None and v.get('propTypeId'):
                tid = str(v['propTypeId']); s0 = st.get(tid) or {'active': 0, 'online': 1, 'offline': 0}
                n = s0['active'] + s0['online'] + s0['offline']
                st = dict(st); st[tid] = (s0 if v['running'] else {'active': 1, 'online': n - 1, 'offline': 0}) if prop else {'active': 0, 'online': n - s0['offline'], 'offline': s0['offline']}
            cache[key] = oracle(k, st, dr if drones is None else list(drones), charge_for)
            o = cache[key]
            if o.errors or o.oracleGaps: raise SystemExit(f'ORACLE {k} {key}: errors {o.errors} gaps {o.oracleGaps}')
        return cache[key]
    # independent candidate lists
    def candidates(k):
        ship, mods, drones, cargo = FITS[k]
        st, _ = states[k]
        wts = []
        for m, c in mods:
            tid = int(T(m))
            if CA.is_weapon(_en(groups[str(types[str(tid)]['groupID'])]['groupName'])) and tid not in wts and (st.get(str(tid)) or {'active': 1})['active'] > 0: wts.append(tid)
        g = {}
        for w in wts:
            loaded = [int(T(c)) for m, c in mods if int(T(m)) == w and c]
            cand = list(dict.fromkeys(loaded + [int(T(c)) for c, _ in cargo if valid_charge(w, int(T(c))) and deals(int(T(c)))]))
            g[w] = (cand, set(loaded))
        dr = [int(T(d)) for d, n in drones]
        return g, dr
    bad, notes, points, opts_checked, flips, nvals, resist_flips = 0, [], 0, 0, 0, 0, 0
    capsec = lambda k: math.inf if est[k]['capacitor'].get('stable') else (est[k]['capacitor'].get('timeToEmptyExactSec') if est[k]['capacitor'].get('timeToEmptyExactSec') is not None else math.inf)
    for m, t in PAIRS:
        gm, dm = candidates(m); gt, dt = candidates(t)
        diffs = []
        for i, st in enumerate(GRID):
            got = out[m + '|' + t][i]; points += 1
            if got is None: diffs.append(f'{st}: no fight'); continue
            me_o = orc(m, bool(st['prop'])); me = CP._Fit(me_o)
            tf_fit = CP._Fit(orc(t)); t_inp = CP.pyfa_inputs(tf_fit)
            m_cur = CP._Fit(orc(m)); m_inp = CP.pyfa_inputs(m_cur)
            my_top = me.getMaxVelocity(); their_top = tf_fit.getMaxVelocity()
            y_frac = 0 if st['mode'] == 'still' else st['speedPct'] / 100; y_ang = 90 if st['mode'] == 'orbit' else 0
            t_frac = st['theirPct'] / 100; t_ang = 90 if st['theirMode'] == 'orbit' else 0
            for side, k, G, D, cur_fit, cur_inp, tgt, sf, ta, asp, aa in (
                    ('yours', m, gm, dm, m_cur, m_inp, tf_fit, t_frac, t_ang, y_frac * my_top, y_ang),
                    ('theirs', t, gt, dt, tf_fit, t_inp, me, y_frac, y_ang, t_frac * their_top, t_ang)):
                speed, sig = CP.pyfa_point(cur_fit, tgt, cur_inp, dict(distance=st['range'], speedFrac=sf, ignoreLockRange=True, ignoreDCR=False, droneMode=1))
                CA.SETTINGS.update(ignoreLockRange=True, ignoreDCR=False, mobileDroneMode=CA.DroneMode(1))
                def typed(o, pick):
                    src = CA._Src(o)
                    am = CA.getApplicationPerKey(src=src, tgt=tgt, atkSpeed=asp, atkAngle=aa, distance=st['range'], tgtSpeed=speed, tgtAngle=ta, tgtSigRadius=sig)
                    s = {kk: 0.0 for kk, _ in TYPES}
                    for mod in src.mods:
                        if pick(mod.m):
                            for kk, v in typed_dps_mod(mod.m).items(): s[kk] += v * am.get(mod, 0)
                    for d in src.drones:
                        if pick(d.d):
                            for kk, v in typed_dps_drone(d.d).items(): s[kk] += v * am.get(d, 0)
                    return s
                applied = lambda o, pick: sum(typed(o, pick).values())
                add = lambda a, b: {kk: a[kk] + b[kk] for kk in a}
                tk = t if side == 'yours' else m   # the target of this side
                def ttks(tsum):
                    # the strip's time to kill (check_matchup.ttk, written from P2) and the buffer alone (no reps, no regen)
                    o = orc(tk); res = resonances(o)
                    tb = 0.0
                    for hp, r in ((o.ship.get('shieldCapacity') or 0, res['shield']), (o.ship.get('armorHP') or 0, res['armor']), (o.ship.get('hp') or 0, res['hull'])):
                        if hp <= 0: continue
                        inc = sum(tsum[kk] * r[kk] for kk, _ in TYPES)
                        if inc <= 0: tb = math.inf; break
                        tb += hp / inc
                    return ttk(o, capsec(tk), tsum), tb
                cur = orc(k)
                fin = lambda x: math.inf if x == 'inf' else x
                g_got = {g['w']: g for g in got[side]['groups']}
                if set(g_got) != set(G): diffs.append(f'{side} {st}: weapon types tool {sorted(g_got)} independent {sorted(G)}'); continue
                rest_drones = typed(cur, lambda dd_: dd_ in cur.drones)
                for w, (cand, loaded) in G.items():
                    exp = []
                    rest = add(typed(cur, lambda mm: mm.item.ID != w and mm in cur.modules), rest_drones)
                    for c in cand:
                        o = orc(k, None, {w: c})
                        own = typed(o, lambda mm: mm.item.ID == w)
                        t1, t2 = ttks(add(rest, own))
                        exp.append([c, sum(own.values()), c in loaded, t1, t2])
                    key = lambda x: (x[3], x[4], not x[2])
                    exp.sort(key=key)
                    tg = g_got[w]['opts']
                    if sorted(x[0] for x in tg) != sorted(x[0] for x in exp): diffs.append(f'{side} {st} {w}: candidates tool {[x[0] for x in tg]} independent {[x[0] for x in exp]}'); continue
                    dd = {x[0]: x for x in exp}
                    for c, dps, ld, t1, t2 in tg:
                        opts_checked += 1; e = dd[c]
                        if not close(dps, e[1]) or bool(ld) != e[2] or not tclose(fin(t1), e[3]) or not tclose(fin(t2), e[4]):
                            diffs.append(f'{side} {st} {w}/{c}: tool {dps} {t1} {t2} loaded {ld} independent {e[1]} {e[3]} {e[4]} loaded {e[2]}')
                    # the order shown; equal keys (within 1e-6) may come in either order
                    order_t = [x[0] for x in tg]; order_e = [x[0] for x in exp]
                    if order_t != order_e and not all(tclose(dd[a][3], dd[b][3]) and tclose(dd[a][4], dd[b][4]) and dd[a][2] == dd[b][2] for a, b in zip(order_t, order_e)): diffs.append(f'{side} {st} {w}: order tool {order_t} independent {order_e}')
                    if exp and loaded and exp[0][0] not in loaded: flips += 1
                    if exp and len(exp) > 1 and sorted(exp, key=lambda x: -x[1])[0][0] != exp[0][0]: resist_flips += 1
                d_got = {d[0]: d for d in got[side]['drones']}
                if set(d_got) != set(D): diffs.append(f'{side} {st}: drone types tool {sorted(d_got)} independent {sorted(D)}'); continue
                rest_mods = typed(cur, lambda mm: mm in cur.modules)
                d_exp = []
                for did in D:
                    n = flight(k, did, orc(k))
                    o = orc(k, None, None, ((did, n),))
                    own = typed(o, lambda dd_: dd_.item.ID == did)
                    t1, t2 = ttks(add(rest_mods, own))
                    d_exp.append((did, n, sum(own.values()), t1, t2))
                    _, cnt, dps, g1, g2 = d_got[did]; opts_checked += 1
                    if cnt != n or not close(dps, sum(own.values())) or not tclose(fin(g1), t1) or not tclose(fin(g2), t2):
                        diffs.append(f'{side} {st} drone {did}: tool x{cnt} {dps} {g1} {g2} independent x{n} {sum(own.values())} {t1} {t2}')
                d_exp.sort(key=lambda x: (x[3], x[4]))
                dt_order = [x[0] for x in got[side]['drones']]
                de = {x[0]: x for x in d_exp}
                if dt_order != [x[0] for x in d_exp] and not all(tclose(de[a][3], de[b][3]) and tclose(de[a][4], de[b][4]) for a, b in zip(dt_order, [x[0] for x in d_exp])):
                    diffs.append(f'{side} {st}: drone order tool {dt_order} independent {[x[0] for x in d_exp]}')
        nvals += len(diffs)
        if diffs: bad += 1; notes.append(f'{m} vs {t}: {len(diffs)} differences, e.g. ' + ' | '.join(diffs[:3]))
    for n in notes[:30]: print(n)
    print(f'{len(PAIRS)} pairs x {len(GRID)} card settings x both sides: {points} points, {opts_checked} candidate DPS values compared, {flips} cases where a carried charge beats the loaded one, {resist_flips} where their resists change the pick from the highest-DPS charge')
    print(f'{bad} mismatches ({nvals} differing values; Weaknesses picks vs pyfa: isValidCharge, an oracle fit per candidate, projected.py + application.py)')
