"""Drones in space (v2026.10.13.23). Hand-typed pyfa rules, SDE values.
Drone DPS = sum(damage) x drone damageMultiplier x Drone Interfacing V x size
skill V x racial Specialization V (each skill only for drones requiring it,
pyfa Effect1730/6663) / (speed / 1000). Limits: Drones skill V = 5 drones in
space (maxActiveDroneBonus x5), ship droneBandwidth vs droneBandwidthUsed.
Drones in space are granted hardest-hitting first; anything over a limit is
refused. Non-combat drones use bandwidth and a drone slot too."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *
DI = SK('Drone Interfacing', 'damageMultiplierBonus')
SIZE = {'Heavy Drone Operation': SK('Heavy Drone Operation', 'damageMultiplierBonus'), 'Medium Drone Operation': SK('Medium Drone Operation', 'damageMultiplierBonus')}
GDS = SK('Gallente Drone Specialization', 'damageMultiplierBonus')
MAXD = sk('Drones', 'maxActiveDroneBonus') * 5
BW = A('Abaddon')['droneBandwidth']
def dps(n):
    a = A(n); r = {name(s) for s in reqs(T(n))}
    if not a.get('speed'): return 0.0
    m = DI * GDS ** ('Gallente Drone Specialization' in r) * [v for k, v in SIZE.items() if k in r][0]
    return sum(a.get(k) or 0 for k in ('emDamage', 'thermalDamage', 'kineticDamage', 'explosiveDamage')) * a['damageMultiplier'] * m / (a['speed'] / 1000)
BAY = {'Ogre II': 3, 'Hammerhead II': 5, 'Hornet EC-300': 2}
def launch(req):
    order = sorted(BAY, key=lambda n: -dps(n)); used = cnt = 0; tot = 0.0; refused = 0
    for n in order:
        want = min(BAY[n], req.get(n, 0)) if req is not None else (BAY[n] if dps(n) else 0)
        k = min(want, MAXD - cnt, int((BW - used) // A(n)['droneBandwidthUsed']))
        if req is not None and k < want: refused += 1
        cnt += k; used += k * A(n)['droneBandwidthUsed']; tot += k * dps(n)
    return round(tot, 1), cnt, used, refused
print('per drone: Ogre II', round(dps('Ogre II'), 2), 'Hammerhead II', round(dps('Hammerhead II'), 2), '| max drones', MAXD, 'bandwidth', BW)
for lbl, req in (('default', None), ('{Ogre 1, Hammerhead 3, Hornet EC-300 1}', {'Ogre II': 1, 'Hammerhead II': 3, 'Hornet EC-300': 1}),
                 ('{Ogre 3, Hammerhead 1}', {'Ogre II': 3, 'Hammerhead II': 1}), ('{Hammerhead 5, Hornet EC-300 2}', {'Hammerhead II': 5, 'Hornet EC-300': 2})):
    print(lbl, '-> dps, in space, bandwidth, refused:', launch(req))
