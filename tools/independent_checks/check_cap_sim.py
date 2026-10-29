"""Capacitor simulation (v2026.10.14.1): expected values from pyfa's OWN simulator.

Drain lists are built here by hand (check_capacitor.py's skill rules + SDE values,
pyfa Fit.__generateDrain: fullCycleTime = rawCycleTime + reactivation delay,
capacitorNeed after skills, turrets unstaggered, Capacitor Boosters as injectors
with capNeed = -GJ, clip = floor(module capacity / charge volume), reload attr)
and run through pyfa's eos/capSim.py exactly as Fit.__runCapSim() runs it (via
tools/cap_sim_oracle.py's settings). Nothing here reads index.html."""
import sys, os, json, importlib.util, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = sys.argv[:1]                      # check_capacitor.py reads argv
from check_capacitor import mult, nm
from indep_common import *
spec = importlib.util.spec_from_file_location('capSim', os.path.join(PYFA_SRC, 'eos', 'capSim.py'))
capSim = importlib.util.module_from_spec(spec); spec.loader.exec_module(capSim)

def sim(capacity, rechargeMs, drains):
    s = capSim.CapSimulator(); s.init(drains)
    s.capacitorCapacity = capacity; s.capacitorRecharge = rechargeMs; s.startingCapacity = capacity
    s.stagger = True; s.scale = False; s.t_max = 6 * 3600 * 1000; s.reload = False; s.optimize_repeats = True
    s.run()
    st = (s.cap_stable_low + s.cap_stable_high) / (2 * capacity)
    return ('stable %.1f%%' % min(100, st * 100)) if st > 0 else ('empties at %.1f s' % (s.t / 1000))

def module_drains(items):
    out = []
    for tid, q in items:
        m, a = mult(tid, 'cap'); cap = a.get('capacitorNeed', 0)
        if cap <= 0 or a.get('speed'): continue
        md, _ = mult(tid, 'dur')
        dur = max(a.get('duration', 0), a.get('durationHighisGood', 0)) * md + a.get('moduleReactivationDelay', 0)
        out += [(int(dur), cap * m, 0, False, 0, False)] * int(round(q))
    return out

def injector(module, charge):
    a, c = A(module), A(charge)
    capacity, volume = types[T(module)]['capacity'], types[T(charge)]['volume']   # type fields (ESI attrs 38 / 161)
    return (int(a['duration']), -c['capacitorBonus'], math.floor(capacity / volume + 1e-9), False, a['reloadTime'], True)

CM, CSO = SK('Capacitor Management', 'capacitorCapacityBonus'), SK('Capacitor Systems Operation', 'capRechargeBonus')

# ---- Curse (zKill 139073592 and its cargo-inference clone): 3x Small + 2x Corpum C-Type Medium
# Energy Neutralizer, 2x Tracking Disruptor II, Guidance Disruptor II, Caldari Navy Warp
# Disruptor, Federation Navy 100MN Afterburner, Medium Ancillary Armor Repairer;
# Medium F-RX Compact Capacitor Booster with Navy Cap Booster 800.
items = [(T(n), q) for n, q in [('Small Energy Neutralizer II', 3), ('Corpum C-Type Medium Energy Neutralizer', 2),
         ('Tracking Disruptor II', 2), ('Guidance Disruptor II', 1), ('Caldari Navy Warp Disruptor', 1),
         ('Federation Navy 100MN Afterburner', 1), ('Medium Ancillary Armor Repairer', 1)]]
cu = A('Curse'); cap, rech = cu['capacitorCapacity'] * CM, cu['rechargeRate'] * CSO
d = module_drains(items)
print('Curse drain %.3f GJ/s' % sum(x[1] / (x[0] / 1000) for x in d))
print('Curse with its Capacitor Booster:', sim(cap, rech, d + [injector('Medium F-RX Compact Capacitor Booster', 'Navy Cap Booster 800')]))
print('Curse without boosts:', sim(cap, rech, d))

# ---- Hawk: Medium Ancillary Shield Booster (charged -> no cap) + 1MN Afterburner II
hk = A('Hawk'); cap, rech = hk['capacitorCapacity'] * CM, hk['rechargeRate'] * CSO
ab = module_drains([(T('1MN Afterburner II'), 1)])
asb = module_drains([(T('Medium Ancillary Shield Booster'), 1)])
print('Hawk ASB charged:', sim(cap, rech, ab), '| ASB out of charges:', sim(cap, rech, ab + asb))

# ---- Ishtar (zKill 137694046; golden ishtar_zkb137694046). The owner's older pyfa screenshot:
# stable 40.5%, capDelta +7.12 GJ/s. Republic Fleet Large Cap Battery adds flat capacity (attr67,
# Capacitor Battery effect); both Flux Coils multiply capacity and recharge, NOT penalized
# (pyfa capacitorCapacityMultiply / modifyPowerRechargeRate pass no stackingPenalties).
# Active by default: X-Large C5-L booster + both shield hardeners; Assault DC II defaults online.
ish, bat = A('Ishtar'), A('Republic Fleet Large Cap Battery')
fl2, flc = A('Capacitor Flux Coil II'), A('Mark I Compact Capacitor Flux Coil')
cap = (ish['capacitorCapacity'] + bat['capacitorBonus']) * CM * fl2['capacitorCapacityMultiplier'] * flc['capacitorCapacityMultiplier']
rech = ish['rechargeRate'] * CSO * fl2['capacitorRechargeRateMultiplier'] * flc['capacitorRechargeRateMultiplier']
d = module_drains([(T(n), 1) for n in ('X-Large C5-L Compact Shield Booster', 'Multispectrum Shield Hardener II', 'EM Shield Hardener II')])
peak = 2.5 * cap / (rech / 1000)
use = sum(x[1] / (x[0] / 1000) for x in d)
print('Ishtar capacity %.0f, drain %.2f GJ/s, peak %.2f, net %.2f:' % (cap, use, peak, peak - use), sim(cap, rech, d))
xlc = A('X-Large C5-L Compact Shield Booster')   # no amplifier, no hull or skill bonus to booster amount (check_repairs.py rules)
print('Ishtar shield booster %.1f HP/s' % (xlc['shieldBonus'] / (xlc['duration'] / 1000)))
