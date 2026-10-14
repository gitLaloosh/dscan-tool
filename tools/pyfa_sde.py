"""CCP SDE access through pyfa's own static-data dump.

Data source (primary): pyfa's repo ships CCP's SDE as JSON under
staticdata/fsd_built/. Point PYFA_SRC at a pyfa checkout (git clone
https://github.com/pyfa-org/Pyfa). Verified with pyfa v2.69.2
(commit 3b9ce39b, SDE client build 3579973).

    PYFA_SRC=/path/to/Pyfa python3 -I some_script.py

Helpers: types, td (type dogma), attrs, effs, groups, cats;
name(typeId), aname(attrId), ename(effectId), T(typeName) -> typeId str,
A(typeName) -> {attributeName: value}, gname(typeId), reqs(typeId).
"""
import json, glob, os
PYFA_SRC = os.environ.get('PYFA_SRC', os.path.join(os.path.dirname(__file__), 'pyfa'))
B = os.path.join(PYFA_SRC, 'staticdata', 'fsd_built') + os.sep
if not os.path.isdir(B):
    raise SystemExit(f'pyfa static data not found at {B}. Set PYFA_SRC to a pyfa checkout.')

def load(prefix):
    d = {}
    for f in sorted(glob.glob(B + prefix + '.*.json')):
        x = json.load(open(f))
        if isinstance(x, dict): d.update(x)
        else:
            for e in x: d[str(e.get('typeID', e.get('id')))] = e
    return d

types = load('types'); td = load('typedogma'); attrs = load('dogmaattributes')
effs = load('dogmaeffects'); groups = load('groups'); cats = load('categories')

def _en(n): return n.get('en-us') if isinstance(n, dict) else n
def name(t): return _en(types[str(t)].get('typeName') or types[str(t)].get('name'))
def aname(a): return attrs[str(a)].get('name')
def ename(e): return effs[str(e)].get('effectName')
def gname(t): return _en(groups[str(types[str(t)]['groupID'])]['groupName'])
def cat(t): return groups[str(types[str(t)]['groupID'])]['categoryID']
_byname = {}
for _k, _v in types.items(): _byname.setdefault(_en(_v.get('typeName') or _v.get('name')), _k)
def T(n): return _byname.get(n)
def A(n):
    t = T(n)
    if t is None: raise KeyError(f'no SDE type named {n!r}')
    return {aname(x['attributeID']): x['value'] for x in td[t]['dogmaAttributes']}
def reqs(t):
    """Direct required skills (requiredSkill1-6) -- what pyfa's requiresSkill() checks."""
    a = {x['attributeID']: x['value'] for x in td.get(str(t), {}).get('dogmaAttributes', [])}
    return {int(a[i]) for i in (182, 183, 184, 1285, 1289, 1290) if i in a}

def pyfa_removed_types():
    """Type ids the SDE has but pyfa's database does not offer (db_update.py post-processing, v2.69.2):
      * boosters whose boosterLastInjectionDatetime is before the data dump (expired event boosters):
        DELETED from the database ("Remove boosters which were expired at the time data dump was generated");
      * items named like '%abyssal%' / '%mutated%' / '%_PLACEHOLDER%' and the four Lux Drifter weapons:
        unpublished (except Abyssal Ore Processing, Mutated Drone Specialization, Asteroid Mining Crystals),
        so pyfa's EFT import (service/port/shared.py fetchItem) refuses them.
    The dump time is staticdata/phobos/metadata.0.json 'dump_time'. Added v2026.10.14.13 (LESSON #32): Erik's
    pyfa dropped Strokar Booster VI (last injection 2026-08-26, dump 2026-10-06) from an EFT paste."""
    import datetime
    meta = json.load(open(os.path.join(PYFA_SRC, 'staticdata', 'phobos', 'metadata.0.json')))
    dump = int(next(x['field_value'] for x in meta if x['field_name'] == 'dump_time'))
    delta = datetime.datetime.fromtimestamp(dump, tz=datetime.timezone.utc) - datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    dumpDays = delta.days + delta.seconds / (24 * 60 * 60)
    lastInj = next(int(k) for k, v in attrs.items() if v.get('name') == 'boosterLastInjectionDatetime')
    out = set()
    for t, v in types.items():
        n = name(t) or ''
        low = n.lower()
        if v.get('published') and (('abyssal' in low or 'mutated' in low or '_placeholder' in low or n in ('Lux Kontos', 'Lux Xiphos', 'Lux Ballistra', 'Lux Kopis'))
                                   and n not in ('Abyssal Ore Processing', 'Mutated Drone Specialization') and 'Asteroid Mining Crystal' not in n):
            out.add(int(t))
        if cat(t) == 20 and v.get('published'):   # the query filters Item.published
            for a in td.get(str(t), {}).get('dogmaAttributes', []):
                if a['attributeID'] == lastInj and a['value'] < dumpDays: out.add(int(t))
    return out
