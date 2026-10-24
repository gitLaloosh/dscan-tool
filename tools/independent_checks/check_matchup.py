"""The My Ship matchup strip (v2026.10.14.41; roadmap/my-ship-plan.md phase 2a, decisions P2 and P4).

    PYFA_SRC=... python3 -I tools/independent_checks/check_matchup.py [index.html]   -> 'N mismatches'

For pairs of golden fits (a threat and "my ship") and a grid of the "Their damage on you" card's settings, compares
the tool's own strip function (mysMatchup, index.html) with an independent build of every number:
  * their DPS on you and your DPS on them, BY DAMAGE TYPE: pyfa's calc/projected.py (their tackle on you, yours on
    them) then calc/application.py getApplicationPerKey per module and drone, each multiplier times that item's own
    pyfa damage by type (charge / drone damage attributes x damageMultiplier x spool / cycle), run unmodified on
    oracle fits (the harnesses of check_projected.py and check_application.py, imported); the mirror as decided
    (P4): your speed as the attacker's, theirs as the target's;
  * your and their top speeds (pyfa's maxVelocity for the states used);
  * "You last" / "They last": the time-to-kill rule written again here from its description (P2), on pyfa's HP,
    resonances and local repair rates (oracle; pairs whose repairs aren't a plain amount / duration are left out
    as targets) and the tool's capacitor time to empty (pyfa's capacitor simulation, checked by
    regression_suite/compare_cap_sim.mjs).
Tolerance 1e-6 relative (times: 1e-6 relative or both infinite).
"""
import sys, os, re, json, math, subprocess, tempfile, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import check_projected as CP
import check_application as CA
from golden_oracle import oracle_for, GOLDEN
from pyfa_fit_oracle import resonances
from compare_implants import _mult, DMG as DMG_ATTRS

TYPES = (('em', 'emDamage'), ('therm', 'thermalDamage'), ('kin', 'kineticDamage'), ('exp', 'explosiveDamage'))
NODE = r'''
const fs = require('fs'), vm = require('vm');
const [htmlPath, inPath, outPath] = process.argv.slice(2);
const code = [...fs.readFileSync(htmlPath, 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const fakeEl = () => ({addEventListener(){}, get style(){return {};}, querySelectorAll(){return [];}, appendChild(){}, innerHTML: ''});
const sb = {fetch: async () => ({ok: false, status: 404}), document: {getElementById: fakeEl, createElement: fakeEl, querySelectorAll(){return [];}},
  console: {log(){}, warn(){}, error(){}}, Promise, Map, Set, Infinity, Math, JSON, Object, Array, Number, String};
vm.createContext(sb); vm.runInContext(code, sb);
const {fits, pairs, grid} = JSON.parse(fs.readFileSync(inPath, 'utf8'));
const out = {};
const fin = (x) => x === Infinity ? 'inf' : x;
for (const [t, m] of pairs) out[t + '|' + m] = grid.map(st => {
  const r = sb.mysMatchup({estimate: fits[t]}, {estimate: fits[m]}, st);
  return r && [r.theirDps, r.yourDps, fin(r.youLast), fin(r.theyLast), r.myTop, r.theirTop, r.keep.you.ok, r.keep.them.ok];
});
fs.writeFileSync(outPath, JSON.stringify(out));
'''
GRID = [dict(range=r, mode=mo, speedPct=sp, prop=pr, sigPct=100, theirPct=tp, theirMode=tm, axis='distance')
        for r, mo, sp, pr, tp, tm in itertools.product([2000, 7500, 15000, 30000], ['still', 'orbit', 'straight'], [100, 50], [True, False], [0, 100], ['toward', 'orbit', 'still'])]   # v.51: their Stopped
# v2026.10.14.53 (F2): Keep at Range for either ship, against every movement of the other one (and both keeping)
GRID += [dict(range=r, mode=mo, speedPct=sp, prop=pr, sigPct=100, theirPct=tp, theirMode=tm, axis='distance')
         for r, (mo, tm), sp, pr, tp in itertools.product([2000, 7500, 15000, 30000],
             [('keep', x) for x in ('toward', 'orbit', 'still', 'keep')] + [(x, 'keep') for x in ('straight', 'orbit', 'still')], [100, 60], [True, False], [100, 40])]

def keep_rule(st, my_top, their_top, their_reach, my_reach):
    """Keep at Range, written again from turret-application-plan.md "Keep at Range in pyfa's inputs": the keeper moves
    straight away (180 deg) at the other ship's closing speed (its speed when it approaches, else 0), capped at its own
    top speed; it can't hold inside the other's scram or web range or when the other closes faster than its top.
    Returns (your speed, your angle, their speed, their angle, you can hold, they can hold)."""
    y_close = st['speedPct'] / 100 * my_top if st['mode'] == 'straight' else 0.0
    t_close = st['theirPct'] / 100 * their_top if st['theirMode'] == 'toward' else 0.0
    ang = {'still': 0, 'straight': 0, 'toward': 0, 'orbit': 90, 'keep': 180}
    def spd(mode, pct, top, other_close):
        if mode == 'still': return 0.0
        if mode == 'keep': return min(other_close, top)
        return pct / 100 * top
    y = spd(st['mode'], st['speedPct'], my_top, t_close); t = spd(st['theirMode'], st['theirPct'], their_top, y_close)
    holds = lambda reach, close, top: not any(x > 0 and st['range'] <= x for x in reach) and close <= top + 1e-9
    return y, ang[st['mode']], t, ang[st['theirMode']], holds(their_reach, t_close, my_top), holds(my_reach, y_close, their_top)
def reach(k):
    """scram range and furthest web (modules, web drones): the tool's projected data, itself checked against pyfa by check_projected.py"""
    pr = (tool[k].get('application') or {}).get('projected') or {}
    webs = [w.get('optimal') or 0 for w in (pr.get('webMods') or []) + (pr.get('webDrones') or [])]
    return (pr.get('scramRange') or 0, max(webs) if webs else 0)

def close(a, b):
    if a == 'inf' or b == math.inf or a == math.inf or b == 'inf': return (a in ('inf', math.inf)) and (b in ('inf', math.inf))
    if a is None or b is None: return a == b
    return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))

def typed_dps_mod(m):
    cyc = max(m.get('speed') or 0, m.get('duration') or 0) / 1000
    if not cyc: return {}
    g = m.item.group.name
    if m.charge is not None and CA.is_weapon(g):
        spool = (m.get('damageMultiplierBonusMax') or 0) if (m.get('damageMultiplierBonusPerCycle') or 0) else 0
        return {k: (m.charge.get(a) or 0) * _mult(m) * (1 + spool) / cyc for k, a in TYPES}
    if g == 'Smart Bomb': return {k: (m.get(a) or 0) / cyc for k, a in TYPES}
    return {}
def typed_dps_drone(d):
    cyc = (d.get('speed') or d.get('duration') or 0) / 1000
    return {k: (d.get(a) or 0) * _mult(d) * d.amountActive / cyc for k, a in TYPES} if cyc else {}

def pyfa_typed(src_fit, src_app, inp, tgt, distance, speedFrac, tgtAngle, atkSpeed, atkAngle):
    speed, sig = CP.pyfa_point(src_fit, tgt, inp, dict(distance=distance, speedFrac=speedFrac, ignoreLockRange=True, ignoreDCR=False, droneMode=1))
    CA.SETTINGS.update(ignoreLockRange=True, ignoreDCR=False, mobileDroneMode=CA.DroneMode(1))
    am = CA.getApplicationPerKey(src=src_app, tgt=tgt, atkSpeed=atkSpeed, atkAngle=atkAngle, distance=distance, tgtSpeed=speed, tgtAngle=tgtAngle, tgtSigRadius=sig)
    typed = {k: 0.0 for k, _ in TYPES}
    for mod in src_app.mods:
        for k, v in typed_dps_mod(mod.m).items(): typed[k] += v * am.get(mod, 0)
    for d in src_app.drones:
        for k, v in typed_dps_drone(d.d).items(): typed[k] += v * am.get(d, 0)
    return typed

def ttk(o, cap_sec, typed):
    """P2, written again from its description: layer by layer, reps while the capacitor lasts, passive shield regen always."""
    sh = o.ship.get; res = resonances(o)
    rep_s = sum(m.get('shieldBonus') / (m.get('duration') / 1000) for m in o.modules if m.state >= 2 and 4 in m.item.effectIds)
    rep_a = sum(m.get('armorDamageAmount') / (m.get('duration') / 1000) for m in o.modules if m.state >= 2 and 27 in m.item.effectIds)
    rep_h = sum(m.get('structureDamageAmount') / (m.get('duration') / 1000) for m in o.modules if m.state >= 2 and 26 in m.item.effectIds)
    shield = sh('shieldCapacity') or 0; tau = (sh('shieldRechargeRate') or 0) / 1000
    layers = [(shield, res['shield'], rep_s, 2.5 * shield / tau if shield > 0 and tau > 0 else 0), (sh('armorHP') or 0, res['armor'], rep_a, 0), (sh('hp') or 0, res['hull'], rep_h, 0)]
    t = 0.0
    for hp, r, rep, passive in layers:
        if hp <= 0: continue
        incoming = sum(typed[k] * r[k] for k, _ in TYPES)
        # time to empty this layer at net rate, the rate changing once when the capacitor runs out
        if t < cap_sec:
            net = incoming - rep - passive
            if net > 0 and hp / net <= cap_sec - t: t += hp / net; continue
            if cap_sec == math.inf: return math.inf
            hp = hp - max(0.0, net) * (cap_sec - t); t = cap_sec
        net2 = incoming - passive
        if net2 <= 0: return math.inf
        t += hp / net2
    return t

SIMPLE_REPS = lambda o: not any(m.item.group.name in ('Shield Boost Amplifier', 'Siege Module', 'Ancillary Shield Booster', 'Ancillary Armor Repairer') or {4936, 5275} & set(m.item.effectIds) for m in o.modules if m.state >= 1)

if __name__ == '__main__':
    ROOT = os.path.join(HERE, '..', '..')
    html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
    G = json.load(open(GOLDEN))
    tmp = tempfile.mkdtemp(); dump = os.path.join(tmp, 'd.json')
    FIELDS = 'application,projectedTarget,moduleStates,droneStates,exact,resonance,capacitor,speed'
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, dump, FIELDS, '-', ','.join(G)], check=True, stdout=subprocess.DEVNULL)
    tool = json.load(open(dump))
    def ok_fit(k):
        t = tool[k]
        return t.get('projectedTarget') and (t.get('application') or {}).get('weapons') is not None
    oracles = {}
    def orc(k, prop=None):
        """oracle with the tool's states; prop: None = as resolved, True / False = the prop module active / online."""
        key = (k, prop)
        if key not in oracles:
            states, drones = CP.tool_states(tool[k])
            v = tool[k]['projectedTarget']['variants']
            if prop is not None and v.get('propTypeId'):
                tid = str(v['propTypeId']); st = states.get(tid) or {'active': 0, 'online': 1, 'offline': 0}
                n = st['active'] + st['online'] + st['offline']
                states = dict(states); states[tid] = (st if v['running'] else {'active': 1, 'online': n - 1, 'offline': 0}) if prop else {'active': 0, 'online': n - st['offline'], 'offline': st['offline']}
            oracles[key] = oracle_for(k, states=states, drones=drones, group_limits=False)
        return oracles[key]
    cands = [k for k in G if ok_fit(k)]
    # my ships: armor / shield reps with the capacitor running out at different times, stable reps, drones, buffer
    MINE = ['rifter_constructed_states_dual_prop_default', 'abaddon_constructed_armor_implants_boosters', 'drake_constructed_shield_implants_boosters',
            'muninn_zkb138989886_rolebonus_audit', 'vexor_constructed_p3_cap_booster_online', 'rifter_user']
    THREATS = ['megathron_popejoy', 'dominix_navyissue_buffer', 'ishtar_alyra', 'vargur_zkb138983121_bastion', 'caracal_alyra', 'hecate_constructed_defense_armor_repairer']
    # (an ancillary booster's rate isn't a plain amount / duration, so such fits are not TARGETS here: hawk_user etc.)
    mine = [k for k in cands if (tool[k]['projectedTarget']['variants'] or {}).get('propTypeId') and SIMPLE_REPS(orc(k)) and not orc(k).errors and not orc(k).oracleGaps]
    mine = mine[::max(1, len(mine) // 6)][:6]
    threats = [k for k in cands if ((tool[k]['application'].get('weapons') or tool[k]['application'].get('drones'))) and SIMPLE_REPS(orc(k)) and not orc(k).errors and not orc(k).oracleGaps]
    tack = [k for k in threats if (tool[k]['application'].get('projected') or {}).get('scramRange') is not None or any((tool[k]['application'].get('projected') or {}).get(x) for x in ('webMods', 'webDrones', 'tpMods'))]
    threats = (tack[:5] + [k for k in threats if k not in tack][::7][:4])
    mine = [k for k in MINE if k in cands and SIMPLE_REPS(orc(k)) and not orc(k).errors and not orc(k).oracleGaps] + [k for k in mine if k not in MINE][:2]
    threats = [k for k in THREATS if k in cands and SIMPLE_REPS(orc(k)) and not orc(k).errors and not orc(k).oracleGaps] + [k for k in threats if k not in THREATS][:5]
    pairs = [(t, m) for t in threats for m in mine if t != m]
    gin, gout, js = os.path.join(tmp, 'in.json'), os.path.join(tmp, 'out.json'), os.path.join(tmp, 'run.js')
    open(js, 'w').write(NODE)
    json.dump({'fits': {k: tool[k] for k in set(threats) | set(mine)}, 'pairs': pairs, 'grid': GRID}, open(gin, 'w'))
    subprocess.run(['node', js, html, gin, gout], check=True)
    out = json.load(open(gout))
    bad, notes, points, inf_seen, finite_cut = 0, [], 0, 0, 0
    keep_seen = [0, 0]
    capsec = lambda k: math.inf if tool[k]['capacitor'].get('stable') else (tool[k]['capacitor'].get('timeToEmptyExactSec') if tool[k]['capacitor'].get('timeToEmptyExactSec') is not None else math.inf)
    for t, m in pairs:
        tf_fit = CP._Fit(orc(t)); tf_app = CA._Src(orc(t)); t_inp = CP.pyfa_inputs(tf_fit)
        diffs = []
        for i, st in enumerate(GRID):
            me_o = orc(m, bool(st['prop'])); me = CP._Fit(me_o)
            my_top = me.getMaxVelocity(); their_top = tf_fit.getMaxVelocity()
            y_spd, y_ang, t_spd, t_ang, y_holds, t_holds = keep_rule(st, my_top, their_top, reach(t), reach(m))   # v.51 Stopped, v.53 Keep at Range
            y_frac = y_spd / my_top if my_top else 0.0; t_frac = t_spd / their_top if their_top else 0.0
            inc = pyfa_typed(tf_fit, tf_app, t_inp, me, st['range'], y_frac, y_ang, t_frac * their_top, t_ang)
            m_src_fit = CP._Fit(me_o); m_app = CA._Src(me_o); m_inp = CP.pyfa_inputs(m_src_fit)
            outd = pyfa_typed(m_src_fit, m_app, m_inp, tf_fit, st['range'], t_frac, t_ang, y_frac * my_top, y_ang)
            you_last = ttk(orc(m), capsec(m), inc); they_last = ttk(orc(t), capsec(t), outd)
            exp = [sum(inc.values()), sum(outd.values()), you_last, they_last, my_top, their_top, y_holds, t_holds]
            got = out[t + '|' + m][i]; points += 1
            inf_seen += (you_last == math.inf) + (they_last == math.inf)
            finite_cut += sum(1 for x, k in ((you_last, m), (they_last, t)) if x != math.inf and x > capsec(k))
            if got is None: diffs.append(f'{st}: tool gave no matchup'); continue
            names = ('theirDps', 'yourDps', 'youLast', 'theyLast', 'myTop', 'theirTop', 'youCanKeep', 'theyCanKeep')
            keep_seen[0] += (st['mode'] == 'keep') + (st['theirMode'] == 'keep'); keep_seen[1] += (not y_holds) + (not t_holds)
            for n, g, e in zip(names, got, exp):
                if not close(g, e) and len(diffs) < 4: diffs.append(f'{n} {st} tool {g} independent {e}')
        if diffs: bad += 1; notes.append(f'{t} -> {m}: ' + '; '.join(diffs))
    for n in notes[:30]: print(n)
    print(f'{len(threats)} threats x {len(mine)} of my ships ({", ".join(mine)}), {points} points over {len(GRID)} card settings: {2 * points - inf_seen} finite times ({finite_cut} after the capacitor ran out), {inf_seen} "holds"')
    print(f'Keep at Range: {keep_seen[0]} keeping ships; the "can hold" verdict compared for both ships at every point ({keep_seen[1]} can\'t)')
    print(f'{bad} mismatches (strip numbers vs pyfa projected.py + application.py by damage type, and the time-to-kill rule)')
