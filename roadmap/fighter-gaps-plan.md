# Fighter gaps: carriers assessed accurately

the owner, 2026-10-25: "Ok lets get the fighter gaps closed. Carriers need to be accurately assessed in the tool."
Every number checked against pyfa (eos, `graphs/data/fitDamageStats`), as everywhere in the tool.

## the owner's decisions (2026-10-25)

- **Default launch:** damage first. The hardest-hitting damage squadrons go out within the tubes and class limits,
  then support squadrons fill the tubes left, webs first.
- **Bombs:** off by default (pyfa's default), with a per-type toggle; counted with pyfa's bomb rule when on.
- **Support EWAR:** webs applied as pyfa does (`getProjFighterData`). Neuts, ECM and warp disruption are shown on the EWAR
  card with pyfa's numbers but not applied to the times, the same as module neuts (that stays with the capacitor/neuts
  backlog item).
- **EFT lines:** keep the bay count (`Firbolg I x18` = 18 in the bay, 3 squadrons); pyfa reads one line as one squadron.
- **Ability buttons:** the game's own icons ("can you use the actual fighter ability icons from the game?") with a short
  label ("Icon + short label").
- **Fighter bay:** open by default when the hull can launch what it holds.
- **Weaknesses picks:** rank your fighters too.

## Deliveries

1. **Squadrons and abilities you choose: done in v2026.10.14.66.**
   - The Fighter bay section works like the drone bay: one square per squadron, and the ability buttons.
   - The icons come from the owner's EVE client (`tools/gen_fighter_ability_icons.py`, `img/fighter-abilities/`).
   - A damage ability switched off adds nothing.
   - A speed ability switched on runs its pyfa handler on the squadron (`PROJ_FIGHTER_SELF_EFFECTS`).
   - Checked by `check_application.py` (the tool's actives as inputs, and pyfa's defaults when none are chosen), two golden
     fits and `fighter_bay_check.py`.
2. **Support fighters:**
   - Dromi webs into PYFA CORE `projected` (`webFighters`): the speeds, the chart and the times.
   - The EWAR card shows web, neut, ECM and warp disruption with pyfa's modified numbers.
3. **Bombs:** when switched on, pyfa's bomb volley (the charge's damage x amount x multiplier) and `_calcBombFactor`.
4. **Weaknesses picks:** rank "your fighters", and the why text says "weapons, drones and fighters".
