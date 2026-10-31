# Fleet from a kill (plan, 2026-10-28)

The owner: "add a backlog item that allows the user to choose a row from the kills list (not a loss) in the pilot dossier.
when chosen, the tool will use that killmail to build out the 'fleet' from that kill using each pilot/participant's
specified ship and weapon. it would be similar to the previous fleet functionality but in this case we actually know the
composition of the fleet so we can pull that pilot's most prominent, recent fit for the specified hull."

Why it's sounder than the hidden fleet view (L4, `local-and-fleet-plan.md`): Local says who is in the system, not who is
undocked or in what (LESSON #78). A killmail lists every player on the kill with their ship and the weapon credited, so
the composition is known; only each pilot's fit is an estimate, and the page says where each came from.

## Decisions (the owner, 2026-10-28)

- **F1. Each fit:** "the same logic that we already do in the pilot analyzer when a hull is chosen": their newest loss in
  that hull; none, their alliance's (else corporation's) common fit, said as not theirs; none, fit unknown.
- **F2. Who:** NPCs, capsules and pilots with no ship left out; no victim's side in this iteration.
- **F3. Where:** "its own tab for now that's only visible when the user has chosen to assess a fleet from the pilot
  dossier" ("i'm a fan of modularizing something like this").
- **F4. Shareable:** the link carries the kill and each pilot's loss, so everyone sees the same fleet.
- **F5. Layout:** "like we did on the system analyzer screen. summary of fleet combined capability along w/ individual
  members, their ships, dps, tackle, etc."
- My additions, agreed ("I agree on all of that"): a weapon check (a weapon the killmail credits them with that their fit
  doesn't carry is said); the fit's age; the coverage line (own / group / unknown); no "against your ship" verdict in the
  first version; 15 pilots at a time with Load more.
- Mockup `Claude outputs/fleet_from_kill_mockup.html`, all four answers as recommended: **F6** Fleet ▸ on every kill with
  2+ pilots; **F7** tackle and EWAR counted by kind; **F8** the dossier's pilot first, then DPS; **F9** one fleet at a
  time (another kill replaces it).

## Status

- **v2026.10.14.94: done.** The Fleet tab (`fk*` in index.html), Fleet ▸ in the dossier's kills list, the `#fleet=` share
  link (FLEET-01 for one cut short). `tools/page_checks/fleet_kill_check.py`.
- **v2026.10.30.4: done.** From Intel (the owner: "killmails on the intel feed and near you should link to a fleet tab that assesses
  the fleet that got the kill. include victims"): Fleet ▸ on Feed kills with 2+ pilots in ships and in Near You's opened rows; Near
  You's kill badges are buttons (one kill: its fleet; several: the row opened on them, option A); a solo kill: Pilot ▸, its pilot in
  the Pilot Analyzer ("send them to the pilot dossier": the ship-against-ship Matchup is the right tool for one ship). The Fleet tab
  says "From Intel", uses the killmail the live feed gave (no ESI request for it) and Close goes back to Intel.
- **Against This Fleet** (`fkvs`): the Matchup board's two halves on top, **the victim first** (the owner: "default to the victim
  in this case. we're assessing the kill first. then have the option to assess against our ship"), its fit the killmail's own (it did
  die, so this side checks the numbers), then **My ship**; below, the System Analyzer's Against Your Ship numbers for the side chosen
  (saVsCompute), pilots with no fit left out and said, the card's own range and prop. The victim's name opens them in the Pilot
  Analyzer on the lost ship. `tools/page_checks/fleet_vs_check.py`, `intel_fleet_check.py`.
- **v2026.10.31.1: Against This Fleet taken out.** The owner, after testing it: "i'm not loving this feature. in particular, it's the
  against my ship part"; one shared range for the whole fleet is unrealistic ("each ship in that fleet is going to be trying to be
  at their optimal range"); then "given the fluidity of ranges in fleet battles" and fits that are only a guess, "we probably should
  not be giving a time to kill numbers" for a whole fleet. No time to kill on the Fleet tab (LESSON #108); the one-on-one Matchup
  in the Pilot Analyzer keeps its numbers. What it would have added that the tab lacked, range, went into the cards already there:
  **Weapon reach** in the summary (nearest to farthest main weapon, turrets optimal + falloff, missiles flight, as pyfa gives them),
  each EWAR kind's farthest optimal, each pilot's main weapon range under the DPS and each module's range on the EWAR badges' hover.
  The victim is a tag in the line under the title (opens them in the Pilot Analyzer). `fleet_vs_check.py` checks all of it.
- **v2026.10.31.2: done.** The kill to analyze is chosen on the Fleet tab (the owner: "move the 'which kill to analyze' decision
  to the fleet tab"; Intel's row list was "not very intuitive or easy to read with a constantly changing list on both sides of the
  page"): a Near You badge opens its kills there, the newest shown, all listed in the header as they were when clicked
  (`fk.picks`, LESSON #110). Every kill opens there, solo ones too ("Fleet tab too"), from the Feed's label ("kills in the feed
  should be links as well. same mechanic"), a badge, or a Near You row opened; the Fleet ▸ / Pilot ▸ button is gone. **The victim**
  card above the fleet: the killmail's own fit (raw DPS and mix, weakest to, weapon reach, tackle and EWAR with reach, EHP), no time
  to kill. zKillboard not answering: one Retry in the pilots' head, counting down while the page's pause is on (`zkbRetryHtml`).
- Later (the owner, 2026-10-31): "a range graph ... that reflects where certain things kick in like points, disruptors, webs, dps
  ranges", and how it works for fleets of dozens or hundreds of ships; a lazy-load rule for everything that evaluates fleet ships.
- Later: group kills by shared attackers ("2 fleets", option D).
- Known simplification: a shared link's alliance fits are built from that variant's newest loss with its own charges (the
  tab itself uses the variant's most common charge per weapon, as the dossier does).
