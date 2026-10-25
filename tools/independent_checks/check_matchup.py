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
  // v2026.10.14.58: each layer's end (the "why" panel's times) and the words
  return r && [r.theirDps, r.yourDps, fin(r.youLast), fin(r.theyLast), r.myTop, r.theirTop, r.keep.you.ok, r.keep.them.ok,
    r.trace.you.layers.map(l => fin(l.end)), r.trace.them.layers.map(l => fin(l.end)), r.why.you, r.why.them];
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
def typed_dps_fighter_ability(f, a):
    """v2026.10.14.64: one fighter ability's DPS by damage type (pyfa FighterAbility.getVolley / getDps on the oracle's attributes)"""
    if not a.dealsDamage or not a.active or a.attrPrefix == 'fighterAbilityLaunchBomb': return {}
    g = f.getModifiedItemAttr; cyc = g(f'{a.attrPrefix}Duration') / 1000
    m = f.amount * g(f'{a.attrPrefix}DamageMultiplier', 1)
    return {k: g(f'{a.attrPrefix}Damage{n}', 0) * m / cyc for k, n in (('em', 'EM'), ('therm', 'Therm'), ('kin', 'Kin'), ('exp', 'Exp'))} if cyc else {}
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
    for f in src_app.fighters:   # v2026.10.14.64 (D5 fighters)
        for a in f.abilities:
            for k, v in typed_dps_fighter_ability(f, a).items(): typed[k] += v * am.get((f, a.effectID), 0)
    return typed

def asb_windows(clip, cyc, reload, cycles):
    """v2026.10.14.57: the times an Ancillary Shield Booster on charges is cycling: `clip` cycles, a reload, again, until
    `cycles` are used (written from the description in METHODOLOGY.md, "The fight")."""
    out, t, left = [], 0.0, cycles
    while left > 0:
        n = min(clip, left); out.append((t, t + n * cyc)); t += n * cyc; left -= n
        if left > 0: t += reload
    return out
def ttk(o, cap_sec, typed, asb=None, ends=None, aar=None):
    """P2, written again from its description: layer by layer, reps while the capacitor lasts, passive shield regen always.
    asb (v.57): {'windows': [...]} for an Ancillary Shield Booster on charges -- it reps inside its windows only, whatever
    the capacitor; None with an ASB fitted = no charges aboard: it reps while the capacitor lasts like any booster.
    ends (v.58): a list that gets each layer's end time (the "why" panel's clock times).
    aar (v.61): {'rate', 'mult', 'windows'} for an Ancillary Armor Repairer with paste aboard -- windows from the ARMOR
    layer's start; rate x mult inside them, nothing in the reloads between, its plain rate after the last, and all of it
    only while the capacitor lasts. None with an AAR fitted = no paste: its plain rate while the capacitor lasts."""
    sh = o.ship.get; res = resonances(o)
    asb_mods = [m for m in o.modules if m.state >= 2 and m.item.group.name == 'Ancillary Shield Booster']
    asb_rate = sum(m.get('shieldBonus') / (m.get('duration') / 1000) for m in asb_mods)
    rep_s = sum(m.get('shieldBonus') / (m.get('duration') / 1000) for m in o.modules if m.state >= 2 and 4 in m.item.effectIds) + (0 if asb else asb_rate)
    aar_mods = [m for m in o.modules if m.state >= 2 and 5275 in m.item.effectIds]   # v.61: fueledArmorRepair
    aar_rate = sum(m.get('armorDamageAmount') / (m.get('duration') / 1000) for m in aar_mods)
    rep_a = sum(m.get('armorDamageAmount') / (m.get('duration') / 1000) for m in o.modules if m.state >= 2 and 27 in m.item.effectIds) + (0 if aar else aar_rate)
    rep_h = sum(m.get('structureDamageAmount') / (m.get('duration') / 1000) for m in o.modules if m.state >= 2 and 26 in m.item.effectIds)
    shield = sh('shieldCapacity') or 0; tau = (sh('shieldRechargeRate') or 0) / 1000
    layers = [(shield, res['shield'], rep_s, 2.5 * shield / tau if shield > 0 and tau > 0 else 0, asb, None), (sh('armorHP') or 0, res['armor'], rep_a, 0, None, aar), (sh('hp') or 0, res['hull'], rep_h, 0, None, None)]
    t = 0.0
    for hp_max, r, rep, passive, a, aa in layers:
        if hp_max <= 0: continue
        incoming = sum(typed[k] * r[k] for k, _ in TYPES)
        aw = [(t + w0, t + w1) for w0, w1 in aa['windows']] if aa else []   # the AAR's clip runs from this layer's start
        def aar_part(mid):
            if not aa or mid >= cap_sec: return 0.0
            if any(w0 <= mid < w1 for w0, w1 in aw): return aa['rate'] * aa['mult']
            return 0.0 if aw and mid < aw[-1][1] else aa['rate']
        # the reps change only at the capacitor's empty time and at the ASB's / AAR's window edges
        edges = sorted({cap_sec} | {x for w in (a['windows'] if a else []) for x in w} | {x for w in aw for x in w})
        hp = hp_max
        while True:
            later = [e for e in edges if e > t + 1e-9]
            nxt = later[0] if later else math.inf
            mid = t + 1e-6 if nxt == math.inf else (t + nxt) / 2
            reps = (rep if mid < cap_sec else 0) + (asb_rate if a and any(w0 <= mid < w1 for w0, w1 in a['windows']) else 0) + aar_part(mid)
            net = incoming - reps - passive
            if nxt == math.inf:
                if net <= 0:
                    if ends is not None: ends.append(math.inf)
                    return math.inf
                t += hp / net; break
            if net > 0 and hp / net <= nxt - t: t += hp / net; break
            hp = min(hp_max, hp - net * (nxt - t)); t = nxt
        if ends is not None: ends.append(t)
    return t

SIMPLE_REPS = lambda o: not any(m.item.group.name in ('Shield Boost Amplifier', 'Siege Module', 'Ancillary Shield Booster', 'Ancillary Armor Repairer') or {4936, 5275} & set(m.item.effectIds) for m in o.modules if m.state >= 1)
# v2026.10.14.57: Ancillary Shield Boosters are checked too (their clip); v2026.10.14.61 Ancillary Armor Repairers too
# (their paste clip); amplifiers and siege still not
ASB_OK = lambda o: not any(m.item.group.name in ('Shield Boost Amplifier', 'Siege Module') for m in o.modules if m.state >= 1)
PASTE = 'Nanite Repair Paste'
def aar_input(o, loaded, hold):
    """v2026.10.14.61: an Ancillary Armor Repairer's paste aboard, the rule as decided (METHODOLOGY.md "The fight"):
    loaded (seen, or a killmail's assumed full clip) = a full clip per copy, plus the hold; the clip from pyfa's numbers
    (capacity / paste volume / chargeRate = numShots, reloadTime), the boost chargedArmorDamageMultiplier."""
    from pyfa_sde import types, T
    mods = [m for m in o.modules if m.state >= 2 and 5275 in m.item.effectIds]
    if not mods: return None
    m = mods[0]; q = len(mods); cr = m.get('chargeRate') or 1
    h = hold(int(T(PASTE)))
    if not loaded and h <= 0: return None
    vol = float(types[str(T(PASTE))]['volume'])
    clip = int(int(m.get('capacity') / vol + 1e-9) // cr)
    if clip <= 0: return None
    cycles = int(((clip * cr * q if loaded else 0) + h) // q // cr)
    if cycles <= 0: return None
    return {'rate': sum(x.get('armorDamageAmount') / (x.get('duration') / 1000) for x in mods), 'mult': m.get('chargedArmorDamageMultiplier'),
            'windows': asb_windows(clip, m.get('duration') / 1000, (m.get('reloadTime') or 0) / 1000, cycles)}
def asb_input(o, cap_tool, hold):
    """The ASB's charges aboard, from the tool's INPUTS (capacitor.asb: loaded / taken from cargo / none, an input choice in
    DEVIATIONS.md) and the fit's hold; the clip from pyfa's numbers (capacity, charge volume, chargeRate, reloadTime)."""
    from pyfa_sde import types, T
    mods = [m for m in o.modules if m.state >= 2 and m.item.group.name == 'Ancillary Shield Booster']
    a = (cap_tool or {}).get('asb') or {}
    if not mods or not a.get('confirmed') or not a.get('chargeName'): return None
    m = mods[0]; q = len(mods)
    vol = float(types[str(T(a['chargeName']))]['volume'])
    clip = int(int(m.get('capacity') / vol + 1e-9) // (m.get('chargeRate') or 1))
    if clip <= 0: return None
    total = hold(int(T(a['chargeName']))) + (0 if a.get('fromCargo') else clip * q)
    return {'windows': asb_windows(clip, m.get('duration') / 1000, (m.get('reloadTime') or 0) / 1000, int(total // q // (m.get('chargeRate') or 1)))}

if __name__ == '__main__':
    ROOT = os.path.join(HERE, '..', '..')
    html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
    G = json.load(open(GOLDEN))
    tmp = tempfile.mkdtemp(); dump = os.path.join(tmp, 'd.json')
    FIELDS = 'application,projectedTarget,moduleStates,droneStates,exact,resonance,capacitor,speed'
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, dump, FIELDS, '-', ','.join(G)], check=True, stdout=subprocess.DEVNULL)
    tool = json.load(open(dump))
    # v2026.10.14.57: the owner's own pair (2026-10-24, both with an X-Large Ancillary Shield Booster), run from their EFT text
    # through the tool's real engine (eft_engine) and through pyfa by item names
    EFT = {'eft:orthrus_threat': os.path.join(HERE, 'fits', 'orthrus_threat.eft'), 'eft:osprey_navy_issue_mine': os.path.join(HERE, 'fits', 'osprey_navy_issue_mine.eft')}
    # v2026.10.14.61: an Ancillary Armor Repairer with its paste loaded, only in cargo, and none
    EFT.update({f'eft:vexor_aar_paste_{v}': os.path.join(HERE, 'fits', f'vexor_aar_paste_{v}.eft') for v in ('loaded', 'cargo', 'none')})
    EFT['km:vexor_aar_paste_none'] = EFT['eft:vexor_aar_paste_none']   # the same fit as a killmail: a full clip assumed
    from eft_engine import run_efts
    tool.update(run_efts(html, {k: open(v).read() for k, v in EFT.items()}))
    def eft_items(k):
        """(module type id, loaded charge name) per module line, and the hold: {type id: qty} of 'Name xN' lines"""
        from pyfa_sde import T, cat
        mods, hold = [], {}
        for l in open(EFT[k]).read().split('\n')[1:]:
            l = l.strip()
            if not l: continue
            if ' x' in l and l.rsplit(' x', 1)[1].isdigit():
                n, q = l.rsplit(' x', 1); tid = T(n.strip())
                if tid: hold[int(tid)] = hold.get(int(tid), 0) + int(q)
                continue
            name, _, ch = l.partition(','); tid = T(name.strip())
            if tid and cat(int(tid)) != 8: mods.append((int(tid), ch.strip() or None))
        return mods, hold
    def hold_of(k):
        if k in EFT: h = eft_items(k)[1]; return lambda tid: h.get(tid, 0)
        f = G[k]
        if f.get('killmail'):
            items = [it for it in f['killmail']['victim'].get('items', []) if it['flag'] in (5, 155)]
            return lambda tid: sum(it.get('quantity_destroyed', 0) + it.get('quantity_dropped', 0) for it in items if it['item_type_id'] == tid)
        t = f.get('tally') or {}
        return lambda tid: sum((t.get(g) or {}).get(str(tid), {}).get('totalQty', 0) / max(1, (t.get(g) or {}).get(str(tid), {}).get('lossCount', 1)) for g in ('Cargo', 'Fleet hangar'))
    def aar_loaded(k):
        """paste in the AAR: a pasted fit (EFT, or a golden with fitSource eft) only when it lists it; a killmail or a
        golden tally always (seen, or a full clip assumed)"""
        from pyfa_sde import T
        if k.startswith('km:'): return True
        if k in EFT: return any(ch == PASTE for _, ch in eft_items(k)[0])
        f = G[k]
        if f.get('fitSource') == 'eft': return str(T(PASTE)) in ((f.get('tally') or {}).get('Low slots') or {})
        return True
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
            if k in EFT:
                from pyfa_fit_oracle import OracleFit
                seen, mods = {}, []
                for tid, ch in eft_items(k)[0]:
                    st_ = states.get(str(tid)) or {'active': 0, 'online': 1, 'offline': 0}; i = seen.get(tid, 0); seen[tid] = i + 1
                    mods.append((tid, 'active' if i < st_['active'] else 'online' if i < st_['active'] + st_['online'] else 'offline', ch))
                oracles[key] = OracleFit(open(EFT[k]).read().split('\n')[0][1:].split(',')[0], mods, drones=drones, fighters=CA.tool_fighters(tool[k].get('application'))).calculate()
            else: oracles[key] = oracle_for(k, states=states, drones=drones, group_limits=False, fighters=CA.tool_fighters(tool[k].get('application')))
        return oracles[key]
    cands = [k for k in G if ok_fit(k)]
    # my ships: armor / shield reps with the capacitor running out at different times, stable reps, drones, buffer
    MINE = ['rifter_constructed_states_dual_prop_default', 'abaddon_constructed_armor_implants_boosters', 'drake_constructed_shield_implants_boosters',
            'muninn_zkb138989886_rolebonus_audit', 'vexor_constructed_p3_cap_booster_online', 'rifter_user']
    THREATS = ['megathron_owner', 'dominix_navyissue_buffer', 'ishtar_zkb137694046', 'vargur_zkb138983121_bastion', 'caracal_zkb136427798', 'hecate_constructed_defense_armor_repairer',
               # v2026.10.14.64 (D5 fighters): carriers -- light, superiority and heavy squadrons; a capital as the TARGET too
               'hel_constructed_fighter_application', 'revenant_constructed_fighter_application', 'nidhoggur_constructed_fighter_velocity']
    # (an ancillary booster's rate isn't a plain amount / duration, so such fits are not TARGETS here: hawk_user etc.)
    mine = [k for k in cands if (tool[k]['projectedTarget']['variants'] or {}).get('propTypeId') and SIMPLE_REPS(orc(k)) and not orc(k).errors and not orc(k).oracleGaps]
    mine = mine[::max(1, len(mine) // 6)][:6]
    threats = [k for k in cands if ((tool[k]['application'].get('weapons') or tool[k]['application'].get('drones') or tool[k]['application'].get('fighters'))) and SIMPLE_REPS(orc(k)) and not orc(k).errors and not orc(k).oracleGaps]
    tack = [k for k in threats if (tool[k]['application'].get('projected') or {}).get('scramRange') is not None or any((tool[k]['application'].get('projected') or {}).get(x) for x in ('webMods', 'webDrones', 'tpMods'))]
    threats = (tack[:5] + [k for k in threats if k not in tack][::7][:4])
    mine = [k for k in MINE if k in cands and SIMPLE_REPS(orc(k)) and not orc(k).errors and not orc(k).oracleGaps] + [k for k in mine if k not in MINE][:2]
    threats = [k for k in THREATS if k in cands and SIMPLE_REPS(orc(k)) and not orc(k).errors and not orc(k).oracleGaps] + [k for k in threats if k not in THREATS][:5]
    pairs = [(t, m) for t in threats for m in mine if t != m]
    # v2026.10.14.64: a capital as the target (anti-capital torpedoes at full damage) and a subcapital threat against a carrier
    pairs += [(t, m) for t, m in (('revenant_constructed_fighter_application', 'hel_constructed_fighter_application'),
                                  ('hel_constructed_fighter_application', 'thanatos_constructed_dda_fighters'),
                                  ('megathron_owner', 'nidhoggur_constructed_fighter_velocity')) if t in cands and m in cands]
    # v.57: fits with an Ancillary Shield Booster, both ways (charges loaded, from cargo, none), and the owner's pair
    asb_fits = [k for k in cands if any(m.item.group.name == 'Ancillary Shield Booster' and m.state >= 2 for m in orc(k).modules) and ASB_OK(orc(k)) and not orc(k).errors and not orc(k).oracleGaps]
    asb_mine = [k for k in asb_fits if (tool[k]['projectedTarget']['variants'] or {}).get('propTypeId')]
    asb_threats = [k for k in asb_fits if tool[k]['application'].get('weapons') or tool[k]['application'].get('drones')]
    pairs += [(t, m) for t in asb_threats for m in mine[:2] if t != m] + [(t, m) for t in threats[:2] for m in asb_mine if t != m]
    pairs += [('eft:orthrus_threat', 'eft:osprey_navy_issue_mine'), ('eft:osprey_navy_issue_mine', 'eft:orthrus_threat')]
    # v.61: fits with an Ancillary Armor Repairer (golden killmails: paste seen; the Vexors: loaded / cargo only / none), both ways
    aar_fits = [k for k in cands if any(5275 in m.item.effectIds and m.state >= 2 for m in orc(k).modules) and ASB_OK(orc(k)) and not orc(k).errors and not orc(k).oracleGaps]
    aar_mine = [k for k in aar_fits if (tool[k]['projectedTarget']['variants'] or {}).get('propTypeId')]
    aar_threats = [k for k in aar_fits if tool[k]['application'].get('weapons') or tool[k]['application'].get('drones')]
    pairs += [(t, m) for t in aar_threats for m in mine[:2] if t != m] + [(t, m) for t in threats[:2] for m in aar_mine if t != m]
    VEX = [f'eft:vexor_aar_paste_{v}' for v in ('loaded', 'cargo', 'none')] + ['km:vexor_aar_paste_none']
    # every threat against each Vexor (weaker ones make long fights: reloads, paste running out), and the Vexors as threats
    pairs += [('eft:orthrus_threat', v) for v in VEX] + [(v, 'eft:osprey_navy_issue_mine') for v in VEX] + [(t, v) for t in threats for v in VEX] + [(v, m) for v in VEX for m in mine[:3]]
    gin, gout, js = os.path.join(tmp, 'in.json'), os.path.join(tmp, 'out.json'), os.path.join(tmp, 'run.js')
    open(js, 'w').write(NODE)
    json.dump({'fits': {k: tool[k] for k in {x for pr in pairs for x in pr}}, 'pairs': pairs, 'grid': GRID}, open(gin, 'w'))
    subprocess.run(['node', js, html, gin, gout], check=True)
    out = json.load(open(gout))
    bad, notes, points, inf_seen, finite_cut = 0, [], 0, 0, 0
    keep_seen = [0, 0]
    why_seen, why_kinds = [0], {}
    def clock(x):
        r = int(math.floor(x + 0.5)); return f'{r // 3600}:{r % 3600 // 60:02d}:{r % 60:02d}' if r >= 3600 else f'{r // 60}:{r % 60:02d}'
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
            you_ends, they_ends = [], []
            you_last = ttk(orc(m), capsec(m), inc, asb_input(orc(m), tool[m]['capacitor'], hold_of(m)), you_ends, aar_input(orc(m), aar_loaded(m), hold_of(m)))
            they_last = ttk(orc(t), capsec(t), outd, asb_input(orc(t), tool[t]['capacitor'], hold_of(t)), they_ends, aar_input(orc(t), aar_loaded(t), hold_of(t)))
            exp = [sum(inc.values()), sum(outd.values()), you_last, they_last, my_top, their_top, y_holds, t_holds]
            got = out[t + '|' + m][i]; points += 1
            inf_seen += (you_last == math.inf) + (they_last == math.inf)
            finite_cut += sum(1 for x, k in ((you_last, m), (they_last, t)) if x != math.inf and x > capsec(k))
            if got is None: diffs.append(f'{st}: tool gave no matchup'); continue
            names = ('theirDps', 'yourDps', 'youLast', 'theyLast', 'myTop', 'theirTop', 'youCanKeep', 'theyCanKeep')
            keep_seen[0] += (st['mode'] == 'keep') + (st['theirMode'] == 'keep'); keep_seen[1] += (not y_holds) + (not t_holds)
            for n, g, e in zip(names, got, exp):
                if not close(g, e) and len(diffs) < 4: diffs.append(f'{n} {st} tool {g} independent {e}')
            # v2026.10.14.58: each layer's end, and the "why" words: every clock time they print is a layer's end
            for side, g_ends, e_ends, why, total in (('you', got[8], you_ends, got[10], you_last), ('them', got[9], they_ends, got[11], they_last)):
                why_seen[0] += 1
                if len(g_ends) != len(e_ends) or not all(close(a, b) for a, b in zip(g_ends, e_ends)):
                    if len(diffs) < 4: diffs.append(f'{side} layer ends {st} tool {g_ends} independent {e_ends}')
                words = ' '.join([why['title']] + why['text'])
                if not why['text'] or re.search(r'undefined|NaN|null|\[object', words):
                    if len(diffs) < 4: diffs.append(f'{side} why {st}: {words!r}')
                ok_t = {clock(x) for x in e_ends if x != math.inf}
                cap_t = clock(capsec(m if side == 'you' else t)) if capsec(m if side == 'you' else t) != math.inf else None
                for c in re.findall(r'breaks at (\d+:\d\d(?::\d\d)?)', words):
                    if c not in ok_t and len(diffs) < 4: diffs.append(f'{side} why {st}: "breaks at {c}" is no layer end ({sorted(ok_t)})')
                for c in re.findall(r'capacitor (?:runs|ran) dry at (\d+:\d\d(?::\d\d)?)', words):
                    if c != cap_t and len(diffs) < 4: diffs.append(f'{side} why {st}: capacitor dry at {c}, independent {cap_t}')
                want = 'You hold' if (side == 'you' and total == math.inf) else 'They hold' if total == math.inf else None
                if want and why['title'] != want and len(diffs) < 4: diffs.append(f'{side} why title {why["title"]!r}')
                kinds = re.findall(r"(reload:|nothing left to load|runs dry|ran dry|even with|regen alone|holds|With no|with paste|paste runs out|full clip is assumed)", words)
                for k_ in kinds: why_kinds[k_] = why_kinds.get(k_, 0) + 1
        if diffs: bad += 1; notes.append(f'{t} -> {m}: ' + '; '.join(diffs))
    for n in notes[:30]: print(n)
    print(f'{len(threats)} threats x {len(mine)} of my ships ({", ".join(mine)}), {points} points over {len(GRID)} card settings: {2 * points - inf_seen} finite times ({finite_cut} after the capacitor ran out), {inf_seen} "holds"')
    print(f'Keep at Range: {keep_seen[0]} keeping ships; the "can hold" verdict compared for both ships at every point ({keep_seen[1]} can\'t)')
    print(f'Ancillary Shield Boosters: {len(asb_threats)} as threats, {len(asb_mine)} as my ship ({", ".join(asb_fits)}), plus the owner\'s Orthrus / Osprey Navy Issue both ways')
    print(f'Ancillary Armor Repairers: {len(aar_threats)} as threats, {len(aar_mine)} as my ship ({", ".join(aar_fits)}), plus 3 Vexors (paste loaded / cargo only / none) and the paste-less one as a killmail (a clip assumed), both ways')
    print(f'Why panel: {why_seen[0]} explanations, each layer\'s end compared; sentence kinds seen: {dict(sorted(why_kinds.items()))}')
    print(f'{bad} mismatches (strip numbers vs pyfa projected.py + application.py by damage type, and the time-to-kill rule)')
