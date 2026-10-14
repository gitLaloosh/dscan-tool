"""A minimal pyfa fit that runs pyfa's OWN effect handlers (eos/effects.py) on real SDE items.

Used by the independent checks as the reference for a whole fit's attributes (added
v2026.10.14.5 for the resistance phase). Nothing here comes from index.html.

    from pyfa_fit_oracle import OracleFit
    f = OracleFit('Paladin', modules=[('Bastion Module I', 'active'), ('Damage Control II', 'online')])
    f.calculate()
    f.ship.get('armorEmDamageResonance')

What is pyfa's own code and what is a hand port:
  * every effect handler is pyfa's eos/effects.py, executed as-is (tools/pyfa_effects.load_effects);
  * the attribute arithmetic is a hand port of eos/modifiedAttributeDict.py __calculateValue:
    forced value (capped) > preAssign/original/SDE default, + preIncrease, x multipliers,
    x each stacking-penalty group separately (>1 and <1 chains, largest first,
    1 + (m-1)*exp(-i^2/7.1289)), + postIncrease, then min/maxAttributeID caps;
  * the calculation order is a hand port of eos/saveddata/fit.py calculateModifiedAttributes:
    for runTime in early, normal, late: character skills (passive, level from the All 5
    character), ship (passive), modules in fitted order (charge effects first; offline
    always, passive when online+, active when active+; overheat is not run), then the
    Tactical Destroyer mode;
    since v2026.10.14.12 also boosters then implants, between the ship and the modules, as
    eos/saveddata/fit.py orders them (eos/saveddata/implant.py: 'passive' and activeByDefault
    effects, context ('implant',); booster.py: 'passive' effects, context ('booster',), side
    effects only when switched on -- pyfa's default is off, so none here);
  * Skill and HandledList semantics: eos/saveddata/character.py Skill, eos/effectHandlerHelpers.py.
Damage pattern: pyfa's default uniform pattern (25 each), which the Reactive Armor Hardener reads.
Not modelled: fighters, projected and command effects. Drones (v2026.10.14.13): the ones passed in, in space.
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_sde import types, td, attrs, groups, name, T, _en
import pyfa_effects
from pyfa_effects import EFFECTS

ATTR_BY_NAME = {v['name']: v for v in attrs.values()}
ATTR_BY_ID = {int(k): v for k, v in attrs.items()}
SKILL_LEVEL = 5
STATES = {'offline': 0, 'online': 1, 'active': 2, 'overheated': 3}

def _skill_types():
    return [int(t) for t, v in types.items() if v.get('published') and groups[str(v['groupID'])]['categoryID'] == 16]
SKILL_IDS_BY_NAME = {name(t): t for t in _skill_types()}

class Group:
    def __init__(self, t): g = groups[str(types[str(t)]['groupID'])]; self.name = _en(g['groupName']); self.ID = types[str(t)]['groupID']; self.category = g['categoryID']

class GameItem:
    """eos.gamedata.Item stand-in."""
    def __init__(self, t):
        self.ID = self.typeID = int(t); self.name = name(t); self.group = Group(t)
        self.attributes = {ATTR_BY_ID[a['attributeID']]['name']: a['value'] for a in td.get(str(t), {}).get('dogmaAttributes', [])
                           if a['attributeID'] in ATTR_BY_ID}
        # pyfa db_update.py processDogmaAttributes: mass / capacity / volume / radius come from the
        # type row when the type has no dogma attribute of that id (a ship's mass is only there).
        for an in ('mass', 'capacity', 'volume', 'radius'):
            if an not in self.attributes and an in types[str(t)]: self.attributes[an] = types[str(t)][an]
        self.effectIds = [e['effectID'] for e in td.get(str(t), {}).get('dogmaEffects', [])]
        self.requiredSkills = {}
        for i, (sa, la) in enumerate((('requiredSkill1', 'requiredSkill1Level'), ('requiredSkill2', 'requiredSkill2Level'), ('requiredSkill3', 'requiredSkill3Level'),
                                      ('requiredSkill4', 'requiredSkill4Level'), ('requiredSkill5', 'requiredSkill5Level'), ('requiredSkill6', 'requiredSkill6Level'))):
            if sa in self.attributes: self.requiredSkills[int(self.attributes[sa])] = self.attributes.get(la, 0)
    def getAttribute(self, key, default=None):
        # eos.gamedata.Item.getAttribute: the unmodified SDE value (ammoInfluenceCapNeed reads it)
        return self.attributes.get(key, default)
    def requiresSkill(self, skill, level=None):
        # eos.gamedata.Item.requiresSkill: a name, or a Skill object (compared by its item)
        if not isinstance(skill, str): skill = skill.item.name
        sid = SKILL_IDS_BY_NAME.get(skill)
        return sid in self.requiredSkills and (level is None or self.requiredSkills[sid] == level)
    def isType(self, tp):
        return any(tp in _etype(e) for e in self.effectIds if e in EFFECTS)

def _etype(eid):
    t = getattr(EFFECTS[eid], 'type', None)
    return t if isinstance(t, tuple) else ((t,) if t else ())
def _runtime(eid): return getattr(EFFECTS[eid], 'runTime', 'normal')
def _active_by_default(eid): return getattr(EFFECTS[eid], 'activeByDefault', True)

class Attrs:
    """Hand port of eos/modifiedAttributeDict.py (the parts effects use)."""
    def __init__(self, item, fit):
        self.item, self.fit = item, fit
        self.preAssigns, self.forced, self.preInc, self.postInc, self.mult, self.pen = {}, {}, {}, {}, {}, {}
        self.intermediary = {}   # __setitem__ (cap boosters set capacitorNeed this way)
    def original(self, key):
        # getOriginal: the item's value, else the attribute's SDE defaultValue (LESSON #22)
        v = self.item.attributes.get(key)
        return v if v is not None else ATTR_BY_NAME.get(key, {}).get('defaultValue')
    def touched(self, key): return any(key in d for d in (self.preAssigns, self.forced, self.preInc, self.postInc, self.mult, self.pen))
    def get(self, key):
        if not self.touched(key):   # __getitem__: no modifier -> intermediary value, else original
            return self.intermediary[key] if self.intermediary.get(key) is not None else self.original(key)
        info = ATTR_BY_NAME.get(key, {})
        lo = self.get(ATTR_BY_ID[info['minAttributeID']]['name']) if info.get('minAttributeID') in ATTR_BY_ID else None
        hi = self.get(ATTR_BY_ID[info['maxAttributeID']]['name']) if info.get('maxAttributeID') in ATTR_BY_ID else None
        if key in self.forced:
            v = self.forced[key]
            if lo is not None: v = max(v, lo)
            if hi is not None: v = min(v, hi)
            return v
        default = info.get('defaultValue', 0.0)
        o = self.original(key)
        v = self.preAssigns.get(key, o if o is not None else default)
        v += self.preInc.get(key, 0)
        v *= self.mult.get(key, 1)
        for group, ms in self.pen.get(key, {}).items():
            for chain in (sorted([m for m in ms if m > 1], key=lambda m: -abs(m - 1)), sorted([m for m in ms if m < 1], key=lambda m: -abs(m - 1))):
                for i, m in enumerate(chain): v *= 1 + (m - 1) * math.exp(-i * i / 7.1289)
        v += self.postInc.get(key, 0)
        if lo is not None: v = max(v, lo)
        if hi is not None: v = min(v, hi)
        return v
    def _lvl(self, skill): return SKILL_LEVEL if skill else 1
    def preAssign(self, key, value, **kw): self.preAssigns[key] = value
    def increase(self, key, inc, position='pre', skill=None, **kw):
        inc *= SKILL_LEVEL if skill else 1
        tbl = self.preInc if position == 'pre' else self.postInc
        tbl[key] = tbl.get(key, 0) + inc
    def multiply(self, key, m, stackingPenalties=False, penaltyGroup='default', skill=None, **kw):
        if m is None: return
        if skill: m *= SKILL_LEVEL
        if stackingPenalties: self.pen.setdefault(key, {}).setdefault(penaltyGroup, []).append(m)
        else: self.mult[key] = self.mult.get(key, 1) * m
    def boost(self, key, b, skill=None, **kw):
        if skill: b *= SKILL_LEVEL
        self.multiply(key, 1 + b / 100.0, **kw)
    def force(self, key, value, **kw): self.forced[key] = value
    def __getitem__(self, key): return self.get(key)
    def __setitem__(self, key, value): self.intermediary[key] = value
    # ModifiedAttributeDict.__contains__ / __iter__ (Effect2589 Neurotoxin Recovery tests
    # `attr in booster.itemModifiedAttributes`; without these, `in` fell back to __getitem__(0, 1, ...)
    # forever -- found 2026-10-14 when boosters were added): the item's own attributes, anything
    # modified, anything set directly.
    def __contains__(self, key): return key in self.item.attributes or self.touched(key) or key in self.intermediary
    def __iter__(self): return iter(dict.fromkeys(list(self.item.attributes) + [k for d in (self.preAssigns, self.forced, self.preInc, self.postInc, self.mult, self.pen, self.intermediary) for k in d]))

class Handled:
    """HandledItem: the item-modification methods effects call."""
    def getModifiedItemAttr(self, key, default=0):
        v = self.attrs.get(key); return v if v is not None else default
    def preAssignItemAttr(self, *a, **k): self.attrs.preAssign(*a, **k)
    def increaseItemAttr(self, *a, **k): self.attrs.increase(*a, **k)
    def multiplyItemAttr(self, *a, **k): self.attrs.multiply(*a, **k)
    def boostItemAttr(self, *a, **k): self.attrs.boost(*a, **k)
    def forceItemAttr(self, *a, **k): self.attrs.force(*a, **k)
    def getModifiedChargeAttr(self, key, default=0):
        return self.charge.getModifiedItemAttr(key, default) if self.charge else default
    def _chargeOp(op):
        def f(self, *a, **k):
            if self.charge: getattr(self.charge.attrs, op)(*a, **k)
        return f
    preAssignChargeAttr = _chargeOp('preAssign'); increaseChargeAttr = _chargeOp('increase')
    multiplyChargeAttr = _chargeOp('multiply'); boostChargeAttr = _chargeOp('boost'); forceChargeAttr = _chargeOp('force')
    def get(self, key): return self.attrs.get(key)

class Item(Handled):
    def __init__(self, t, fit, state='online', charge=None):
        self.item = GameItem(t); self.attrs = Attrs(self.item, fit); self.state = STATES[state]
        self.charge = Item(charge, fit) if charge else None
        self.owner = fit; self.projected = False; self.rahPatternOverride = None; self.level = SKILL_LEVEL
        self.typeID = self.item.ID; self.isEmpty = False
    @property
    def itemModifiedAttributes(self): return self.attrs   # the ModifiedAttributeDict ([] get/set, force)
    # A module's .charge is an eos.gamedata.Item in pyfa: filters call mod.charge.requiresSkill(...)
    # and read mod.charge.group / .name directly.
    def requiresSkill(self, skill, level=None): return self.item.requiresSkill(skill, level)
    @property
    def group(self): return self.item.group
    @property
    def name(self): return self.item.name
    def __getattr__(self, k): return _Any()

class _Any:
    def __getattr__(self, k): return _Any()
    def __call__(self, *a, **k): return _Any()
    def __iter__(self): return iter(())
    def __bool__(self): return False

class HList(list):
    """eos/effectHandlerHelpers.py HandledList: filtered operations (AttributeError swallowed as pyfa does)."""
    def _f(op, charge=False):
        def f(self, flt, *a, **k):
            for el in self:
                try:
                    if flt(el):
                        tgt = el.charge if charge else el
                        if tgt is not None: getattr(tgt.attrs, op)(*a, **k)
                except AttributeError: pass
        return f
    filteredItemPreAssign = _f('preAssign'); filteredItemIncrease = _f('increase'); filteredItemMultiply = _f('multiply')
    filteredItemBoost = _f('boost'); filteredItemForce = _f('force')
    filteredChargePreAssign = _f('preAssign', True); filteredChargeIncrease = _f('increase', True); filteredChargeMultiply = _f('multiply', True)
    filteredChargeBoost = _f('boost', True); filteredChargeForce = _f('force', True)

class Pattern:
    emAmount = thermalAmount = kineticAmount = explosiveAmount = 25

# eos/saveddata/ship.py Ship.EXTRA_ATTRIBUTES
SHIP_EXTRA_ATTRIBUTES = {'armorRepair': 0, 'armorRepairPreSpool': 0, 'armorRepairFullSpool': 0, 'hullRepair': 0, 'shieldRepair': 0,
                         'maxActiveDrones': 0, 'maxTargetsLockedFromSkills': 2, 'droneControlRange': 20000, 'cloaked': False}

class OracleFit:
    def __init__(self, ship, modules=(), mode=None, implants=(), boosters=(), drones=()):
        """ship: name or typeId; modules: [(name or id, state, charge name or id or None)];
        mode: Tactical Destroyer mode item name (e.g. 'Skua Defense Mode') or None;
        implants / boosters: [name or typeId] (pyfa's fit implants, ImplantLocation.FIT);
        drones: [(name or typeId, amountActive)] -- drones in space (v2026.10.14.13)."""
        tid = lambda x: int(x) if isinstance(x, int) or str(x).isdigit() else int(T(x))
        self.ship = Item(tid(ship), self, 'online')
        self.modules = HList()
        for m in modules:
            m = tuple(m) + (None,) * (3 - len(m))
            self.modules.append(Item(tid(m[0]), self, m[1] or 'online', tid(m[2]) if m[2] else None))
        self.mode = Item(tid(mode), self) if mode else None
        self.skills = [Item(s, self) for s in _skill_types()]
        self.drones = HList(); self.fighters = HList()
        for d, n in drones:   # eos/saveddata/drone.py: amountActive copies in space
            it = Item(tid(d), self); it.amountActive = n; self.drones.append(it)
        # pyfa's database has no expired event boosters (db_update.py deletes them; pyfa_sde.pyfa_removed_types),
        # so pyfa can't load them: dropped here and listed in notLoaded (v2026.10.14.13, LESSON #32).
        from pyfa_sde import pyfa_removed_types
        removed = pyfa_removed_types()
        self.notLoaded = [tid(x) for x in list(implants) + list(boosters) if tid(x) in removed]
        self.appliedImplants = HList(Item(tid(x), self) for x in implants if tid(x) not in removed)
        self.boosters = HList(Item(tid(x), self) for x in boosters if tid(x) not in removed)
        self.character = self; self.damagePattern = Pattern(); self.isStructure = False
        self.errors = []; self.oracleGaps = []
        # eos Fit.extraAttributes IS the ship's ModifiedAttributeDict (fit.py: self.extraAttributes =
        # self.ship.itemModifiedAttributes), whose originals include Ship.EXTRA_ATTRIBUTES (ship.py) --
        # droneControlRange starts at 20000. Before v2026.10.14.13 it was a separate empty dict, so the
        # drone control range read 0 + increases.
        for k, v in SHIP_EXTRA_ATTRIBUTES.items(): self.ship.item.attributes.setdefault(k, v)
        self.extraAttributes = self.ship.attrs
    def getSkill(self, item):
        # eos Character.getSkill (the All 5 character): by name or typeID
        sid = SKILL_IDS_BY_NAME.get(item) if isinstance(item, str) else int(item)
        return next(s for s in self.skills if s.item.ID == sid)
    def __getattr__(self, k): return _Any()
    def _run(self, eid, src, ctx):
        try: EFFECTS[eid].handler(self, src, ctx, None, effect=None)
        except AttributeError as ex:   # pyfa swallows these for skills (character.py) and in HandledList
            # ...but one raised by a MISSING STAND-IN METHOD here is an oracle bug, not pyfa behaviour
            # (LESSON #27, 2026-10-14: no GameItem.getAttribute silently dropped every crystal's cap-need bonus).
            if any(c in str(ex) for c in ("'GameItem'", "'Group'", "'Item'", "'Attrs'", "'OracleFit'", "'HList'")): self.oracleGaps.append((eid, src.item.name, str(ex)[:120]))
        except Exception as ex: self.errors.append((eid, src.item.name, repr(ex)[:120]))
    def calculate(self):
        for rt in ('early', 'normal', 'late'):
            for s in self.skills:
                for e in s.item.effectIds:
                    if e in EFFECTS and _runtime(e) == rt and 'passive' in _etype(e) and _active_by_default(e): self._run(e, s, ('skill',))
            for e in self.ship.item.effectIds:
                if e in EFFECTS and _runtime(e) == rt and 'passive' in _etype(e) and _active_by_default(e): self._run(e, self.ship, ('ship',))
            for d in self.drones:   # drone.py: passive activeByDefault effects, once per drone in space, context ('drone',)
                for e in d.item.effectIds:
                    if e in EFFECTS and _runtime(e) == rt and 'passive' in _etype(e) and _active_by_default(e):
                        for _ in range(d.amountActive): self._run(e, d, ('drone',))
            for b in self.boosters:   # booster.py: passive effects; side effects off (pyfa default)
                for e in b.item.effectIds:
                    if e in EFFECTS and _runtime(e) == rt and 'passive' in _etype(e): self._run(e, b, ('booster',))
            for imp in self.appliedImplants:   # implant.py: passive and activeByDefault
                for e in imp.item.effectIds:
                    if e in EFFECTS and _runtime(e) == rt and 'passive' in _etype(e) and _active_by_default(e): self._run(e, imp, ('implant',))
            for m in self.modules:
                ok = lambda e: (e in EFFECTS and _runtime(e) == rt and _active_by_default(e) and
                                ('offline' in _etype(e) or ('passive' in _etype(e) and m.state >= 1) or ('active' in _etype(e) and m.state >= 2)))
                if m.charge:
                    for e in m.charge.item.effectIds:
                        if ok(e): self._run(e, m, ('moduleCharge',))
                for e in m.item.effectIds:
                    if ok(e): self._run(e, m, ('module',))   # local fit: pyfa's projected/gang conditions are true
            if self.mode:
                for e in self.mode.item.effectIds:
                    if e in EFFECTS and _runtime(e) == rt and _active_by_default(e): self._run(e, self.mode, ('module',))
        return self

RESONANCE = {'shield': {'em': 'shieldEmDamageResonance', 'therm': 'shieldThermalDamageResonance', 'kin': 'shieldKineticDamageResonance', 'exp': 'shieldExplosiveDamageResonance'},
             'armor': {'em': 'armorEmDamageResonance', 'therm': 'armorThermalDamageResonance', 'kin': 'armorKineticDamageResonance', 'exp': 'armorExplosiveDamageResonance'},
             'hull': {'em': 'emDamageResonance', 'therm': 'thermalDamageResonance', 'kin': 'kineticDamageResonance', 'exp': 'explosiveDamageResonance'}}
def resonances(fit):
    return {lay: {d: fit.ship.get(a) if fit.ship.get(a) is not None else 1.0 for d, a in m.items()} for lay, m in RESONANCE.items()}
