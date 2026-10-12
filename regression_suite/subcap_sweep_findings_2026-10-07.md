# Sub-cap representative sweep — findings (2026-10-07)

## Method

Pulled 10 real, recent (all within the last day, Oct 7 2026) PvP losses from zKillboard across a representative spread of sub-cap hull classes — frigate (interceptor), destroyer (interdictor, tactical destroyer), cruiser (T1, HAC, T3 Strategic Cruiser), battlecruiser-class attack cruiser, logistics cruiser, and battleship (T1 faction, Marauder). For each ship, picked the most recently-killed loss with the highest count of actually-fitted modules (to avoid cargo-stuffed "loot piñata" losses), pulled the full killmail from ESI, and ran it through dscan-tool.html's **own** `buildLossTally()` + `estimateHpAndDps()` pipeline (the exact same code path the tool uses for its live "pilot fit history" feature) inside a Node `vm` sandbox, with a trimmed ESI dataset (219 item/ship types + 102 groups, filtered to only the dogma attributes the tool's formulas read) standing in for live `fetch()` calls.

No tool code was changed for this pass — this was a read-only sweep to surface candidates for you to check against pyfa.

Ships swept: **Hecate, Sabre, Loki, Gila, Orthrus, Stabber, Malediction, Scimitar, Vargur, Machariel.**

## Summary table

| Ship | Fit (zKillboard) | Shield/Armor/Hull EHP | Total EHP | Raw HP | DPS (confirmed+drone) | Weakest |
|---|---|---|---|---|---|---|
| Hecate | [138985442](https://zkillboard.com/kill/138985442/) | 1,548 / 1,861 / 3,109 | 6,518 | 2,938 | 296 | em 54% |
| Sabre | [138985791](https://zkillboard.com/kill/138985791/) | 4,805 / 1,636 / 1,555 | 7,996 | 3,750 | 285 | kin 53% |
| Loki | [138985490](https://zkillboard.com/kill/138985490/) | 9,620 / 6,291 / 4,975 | 20,886 | 8,250 | 185 | exp 50% |
| Gila | [138983011](https://zkillboard.com/kill/138983011/) | 7,705 / 4,074 / 4,646 | 16,424 | 9,863 | 683 (460 drone) | em 76% |
| Orthrus | [138984898](https://zkillboard.com/kill/138984898/) | 6,484 / 4,967 / 6,530 | 17,981 | 9,163 | 641 (70 drone) | therm 54% |
| Stabber | [138985003](https://zkillboard.com/kill/138985003/) | 5,673 / 2,832 / 4,042 | 12,548 | 5,250 | 517 | exp 48% |
| Malediction | [138985538](https://zkillboard.com/kill/138985538/) | 663 / 1,795 / 1,322 | 3,780 | 1,625 | 37 | em 47% |
| Scimitar | [138985080](https://zkillboard.com/kill/138985080/) | 49,584 / 4,765 / 4,459 | 58,808 | 16,706 | 59 (59 drone) | kin 40% |
| Vargur | [138983121](https://zkillboard.com/kill/138983121/) | 28,483 / 18,216 / 21,455 | 68,155 | 28,125 | 1,305 (73 drone) | exp 49% |
| Machariel | [138983888](https://zkillboard.com/kill/138983888/) | 17,676 / 266,713 / 16,951 | 301,341 | 80,171 | 819 (73 drone) | em 43% |

Shield/Armor/Hull/Total figures are **effective HP** (raw HP ÷ average post-resist resonance), matching how the tool already reports these fields elsewhere — `rawHP` is the pre-resist sum, shown alongside for reference.

Full fit lists for every ship (so you can rebuild any of these exactly in pyfa) are in `ship_details.txt`, attached alongside this report.

## Two results that looked wrong at first glance but checked out

**Machariel armor EHP = 266,713.** This fit is a double-plate "brick": 2× Imperial Navy 1600mm Steel Plate + 4 armor-tank low slots (Coreli A-Type Multispectrum Coating + 3 single-damage-type X-Type hardeners) + 3× Large Trimark Armor Pump II, filling all 6 low slots. Verified against primary sources:
- Machariel's Battleship role bonus really is **+50% to Armor Plates' own flat-HP attribute** (confirmed via everef.net's type traits page: "50% bonus to Hull Upgrades hitpoints" role bonus).
- Multiple Trimark rigs of the same type really do **not** stacking-penalize each other — confirmed via EVE University's stacking-penalty reference page: "Shield / armor / hull hit points: no [stacking penalty]" (only *resistances* from hardeners are stacking-penalized, which this fit also has four of, dragging average armor resonance down to ~0.21 and inflating the EHP division).
- Hand-recomputing the formula by hand lands within ~0.01% of the tool's output.

So the number is mathematically consistent with the tool's existing (already pyfa-cross-checked on other golden fits) EHP methodology — it's just an unusually extreme real loss (a very over-tanked, probably non-meta brawler fit). Still worth a quick pyfa sanity-check given how large it is.

**Sabre shows 7 confirmed autocannons.** Looked suspicious since most interceptor/destroyer-class ships only have 3-4 highs, but everef.net confirms the Sabre genuinely has **8 high slots** (7 turret hardpoints + 1 launcher hardpoint), so "7× 150mm AutoCannon II + 1× Interdiction Sphere Launcher" is a fully legal, real fit. No issue.

## Two likely real gaps worth your pyfa check

**1. Loki's Offensive subsystem rate-of-fire bonus is not applied.**

The swept Loki fit has 5× Republic Fleet Heavy Assault Missile Launcher loaded with Caldari Navy Inferno HAM, plus the **Loki Offensive - Launcher Efficiency Configuration** subsystem fitted. everef.net's traits page for that subsystem (type 45608) confirms it grants, per Minmatar Offensive Systems skill level (max 5):
- **10% bonus to RLML/HML/HAM rate of fire per level → 50% at max skill**
- 5% missile velocity per level, 5% missile explosion velocity per level
- Role bonus: 25% PG/CPU fitting reduction for those launchers

dscan-tool.html's `SUBSYSTEM_ROLE_BONUS` table currently has exactly **one** entry (`'45598'`, the Legion's energy-damage subsystem). It has no entry for the Loki's offensive subsystem, so this 50% RoF bonus is silently dropped — the tool's own `estimateHpAndDps()` code already *supports* subsystem-granted `'rof'` bonuses (the same per-category loop that applies `SHIP_ROLE_BONUS` 'rof' entries would apply this too, if it were in the table), it's just missing the data entry. A 50% RoF bonus roughly doubles DPS on top of whatever Ballistic Control Systems already contribute, so this Loki's reported 185 DPS is likely a significant undercount — possibly closer to 300-370 once the subsystem bonus is included.

This is very likely NOT limited to this one subsystem — Tengu, Proteus, and the other Legion/Loki offensive subsystem variants almost certainly have their own uncaptured role bonuses too, since only one of ~12+ relevant subsystems has ever been added to the table. Worth a dedicated follow-up pass auditing all T3 Strategic Cruiser subsystems via everef.net rather than a one-off patch.

**To verify in pyfa:** fit a Loki with Loki Offensive - Launcher Efficiency Configuration, 5× Republic Fleet Heavy Assault Missile Launcher (Caldari Navy Inferno HAM loaded), 2× Abyssal Ballistic Control System, at all-5 skills, and compare pyfa's displayed DPS to our tool's 185.

**2. Marauders' Bastion Module all-resist bonus is never read.**

The swept Vargur fit has a **Bastion Module I** fitted (a high-slot module restricted to Marauders). everef.net confirms Bastion gives **+30% to every shield/armor/structure resistance** (all 4 damage types, all 3 layers) while active, plus +60% armor repair/shield boost amplifier and some weapon falloff/optimal bonuses.

dscan-tool.html's resistance-scanning loop only walks `defensiveGroups = ['Mid slots', 'Low slots', 'Rigs', 'Subsystems']` — **it never looks at High slots**. Since Bastion Module is a High-slot item, its resistance attributes (the same `267`-`274` / `974`-`977` attribute IDs a Damage Control carries) are never read at all, even though the code's existing Damage-Control-handling logic would pick them up correctly if the item were just included in the scan. This silently drops a +30% all-resist bonus for every Marauder (Vargur/Golem/Kronos/Paladin) fit that includes Bastion — on top of whatever Damage Control the ship already carries.

**To verify in pyfa:** fit the same Vargur (shown in the table above) with Bastion Module active and compare its EHP to our tool's 68,155; then compare again with Bastion toggled off, to isolate the size of the gap.

## Everything else

Hecate, Gila, Orthrus, Stabber, Malediction and Scimitar all came back internally consistent — weapon counts, ammo matching, and drone-bay handling all lined up with their real fits, no red flags. Full breakdowns are in `ship_details.txt` if you want to spot-check any of them in pyfa too.

## Files

- `ship_details.txt` — full per-ship fit lists + results for all 10 ships (module names resolved, not just type IDs)
- `sweep_results2.json` — raw JSON output (tally + estimateHpAndDps result) for all 10 ships, for anyone who wants to dig further
