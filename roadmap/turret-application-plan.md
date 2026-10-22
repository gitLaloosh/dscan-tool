# Plan: how much of their damage actually lands (turret application)

Status: **PROPOSAL** (2026-10-22), waiting for Erik's decisions in section 4.
Backlog: "Turret damage application" (DEVIATIONS.md: "turret tracking application"; architecture memory:
"turret-side damage application, needs attacker tracking + assumed range").

---

## 1. Problem

The Firepower card shows a target's raw DPS, and its turrets' optimal and falloff. It doesn't show how much
of that DPS reaches a smaller or faster ship, or one fighting outside their optimal. For the tool's purpose
("how do I beat this ship?") that is often the deciding question:

- Can I get under their guns? (Close orbit, high transversal: big turrets miss.)
- Can I kite them? (Outside optimal + falloff, their hit chance collapses.)
- Will my sig tank their guns? (A frigate against Large turrets.)

Missiles already account for application. Since v2026.10.14.27 the missile pick uses the target's
signature and speed with All V skills. Turrets and drones don't.

## 2. How pyfa does it (primary source: pyfa v2.69.3)

pyfa doesn't put one "applied DPS" number on a fit. Application lives in its **Damage graph**
(`graphs/data/fitDamageStats/calc/application.py`). The user sets the distance, the target's speed, sig
and angle, and the attacker's speed and angle. The default target is the "ideal target": no signature limit,
not moving.

The formulas, per weapon (`getApplicationPerKey`):

| Weapon | pyfa function | Inputs |
|---|---|---|
| Turrets | `_calcTurretChanceToHit` x `_calcTurretMult` | range factor `0.5 ** ((max(0, d - optimal) / falloff) ** 2)` (`eos/calc.py calculateRangeFactor`); tracking factor `0.5 ** ((angular x optimalSigRadius / (trackingSpeed x tgtSig)) ** 2)`; angular = transversal / (atkRadius + d + tgtRadius); damage multiplier with 1% wrecking hits (x3) and a (0.01 + cth) / 2 + 0.49 average |
| Missiles | `getLauncherMult` | full damage inside the shorter flight distance, pyfa's chance between the two flight distances, 0 beyond; then `min(1, S/E, (S/E x Ve/Vt) ** drf)` (the tool already has this) |
| Vorton | `getVortonMult` | range factor x the missile factor |
| Smartbombs | `getSmartbombMult` | inside the blast radius or not |
| Drones | `getDroneMult` | out of drone control range or lock range = 0. If the drone is faster than the target, it is assumed to always hit (pyfa's "auto" mode). Otherwise turret maths from the drone's own tracking, optimal, falloff and speed |
| Fighters | `getFighterAbilityMult` | per ability |

Everything beyond the attacker's **lock range** is 0, except FoF missiles and bombs.

What the tool already has: turret optimal and falloff (generated weapon-range table), missile application,
ship radius (attr 162), lock range, drone control range.

What's missing:

- **Turret tracking speed.** pyfa has 78 handlers on `trackingSpeed`. They're carried by ammo (184 charges,
  e.g. Scorch, Barrage), tracking computers and enhancers with scripts, 81 hulls, implants and boosters,
  T3 subsystems and the Motion Prediction skill. The handler recorder and `gen_weapon_range_table.py`
  already capture exactly this shape of row (optimal and falloff), so tracking would be one more target.
- `optimalSigRadius` (attr 620). No handler modifies it, so it's read as is.
- **Drone speed, tracking, optimal and falloff** after skills and modules. Today the drone pick uses fixed
  travel speeds per drone size.

## 3. Proposed behaviour

### Engine (Phase 1, no visible change)

- Generate turret tracking from pyfa's handlers: the same generator, rows, verification and PYFA CORE lock as
  weapon range.
- A new PYFA CORE section `application`: a line-for-line port of the functions above. It's verified by
  lifting pyfa's own functions unmodified (via `ast`, as `check_missile_range.py` does) and comparing every
  golden fit over a grid of distance x target speed x sig x angle.
- Result field per weapon: `application(profile, distance)`. Applied DPS = sum of each weapon's DPS x its
  multiplier, the same way pyfa sums them.

### Display (Phase 2)

On the Firepower card, under the raw DPS: **"Their damage on you"**. A small DPS-vs-distance chart from 0
to their reach, with two lines (see D3), plus one headline number at the distance you pick. It has hover,
like pyfa's graph.

### Optional (Phase 3)

The reverse direction, **your guns vs them**: turret ammo picks that account for range and tracking, like
the missile pick does today. This is also the groundwork for the "counter-fit" roadmap idea (time to kill =
your applied DPS vs their tank, and theirs vs yours).

## 4. Decisions needed (Erik)

| # | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Which direction first? | (a) **their guns vs you** (threat); (b) your guns vs them; (c) both together | **(a)**, then (b) as Phase 3. (a) answers the threat question with nothing assumed about your weapons. |
| D2 | Where do "your" sig, speed and radius come from? | (a) **a fit you've analyzed, saved as "my ship"** (one click in the Fit Analyzer, remembered in your browser); (b) class presets (frigate / cruiser / battleship); (c) typed in by hand | **(a)**, with (b) as the fallback until a ship is set. With (a) the numbers come from the tool's own pyfa-exact stats, MWD or AB included. |
| D3 | What movement do we assume? | (a) **two lines: you sitting still and you orbiting at full speed** (90°, the worst case for them); (b) orbiting only; (c) a speed slider | **(a)**. Still = their range-only damage, orbiting = with tracking. The gap between the lines is what speed tanking buys you. |
| D4 | Prop module for "you" | (a) **your fit's prop active** (AB or MWD, with the MWD's sig bloom); (b) cruising | **(a)**. Real orbits run the prop, and the MWD's sig bloom is exactly the trade-off the chart should show. |
| D5 | Their drones and fighters | (a) **include now** (needs drone speed and tracking: more engine work); (b) turrets, missiles, Vorton and smartbombs first, drones in a follow-up | **(b)**. Drone DPS keeps showing raw until then, labelled. |
| D6 | Pilot Analyzer as well as Fit Analyzer? | (a) **both**; (b) Fit Analyzer only | **(a)**. Same engine; killmail fits get the same card. |

## 5. Risks and how they're handled

- **Assumptions in the numbers.** Application depends on inputs nobody can know (your exact movement). The
  card names its assumptions on the chart: profile, still or orbiting, prop on. Raw DPS stays visible.
- **Lock range.** Beyond their lock range pyfa counts 0. The chart shows it as a cliff, with the reason on
  hover.
- **Sig from a saved fit goes stale** if you change that fit later. The profile stores the numbers and the
  fit name, and the card says which fit it used.

## 6. Verification plan (`LESSONS_LEARNED.md` order)

1. Recorder survey of every `trackingSpeed` handler. The generated table must reproduce the handler set
   exactly (`gen_weapon_range_table.py` reports "up to date").
2. `tools/independent_checks/check_application.py`: pyfa's own application functions, lifted unmodified,
   vs the tool, over every golden fit x a grid (distance 0 to 2x reach, target speed 0 to 3,000 m/s, sig
   20 to 5,000 m, angle 0 / 45 / 90°). Must print 0 mismatches. It goes in the update-check chain.
3. `compare_fit_stats.py` gains tracking speed per turret, compared with the oracle at 1e-6.
4. Constructed golden fits that fail on the old build:
   - a Megathron with 425mm Rails vs a frigate profile at 5 / 20 / 40 km;
   - a Rifter with autocannons and a Tracking Enhancer + Barrage;
   - a lock-range cliff case.
5. A pyfa screenshot check from you: the Damage graph for one test fit with a set target profile. We read
   two points off it.
6. Page checks: the chart at 1440 / 375 px, profile save and reload, no sideways scroll.

## 7. Rough size

| Phase | Size |
|---|---|
| 1 — tracking table + application core + checks | Medium to large (one or two deliveries) |
| 2 — "Their damage on you" chart + "my ship" profile | Medium |
| 3 — your guns vs them (optional) | Medium |
| Drones / fighters follow-up (if D5 = b) | Medium |
