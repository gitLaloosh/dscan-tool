# Sub-cap sweep #3 — findings (2026-10-08)

Pulled 12 more fresh, Abyssal-free real killmails from zKillboard, covering hull
classes not yet exercised by sweeps #1/#2: HACs not yet checked (Deimos,
Vagabond, Sacrilege), Combat/Force Recon ships (Pilgrim, Curse, Arazu, Rapier),
an Amarr Command Ship (Absolution), an interceptor (Crusader), two T1
destroyers (Catalyst, Thrasher), and a stealth bomber (Manticore). Ran each
through the tool's own `buildLossTally()` + `estimateHpAndDps()` pipeline (no
reimplementation). Raw data + per-hull tool output saved in
`sweep4_payload.json` / `sweep4_results.json` for the record.

## Finding #1 (CONFIRMED BUG, root-caused, fix identified — not yet applied):
## Bomb Launchers get misclassified as a sustained missile weapon and inflate DPS massively

The Manticore kill (killmail 138990812) came back with `dpsFixed: 3533` —
suspiciously high for a 3-torpedo-launcher bomber. Breaking it down via the
tool's own `confirmedAmmoBreakdown` showed why: **2980 of the 3533 DPS (84%)
is attributed to a single "Concussion Bomb" loaded in 1 Bomb Launcher I**,
while the 3 actual Torpedo Launchers (loaded with Caldari Navy Scourge
Torpedo) only contribute 553 DPS combined — a more plausible number on its
own.

Root cause, confirmed in the code (`dscan-tool.html`):
```js
function weaponCategoryFromGroup(groupName){
  const g = (groupName || '').toLowerCase();
  if(g.includes('missile launcher') || g.includes('rocket launcher') || g.includes('bomb launcher')) return 'missile';
  ...
}
```
EVE's own SDE group name for a Bomb Launcher is **"Missile Launcher Bomb"**
(confirmed via live ESI: type 27914 "Bomb Launcher I" → group_id 862 → group
name "Missile Launcher Bomb") — not "Bomb Launcher" as the code's own comment-
intent assumed. `"missile launcher bomb".includes("missile launcher")` is
true, so every Bomb Launcher is caught by the FIRST clause and classified as
an ordinary `'missile'`-category variable weapon, identically to a real
Torpedo/Cruise/Heavy Missile Launcher. From there it gets the full missile
treatment: `MAX_MISSILE_DAMAGE_MULT` (missile skill + Warhead Upgrade, 1.10 ×
1.25 = 1.375×), `MAX_MISSILE_ROF_MULT`, and this fit's 2x Ballistic Control
System II (which *do* apply their dmgMult/rofMult to the 'missile' category
generically) all get layered onto the bomb's raw 5800-damage warhead, then
that per-shot number is divided by the Bomb Launcher's own 10-second cycle
time (attribute 51) as if it were a sustained-fire weapon.

This is wrong on two independent counts, both confirmable from basic EVE
mechanics without needing a pyfa cross-check: (1) **bombs are not affected by
any missile skill, Warhead Upgrade, or Ballistic Control System** in real EVE
— their damage is fixed, unmodified by any of those bonuses; (2) a Bomb
Launcher does not fire continuously — it launches one bomb that travels,
explodes once, and the launcher (and in practice every bomb launcher the
pilot has active, server-side) is subject to a long-shared disable timer, so
treating its raw per-shot damage as a steady "damage ÷ cycle-time" DPS stream
overstates its real contribution to sustained threat by a huge margin.

**Proposed fix (not yet applied, flagged for the user's go-ahead):** exclude
groups matching `/bomb/` from the `weaponCategoryFromGroup` "missile" bucket
(check group name order more carefully — "bomb" appears in "Missile Launcher
Bomb" but a plain substring exclusion for `/bomb/` before the missile-launcher
check would fix it cleanly), and likewise exclude "Bomb" from
`ammoCategoryFromGroup`'s missile bucket. Simplest correct behavior for a
threat-assessment tool: treat Bomb Launchers as contributing ~0 to sustained
`dpsFixed` (same treatment Probe Launchers already get, bug-class #17c) rather
than inventing a burst-damage model — bombs are a situational alpha tool, not
part of a ship's sustained DPS output, and any value this tool bolts on for
"one bomb's worth of burst" would need its own (currently nonexistent)
burst-vs-sustained UI distinction to be meaningful.

## Finding #2 (likely real, extends the already-known bug-class #17a gap):
## 5 more hulls confirmed to carry a genuine damage/resist bonus with no `SHIP_ROLE_BONUS` entry

Checked (via everef.net SDE-backed trait text, same method as bug-class #17a)
every hull in this batch that actually fired a weapon on its kill. None of
Deimos (12023), Vagabond (11999), Sacrilege (12019), Absolution (22448), or
Crusader (11184) appear as a `SHIP_ROLE_BONUS` key, and all five carry a real,
nonzero, per-level skill bonus:

| Hull | Skill | %/level | At V | Type restriction |
|---|---|---|---|---|
| Deimos (HAC) | Gallente Cruiser | 5% dmg | +25% | Medium Hybrid Turret |
| Deimos (HAC) | Heavy Assault Cruisers | 7.5% dmg | +37.5% | Medium Hybrid Turret |
| Vagabond (HAC) | Minmatar Cruiser | 5% RoF | +25% | Medium Projectile Turret |
| Vagabond (HAC) | Heavy Assault Cruisers | 5% dmg | +25% | Medium Projectile Turret |
| Sacrilege (HAC) | Amarr Cruiser | 5% dmg | +25% | **HM/HAM only** (not RLML) |
| Sacrilege (HAC) | Amarr Cruiser | 5% all armor resist | +25% | n/a (resist) |
| Sacrilege (HAC) | Heavy Assault Cruisers | 7.5% RoF | +37.5% | RLML/HM/HAM |
| Absolution (Command Ship) | Command Ships | **20% dmg** | **+100%** | Medium Energy Turret |
| Absolution (Command Ship) | Amarr Battlecruiser | 4% all armor resist | +20% | n/a (resist) |
| Crusader (Interceptor) | Amarr Frigate | 10% dmg | +50% | Small Energy Turret |

Also checked Catalyst (16240) and Thrasher (16242) — both T1 destroyers, on
the theory that T1 hulls "shouldn't" have intrinsic damage bonuses. That
theory was WRONG for Thrasher: Minmatar Destroyer skill gives Thrasher a real
5%/level (+25% at V) Small Projectile Turret damage bonus, also missing from
`SHIP_ROLE_BONUS`. Catalyst's own Gallente Destroyer skill bonuses (tracking
speed + falloff only) genuinely carry no damage component, so Catalyst's
absence from the table is correct, not a gap — worth noting as a reminder not
to assume a whole ship class is exempt without checking each hull.

Combined with bug-class #17a's original 7 hulls (Zealot, Cerberus, Muninn,
Nighthawk, Broadsword, Rokh, Vindicator), this sweep brings the confirmed
missing-bonus count to **12 individual hulls across HAC/Command
Ship/HIC/Battleship/Interceptor/Destroyer classes**, strongly reinforcing that
the earlier 340-ship audit (bug-class #7) systematically missed entire T2
cruiser-line ship classes (every HAC checked so far except Ishtar is missing
its entry) rather than a handful of stragglers. Still not implemented in
`dscan-tool.html` — worklist, pending the user's go-ahead (likely a
dedicated "HAC class" + "Command Ship class" implementation pass, each with
its own pyfa cross-check per the Marauder/Bastion work's template).

## Everything else

Pilgrim, Arazu, and Curse (Combat/Force Recon ships) correctly showed 0
turret DPS (drones only) — confirmed from the kills that none of the three had
an actual weapon fitted (consistent with their usual EWAR/neut fleet role, not
a bug). Rapier showed the same already-documented bug-class #17c cosmetic
Probe-Launcher miscount (1 "unmatched weapon" = its Expanded Probe Launcher I,
contributing correctly 0 DPS). Vagabond, Sacrilege, Deimos, Catalyst,
Thrasher, Absolution, and Crusader all produced DPS/EHP numbers in a plausible
range for their hull/fit (no crashes, no impossible numbers) aside from the
missing-bonus gap documented above. None of these 12 fits have pyfa numbers
yet — raw data is saved for whoever picks this up next; treat as a worklist,
not a confirmed-and-pyfa-verified-exact-magnitude list (except Finding #1,
which needed no pyfa check — the mechanism is confirmed directly from basic,
uncontroversial EVE game mechanics plus the tool's own code and ESI's group
name).
