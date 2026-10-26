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
2. **Support fighters: done in v2026.10.14.70.**
   - Dromi webs into PYFA CORE `projected` (`webFighters`, pyfa `getProjFighterData`): the speeds, the chart and the times.
     Against the default target a Nidhoggur's applied DPS goes from 397 to 633 with its Dromi out.
   - The EWAR card shows web, neut, ECM and warp disruption with pyfa's modified numbers (the carrier's bonuses and Support
     Fighters at V; `gen_projected_table.py` records the handlers), one chip per squadron type; only the web is applied.
   - Checked by `check_projected.py` (the tool's launched squadrons and abilities as inputs), four golden fits and
     `support_fighters_check.py`.
3. **Bombs: done in v2026.10.14.71.**
   - The Bomb button is a toggle, off by default (pyfa's default).
   - When switched on: pyfa's bomb volley (the squadron's charge's damage x its fighters x the bomb damage multiplier,
     absent: 1) every Launch Bomb duration, and `_calcBombFactor` in PYFA CORE `application` (no lock, no range).
     No pyfa handler modifies a bomb (`gen_projected_table.py` asserts it).
   - Two Ametat II squadrons on a Hel: 2 x 3,840 per 60 s = 128 DPS.
   - Checked by `check_application.py` (pyfa's getVolley from the charge and the bomb branch), the golden fit
     `hel_constructed_ametat_bombs_on` and `fighter_bombs_check.py`.
4. **Weaknesses picks: done in v2026.10.14.72.**
   - the owner: "One tile per class" and abilities "As set in the Fighter bay".
   - "Your light fighters" / "Your heavy fighters" ("Their ..." in the My Ship Perspective): each damage-dealing type in the
     bay flown in that class's squadrons (bay, class limit, the tubes left by the other classes), ranked by the strip's
     time to kill with the rest of the fit as it is.
   - The why text and the empty-card message name fighters; the card's info explains the per-class pick.
   - Checked by `check_weakness_picks.py` (a Nyx with four light and two heavy types, both ways; an oracle fit per
     candidate) and `fighter_picks_check.py`.

All four deliveries are done: carriers are assessed with pyfa's numbers for squadrons, abilities, support EWAR, bombs
and the picks.

Follow-up, v2026.10.14.73 (the owner: "are we not recommending fighters when my ship is not active?"): with no ship saved,
the Weaknesses card has a Fighter tile too: the T2 light fighter, heavy fighter and bomber of the target's least resisted
damage type, and how much of each one's damage lands (pyfa's getFighterAbilityMult, skills at V, the bomb counted).
The Missile and Fighter tiles start collapsed to one summary line. Checked by `check_fighter_rec.py` and
`fighter_tile_check.py`.
