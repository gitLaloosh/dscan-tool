"""Run a golden fit (regression_suite/golden_fits.json) through pyfa's own handlers
(tools/pyfa_fit_oracle.py). Only the fit's ITEM LIST is read from the golden file
(slot groups, quantities, loaded charges, pinned module states) -- never its expected values
and never index.html.

States: a pinned moduleStates entry if the fit has one, else pyfa's state for a freshly
added module (Module.getMaxState(ACTIVE): active when the item has an active effect and
activationBlocked is 0, else online).
Implants / boosters (v2026.10.14.12): the tally's 'Implants' / 'Boosters' groups (a pasted EFT fit) or,
for a killmail fixture, flag-89 items -- the latter only when the tool's PILOT_ANALYZER_APPLY_IMPLANTS is on
(off: the Pilot Analyzer does not apply them; read from index.html, an input switch, not a formula)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pyfa_fit_oracle import OracleFit, GameItem, resonances, EFFECTS, _etype
from indep_common import GOLDEN

SLOTS = ('High slots', 'Mid slots', 'Low slots', 'Rigs', 'Subsystems')
# The tool's documented INPUT choice (DEVIATIONS.md section 2): modules carrying one of these
# effects default to online instead of active (cloaks, MJD/MJFG, Signature Suppressor burst,
# Entosis Link, Capital Sensor Arrays, Assault Damage Control burst). Same ids as the tool's
# MODULE_DEFAULT_ONLINE_EFFECTS -- typed here from that DEVIATIONS entry, an input, not a formula.
DEFAULT_ONLINE_EFFECTS = {607, 980, 5945, 4921, 6208, 12126, 8109, 6063, 6567, 12597, 7012, 2857, 7142}   # 2857 cyno since v2026.10.14.8; 7142 Zero-Point Mass Entangler since v2026.10.14.30
def pyfa_default_state(t):
    it = GameItem(t)
    act = any('active' in _etype(e) for e in it.effectIds if e in EFFECTS) and not it.attributes.get('activationBlocked', 0)
    if act and DEFAULT_ONLINE_EFFECTS & set(it.effectIds): return 'online'
    return 'active' if act else 'online'
def apply_group_limits(mods):
    """pyfa Module.canHaveState: at most maxGroupActive ACTIVE / maxGroupOnline online-or-active per group name."""
    act, onl, out = {}, {}, []
    for t, s, ch in mods:
        it = GameItem(t); g = it.group.name
        ma, mo = it.attributes.get('maxGroupActive'), it.attributes.get('maxGroupOnline')
        if s == 'active' and ma and act.get(g, 0) >= ma: s = 'online'
        if s in ('active', 'online') and mo and onl.get(g, 0) >= mo: s = 'offline'
        if s == 'active': act[g] = act.get(g, 0) + 1
        if s in ('active', 'online'): onl[g] = onl.get(g, 0) + 1
        out.append((t, s, ch))
    return out

_G = None
def td_mode(shipId, mode):
    """Tactical Destroyer mode item for a hull ('sharpshooter'|'defense'|'propulsion'), or None."""
    from pyfa_sde import name, T
    t = T(f'{name(shipId)} {mode.capitalize()} Mode')
    return int(t) if t else None
def _pilot_analyzer_applies_implants():
    import re
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')).read()
    m = re.search(r'const PILOT_ANALYZER_APPLY_IMPLANTS = (true|false);', src)
    return bool(m and m.group(1) == 'true')
def implants_of(f):
    """(implants, boosters) type ids the tool applies for this golden fit."""
    if f.get('killmail'):
        if not _pilot_analyzer_applies_implants(): return [], []
        return [it['item_type_id'] for it in f['killmail']['victim'].get('items', []) if it['flag'] == 89], []
    t = f.get('tally') or {}
    return [int(x) for x in (t.get('Implants') or {})], [int(x) for x in (t.get('Boosters') or {})]
def per_copy_order(st, n):
    """v2026.10.14.76: a state per copy (moduleStates[typeId].order, set on the Fit card; copies in flag order), used, as
    the tool uses it, only when it has one entry per copy and as many 'active' as the resolved counts."""
    if not isinstance(st, dict): return None
    o = st.get('order')
    if not isinstance(o, list) or len(o) != n: return None
    if 'active' in st and o.count('active') != round(st['active']): return None
    return o

def oracle_for(fitId, mode=None, states=None, drones=(), group_limits=True, fighters=()):
    """drones: [(typeId, inSpace)] -- the tool's own choice of drones in space (an input, DEVIATIONS.md).
    fighters: [(typeId, amount)] per squadron in space -- likewise the tool's own launch (v2026.10.14.64).
    group_limits=False: the states given are already legal (the tool's own resolved states, which apply the
    hull's maxGroupActive modifiers this stand-in doesn't), so apply_group_limits is skipped."""
    global _G
    if _G is None: _G = json.load(open(GOLDEN))
    f = _G[fitId]
    if mode is None:
        # the tool's default (resolveModeKey): the fit's pinned mode, else Sharpshooter on a Tactical
        # Destroyer, else the hull's first mode item (pyfa Ship.validateModeItem: the Anhinga's Primary)
        sid = int(f['shipTypeId'])
        mode = td_mode(sid, f.get('tacticalMode') or 'sharpshooter') or td_mode(sid, 'primary')
    pinned = states or f.get('moduleStates') or {}
    if states:   # v.76: the tool's resolved counts keep the fit's pinned state per copy (an input; per_copy_order checks it agrees)
        pinned = {tid: ({**st, 'order': po['order']} if isinstance(st, dict) and isinstance(po, dict) and isinstance(po.get('order'), list) else st)
                  for tid, st in states.items() for po in [(f.get('moduleStates') or {}).get(tid)]}
    if f.get('killmail'):
        # ESI killmail flags: 11-18 low, 19-26 mid, 27-34 high, 92-99 rigs, 125-132 subsystems;
        # a charge shares its module's flag (category 8).
        from pyfa_sde import cat
        byflag = {}
        for it in f['killmail']['victim'].get('items', []):
            fl = it['flag']
            if not (11 <= fl <= 34 or 92 <= fl <= 99 or 125 <= fl <= 132): continue
            q = it.get('quantity_destroyed', 0) + it.get('quantity_dropped', 0)
            byflag.setdefault(fl, []).append((it['item_type_id'], q))
        mods = []; seen = {}
        for fl, lst in sorted(byflag.items()):
            mod = next((t for t, q in lst if cat(t) != 8), None); ch = next((t for t, q in lst if cat(t) == 8), None)
            if mod is None: continue
            st = pinned.get(str(mod)); i = seen.get(mod, 0); seen[mod] = i + 1
            if isinstance(st, dict):   # {active, online, offline} counts (compare_fit_stats.py passes the tool's own)
                s = 'active' if i < st.get('active', 0) else 'online' if i < st.get('active', 0) + st.get('online', 0) else 'offline'
            else: s = st if isinstance(st, str) else pyfa_default_state(mod)
            mods.append((mod, s, ch))
        imps, boos = implants_of(f)
        return OracleFit(int(f['shipTypeId']), apply_group_limits(mods) if group_limits else mods, mode=mode, implants=imps, boosters=boos, drones=drones, fighters=fighters).calculate()
    # A slot flag lists its module and loaded charge in either order (the killmail's item order).
    from pyfa_sde import cat
    charges = {}
    for key in ('highSlotByFlag', 'midSlotByFlag'):
        for flag, lst in sorted((f.get(key) or {}).items(), key=lambda kv: int(kv[0])):   # copies in flag order, as the tool walks them
            mod = next((x for x in lst if cat(x['id']) != 8), None); ch = next((x['id'] for x in lst if cat(x['id']) == 8), None)
            # a constructed fit may list several copies under one flag ({id, qty: 5}): each copy gets the charge
            if mod is not None and ch is not None: charges.setdefault(mod['id'], []).extend([ch] * max(1, int(mod.get('qty') or 1)))
    mods = []
    for g in SLOTS:
        for tid, v in (f['tally'].get(g) or {}).items():
            if cat(int(tid)) == 8: continue   # loaded charges (paired above), not modules
            n = round(v['totalQty'] / max(1, v.get('lossCount', 1)))
            st = pinned.get(tid)
            order = per_copy_order(st, n)
            for i in range(n):
                if order: s = order[i]
                elif isinstance(st, dict):   # {active, online, offline} counts
                    s = 'active' if i < st.get('active', 0) else 'online' if i < st.get('active', 0) + st.get('online', 0) else 'offline'
                else: s = st or pyfa_default_state(int(tid))
                ch = charges.get(int(tid), [])
                mods.append((int(tid), s, ch[i] if i < len(ch) else None))
    imps, boos = implants_of(f)
    return OracleFit(int(f['shipTypeId']), apply_group_limits(mods) if group_limits else mods, mode=mode, implants=imps, boosters=boos, drones=drones, fighters=fighters).calculate()
