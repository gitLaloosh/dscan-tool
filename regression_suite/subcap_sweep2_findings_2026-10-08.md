# Sub-cap sweep #2 — findings (2026-10-08)

Pulled 12 fresh, Abyssal-free real killmails from zKillboard (one per hull, picked
to cover ship classes not yet exercised by this project's regression suite) and
ran each through the tool's own `buildLossTally()` + `estimateHpAndDps()`
pipeline (no reimplementation — the actual code path). None of the 12 threw
errors, and none of the 12 produced obviously-impossible numbers (no negative
HP, no infinite DPS, etc.). The real finding is a **systemic coverage gap**, not
a crash or a one-off miscalculation: live ESI confirms that most of these hulls
carry a genuine, nonzero intrinsic damage/RoF/resistance bonus that has **no
entry at all in `SHIP_ROLE_BONUS`**, so the tool is very likely under-stating
their DPS and/or resistances. None of this has been cross-checked against pyfa
yet — these are flagged candidates, not confirmed-and-fixed bugs, consistent
with this project's primary-source-before-fixing standard.

## Hulls tested

Falcon, Zealot, Nighthawk, Broadsword, Confessor, Guardian, Muninn, Vindicator,
Cerberus, Basilisk, Tengu, Rokh — one real kill each (zKillboard killmail IDs
in `suspect_fits_2026-10-08.json`), screened to exclude any fit containing an
Abyssal/mutaplasmid item per the standing instruction.

## Finding #1 (likely real, not yet fixed): Heavy Assault Cruisers, Command
Ships, and some Battleships have NO `SHIP_ROLE_BONUS` entry at all

Checked: none of these 12 hull type IDs (11957 Falcon, 12003 Zealot, 22470
Nighthawk, 12013 Broadsword, 34317 Confessor, 11987 Guardian, 12015 Muninn,
17740 Vindicator, 11993 Cerberus, 11985 Basilisk, 29984 Tengu, 24688 Rokh)
appear as a key in `SHIP_ROLE_BONUS`. For the ones that actually matter (the
ship is fitted with the weapon type the bonus targets), live ESI confirms a
real, nonzero, per-skill-level bonus exists:

| Hull | Fitted weapon (confirmed from the kill) | ESI-confirmed unmodeled bonus | Magnitude (ESI, per level) |
|---|---|---|---|
| Zealot | Energy Weapon (laser) | `eliteBonusHeavyGunshipLaserDmg2` — turret damage | 5%/level (attr 693) |
| Vindicator | Hybrid Weapon (blaster) | `shipHybridDmgPirateBattleship` — turret damage | 37.5 (attr 793; not yet reconciled to a %/level convention — flagged, not applied) |
| Rokh | Hybrid Weapon (blaster) | `shipBonusEmShieldResistanceCB2` (+3 sibling effects, Exp/Kin/Therm) — shield resist | -4%/level (attr 501), all 4 damage types |
| Cerberus | Heavy Assault Missile Launcher II, **Scourge** (kinetic) ammo | `shipMissileKineticDamageCC` — missile damage, kinetic-only (matches loaded ammo exactly) + `eliteBonusHeavyGunshipHeavyMissileLauncherRof2`/`...AssaultMissileLauncherRof2` — RoF | 2.5%/level dmg (attr 487); RoF magnitude not yet pulled |
| Nighthawk | Heavy Assault Missile Launcher II, **Scourge** (kinetic) ammo | `shipBonusHeavyAssaultMissileKineticDamageCBC1`/`...HeavyMissileKineticDamageCBC1` — kinetic missile damage (matches loaded ammo exactly) + `eliteBonusCommandShipHAMRoFCS1`/`...HMRoFCS1` — RoF | 10%/level dmg (attr 743); RoF -7.5 (attr 1000, convention not yet reconciled) |
| Broadsword | Projectile Weapon (autocannon/artillery) | `shipProjectileDmgMC2` — turret damage + `shipPTurretSpeedBonusMC` — RoF | not yet pulled |
| Muninn | (this specific kill: Rapid Light Missile Launcher, an unusual fit) | `shipBonusShieldArmorResonanceMC` — shield/armor resist (weapon-type-independent, still applies) | not yet pulled |

Guardian, Basilisk, and Falcon are NOT affected by this — confirmed from the
kill data that none of the three had any actual weapon fitted (Guardian/Basilisk
are dedicated remote-rep logistics boats; Falcon is a pure ECM/cloak fit), so
their near-zero `dpsFixed` (79, 0, 0 respectively) is correct, not a bug.

This strongly suggests the earlier "340-ship `SHIP_ROLE_BONUS` audit" (see
project memory, bug-class #7) missed entire ship *classes* — Heavy Assault
Cruisers and Command Ships in particular — rather than just a handful of
individual hulls. Tengu wasn't affected by this specific gap (T3 Cruisers
correctly have no `SHIP_ROLE_BONUS` of their own — their bonus lives on the
fitted subsystem, which IS modeled).

**Not yet done, on purpose:** none of these magnitudes have been converted
into a `SHIP_ROLE_BONUS` entry yet. Several of the raw ESI values (e.g.
Vindicator's 37.5, Rokh's RoF-looking entries) don't obviously fit the simple
"X%/level, assume level V" convention the rest of the table uses, and this
project's standard is to pin the exact mechanism (and ideally get a pyfa
cross-check) before writing a number into the table — the Marauder/Bastion
work earlier this session is the template for how to do that properly. Fixing
this properly is its own follow-up task, likely one hull-class at a time.

## Finding #2 (structural, likely real, not yet modeled at all): T3 Destroyer
"Mode" mechanic

Confirmed via `grep` that `dscan-tool.html` has **no code at all** referencing
Tactical Destroyer modes (Sharpshooter/Defense/Propulsion Mode) — the only T3D
reference is a slot-size-tier lookup. In real EVE, a Tactical Destroyer's
active Mode module is one of its single biggest damage/resist/speed swings
(e.g. Sharpshooter Mode substantially boosts turret/launcher damage and
falloff/explosion radius; Defense Mode boosts resistances). This specific
Confessor kill happened not to have a Mode module fitted, so it doesn't
directly demonstrate the gap, but the gap is structural and will affect
Confessor, Hecate, Jackdaw, and Svipul fits generally whenever a Mode module
is actually running (which is most of the time in real combat). Flagging this
as a bigger, separate follow-up — it needs its own research pass (confirm the
exact per-mode bonus attributes via ESI, same rigor as everything else in this
project) before any fix.

## Finding #3 (cosmetic, low severity): Probe Launchers (and similar
non-damage "...Launcher"-named utility modules) get miscounted as unresolved
weapons

The Tengu kill's `Sisters Expanded Probe Launcher` (a scan probe launcher, not
a weapon) tripped the code's generic `/turret|launcher|weapon/` regex
fallback classifier and was counted as 1 of `variableWeaponCount`, then
correctly failed to find any damage-dealing "ammo" for it and landed in
`unmatchedWeaponCount` instead. This does **not** affect `dpsFixed` (0 DPS was
correctly NOT added for it) — it's purely a diagnostic miscount
(`unmatchedWeaponCount`/`variableWeaponCount` read as 1/7 instead of 0/6 on
this fit). Worth a small follow-up fix (exclude the Probe/Survey/Salvager
Launcher-ish groups from the generic weapon-classification fallback) but it's
not a threat-assessment accuracy bug.

## Everything else

Shield/armor/hull HP totals across all 12 looked plausible for their hull
classes (no implausible outliers), and no fit threw an error or produced a
nonsensical number. Full raw data (killmail, ESI types/groups, the tool's own
tally, and its full result object) for all 12 is saved in
`suspect_fits_2026-10-08.json` for whoever picks this up next — these are
**not** in `golden_fits.json` (no pyfa numbers exist for them yet), so they
won't be auto-checked by the regression suite; treat them as a worklist, not
a confirmed-bug list.

## Follow-up: exact magnitudes pinned (2026-10-08, via everef.net's SDE-backed "Type Bonuses" trait text — the same methodology-note fallback used earlier in this project when ESI's own effect data can't answer scope/magnitude questions)

Corrects/replaces the "not yet pulled" placeholders above. Two things worth
flagging about the research itself: Cerberus's missile damage bonus turned
out to be universal (all 4 damage types), not kinetic-restricted as the ESI
effect *name* (`shipMissileKineticDamageCC`) suggested — Cerberus actually
carries one such effect per damage type (899/5383/5384/5385, one each for
kin/em/therm/exp), which together implement an untyped bonus, not a
kinetic-only one. And Muninn turned out to be a **missile** HAC, not
projectile as I initially assumed from memory — its own ESI description
("laden with missile hardpoints") confirms this, and the swept kill's
Rapid Light Missile Launcher fit is the NORMAL configuration for this hull,
not an unusual one as the first pass of this report said.

| Hull | Skill | %/level | At level V | Type restriction | Source of bonus |
|---|---|---|---|---|---|
| Zealot | Amarr Cruiser | 7.5% dmg | +37.5% | none (energy) | skill |
| Zealot | Heavy Assault Cruisers | 5% dmg | +25% | none (energy) | skill |
| Cerberus | Caldari Cruiser | 2.5% dmg | +12.5% | none (all 4 types) | skill |
| Cerberus | Heavy Assault Cruisers | 5% RoF | +25% | none (RLML/HML/HAM) | skill |
| Muninn | Minmatar Cruiser | 5% dmg | +25% | none (LML/HML/HAM) | skill |
| Muninn | Minmatar Cruiser | 3% all shield+armor resist | +15% | n/a (resist) | skill |
| Muninn | Heavy Assault Cruisers | 5% RoF | +25% | none (LML/HML/HAM) | skill |
| Nighthawk | Caldari Battlecruiser | 10% dmg | +50% | **kinetic only** (confirmed by trait text itself, not just effect name) | skill |
| Nighthawk | Caldari Battlecruiser | 4% all shield resist | +20% | n/a (resist) | skill |
| Nighthawk | Command Ships | 7.5% RoF | +37.5% | none (HM/HAM) | skill |
| Broadsword | Minmatar Cruiser | 5% dmg | +25% | none (medium projectile) | skill |
| Broadsword | Minmatar Cruiser | 5% RoF | +25% | none (medium projectile) | skill |
| Broadsword | (hull role bonus, not skill) | flat | **+20% all shield resist** | n/a | flat role bonus |
| Rokh | Caldari Battleship | 4% all shield resist | +20% | n/a (resist) | skill |
| Vindicator | (hull role bonus, not skill) | flat | **+37.5% Large Hybrid Turret dmg** | none | flat role bonus |

Not a damage/resist bonus (confirmed irrelevant to this tool's threat-assessment math, skipped): Zealot's/Cerberus's/Muninn's turret-or-missile-velocity/optimal/falloff bonuses, Rokh's optimal-range bonus, Nighthawk's explosion-radius and gang-link/Command-Burst bonuses, Broadsword's falloff and Warp Disruption Field Generator range bonuses, Cerberus's/Vindicator's/Rokh's HP-role-bonus lines (Shield/Hull Upgrades HP role bonus — already handled generically for any ship via the existing `ARMOR_PLATE_ROLE_BONUS_ATTR`/`SHIELD_EXTENDER_ROLE_BONUS_ATTR` mechanism).

All of the above are skill-based bonuses except the two explicitly marked "flat role bonus" (Broadsword's shield resist, Vindicator's hybrid damage), which do not scale with any skill level and would need to be modeled the same way the existing universal Battleship HP role bonus already is (read generically off the ship's own attribute rather than per-level). None of this has been implemented in `dscan-tool.html` yet or cross-checked against a pyfa export — still a worklist pending the user's go-ahead to implement and the usual pyfa verification pass.
