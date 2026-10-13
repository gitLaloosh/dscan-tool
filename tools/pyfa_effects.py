"""Run pyfa's REAL effect handlers against a recording mock, instead of
reading eos/effects.py with regexes.

WHY (LESSONS_LEARNED.md #1): regex/text parsing of effects.py silently
misses handlers that loop over attribute names (`for attr in ('maxRange',
'falloff')`), pick skill/penalty through variables, or branch on context.
In the weapon-range batch, text matching found 128 relevant handlers; the
recorder found every one, including the Raven (891), Tracking Computer
(4559) and Myrmidon Navy Issue (11061) that text matching missed.

How it works:
  * load_effects() execs effects.py with its 4 eos imports stubbed (no pip).
  * run(effectId, ctx) calls the handler with a fake `fit` whose collections
    (fit.modules, fit.ship, ...) RECORD every call, and a fake source item
    whose getModifiedItemAttr(name) returns a symbol 'a:<name>' (so you see
    exactly which attribute feeds the bonus and any `* level` scaling).
  * Filters: the recorded lambda is evaluated against real SDE items via
    Probe objects. requiresSkill() uses the item's direct requiredSkill1-6,
    exactly like pyfa. group.name is a RecStr so `==` / `in (...)` compares
    are recorded too.
ctx: 'ship' for hull effects, 'module' for modules/rigs/subsystems/scripts,
'skill' for skills. pyfa passes these as `context`.

Example:
    from pyfa_effects import *
    calls, err = run(4559, 'module')   # pass evaluator=... to test filters (see filter_hits)
    for coll, meth, args, kw in calls: print(coll, meth, args, kw)
"""
import re, sys, os
from pyfa_sde import *

def load_effects():
    src = open(os.path.join(PYFA_SRC, 'eos', 'effects.py')).read()
    src = re.sub(r'^(import eos\.config|from eos\.\S+ import .*)$', r'# \1', src, flags=re.M)
    class _Any:
        def __getattr__(self, k): return _Any()
        def __call__(self, *a, **k): return _Any()
    ns = {'eos': _Any(), 'calculateRangeFactor': lambda *a, **k: 1, 'FittingModuleState': _Any(),
          'FitSystemSecurity': _Any(), 'SpoolType': _Any(), 'SpoolOptions': _Any(),
          'calculateSpoolup': lambda *a, **k: (0, 0, 0), 'resolveSpoolOptions': lambda *a, **k: None}
    exec(compile(src, 'effects.py', 'exec'), ns)
    return {int(k[6:]): v for k, v in ns.items() if k.startswith('Effect') and k[6:].isdigit()}

EFFECTS = load_effects()
skillId = {}
for _k, _v in types.items():
    if groups[str(_v['groupID'])]['categoryID'] == 16: skillId.setdefault(name(_k), int(_k))

class Sym:
    """Symbolic number: records how a bonus value is built (e.g. '(a:rangeSkillBonus*LVL)')."""
    def __init__(s, e): s.e = e
    def _b(s, o, op, r=False):
        oe = o.e if isinstance(o, Sym) else repr(o)
        return Sym(f"({oe}{op}{s.e})" if r else f"({s.e}{op}{oe})")
    __mul__ = lambda s, o: s._b(o, '*'); __rmul__ = lambda s, o: s._b(o, '*', True)
    __add__ = lambda s, o: s._b(o, '+'); __radd__ = lambda s, o: s._b(o, '+', True)
    __sub__ = lambda s, o: s._b(o, '-'); __rsub__ = lambda s, o: s._b(o, '-', True)
    __truediv__ = lambda s, o: s._b(o, '/'); __rtruediv__ = lambda s, o: s._b(o, '/', True)
    __neg__ = lambda s: Sym(f"(-{s.e})")
    __bool__ = lambda s: True
    def __float__(s): return 1.0
    def __gt__(s, o): return True
    __lt__ = __ge__ = __le__ = lambda s, o: False
    def __repr__(s): return s.e

class Any:
    def __getattr__(s, k): return Any()
    def __call__(s, *a, **k): return Any()
    def __iter__(s): return iter([])
    def __bool__(s): return False
    def __contains__(s, x): return False

CALLS = []
class Src:
    """The item carrying the effect (ship/module/skill). Self-modifications
    such as module.boostItemAttr(...) (scripts, ammo) are recorded as 'self'."""
    def __init__(s, ctx, carrier=None): s.ctx = ctx; s.level = Sym('LVL'); s.item = Any(); s.carrier = carrier
    def getModifiedItemAttr(s, n, *a, **k): return Sym('a:' + n)
    getModifiedChargeAttr = getModifiedItemAttr
    def __getattr__(s, k):
        if k.endswith('ItemAttr') and not k.startswith('getModified'):
            def f(*a, **kw): CALLS.append(('self', k, a, kw))
            return f
        return Any()

EVALUATOR = None
class Coll:
    """A fit collection (fit.modules, fit.ship, ...). Every call is recorded.
    If run() was given an evaluator, a filter lambda is evaluated AT CALL TIME
    and the result stored in kwargs['_eval']. This matters: pyfa handlers often
    build lambdas inside a loop (`for skill in (...): ...requiresSkill(skill)`),
    and Python closures see the loop variable's LAST value if evaluated later
    (LESSONS_LEARNED.md #16)."""
    def __init__(s, nm): s.nm = nm
    def __getattr__(s, meth):
        def f(*a, **k):
            if EVALUATOR and a and callable(a[0]):
                k = dict(k); k['_eval'] = EVALUATOR(s.nm, meth, a)
            CALLS.append((s.nm, meth, a, k))
        return f
    def __iter__(s): return iter([])

class Fit:
    def __init__(s):
        for c in ('modules', 'ship', 'drones', 'fighters', 'character', 'appliedImplants'): setattr(s, c, Coll(c))
    def __getattr__(s, k): return Any()

REC = []
class RecStr(str):
    def __eq__(s, o): REC.append(('eq', str(o))); return str.__eq__(s, o)
    def __hash__(s): return str.__hash__(s)
class ProbeGroup:
    def __init__(s, t): s.name = RecStr(gname(t)); s.ID = types[str(t)]['groupID']
class ProbeItem:
    def __init__(s, t): s.t = t; s.group = ProbeGroup(t); s.name = name(t); s.typeID = t; s.ID = t
    def requiresSkill(s, n, *a):
        # LESSON #19: some skill handlers filter on the skill ITSELF
        # (`requiresSkill(skill)`, e.g. Effect1730 drone damage, 1851 launcher
        # RoF). n is then the Src object, not a name: resolve it through the
        # carrier given to run(); without one, record 'skill?' so callers can
        # see the filter was not evaluated instead of getting a silent [].
        if isinstance(n, Src):
            if n.carrier is None: REC.append(('skill?', 'the carrying skill -- pass carrier= to run()')); return False
            REC.append(('skill', name(n.carrier))); return int(n.carrier) in reqs(s.t)
        REC.append(('skill', n)); return skillId.get(n) in reqs(s.t)
    def __getattr__(s, k): return Any()
class Probe:
    """A fitted module (item) with an optional loaded charge, built from real SDE types."""
    def __init__(s, t, chargeT=None):
        s.item = ProbeItem(t); s.charge = ProbeItem(chargeT) if chargeT else None

def run(eid, ctx, evaluator=None, carrier=None):
    """Execute pyfa handler `eid` in context ctx; returns (calls, error).
    evaluator(collection, method, args) -> anything: called immediately for
    every call whose first argument is a filter lambda (see Coll).
    carrier: typeId of the item carrying the effect. Needed for skill
    handlers whose filter is `requiresSkill(skill)` (LESSON #19)."""
    global EVALUATOR
    CALLS.clear(); EVALUATOR = evaluator
    try:
        EFFECTS[eid].handler(Fit(), Src(ctx, carrier), (ctx,), None)
    except Exception as ex:
        return None, repr(ex)[:160]
    finally:
        EVALUATOR = None
    return list(CALLS), None

def filter_hits(lam, pool, as_charge=False, launcher=None):
    """Types in `pool` the handler's filter lambda accepts, plus what it checked."""
    REC.clear(); hits = []
    for t in pool:
        p = Probe(launcher, t) if as_charge else Probe(t)
        try:
            if lam(p): hits.append(t)
        except Exception: pass
    return hits, sorted(set(REC))

def carriers():
    """effectId -> [published typeIds carrying it]."""
    out = {}
    for t, v in types.items():
        if not v.get('published'): continue
        for e in td.get(t, {}).get('dogmaEffects', []): out.setdefault(e['effectID'], []).append(int(t))
    return out
