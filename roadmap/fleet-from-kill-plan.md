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
- **v2026.10.31.3:** the dossier's fleet icon (option D) opens any kill, solo ones too; the tab's zKillboard link is the zK icon;
  names in their standing's colour, the system in its security colour.
- Later (the owner, 2026-10-31): "a range graph ... that reflects where certain things kick in like points, disruptors, webs, dps
  ranges", and how it works for fleets of dozens or hundreds of ships; a lazy-load rule for everything that evaluates fleet ships.
- Later: group kills by shared attackers ("2 fleets", option D).
- Known simplification: a shared link's alliance fits are built from that variant's newest loss with its own charges (the
  tab itself uses the variant's most common charge per weapon, as the dossier does).

## The kill list scrolls, with each kill's ISK (v2026.11.01.3)

The owner (2026-10-31): "fleet tab > list of kills originating from intel tab needs scrolling. systems with large battles will fill the
entire screen and cause endless scrolling"; (2026-11-01) "add isk value of a kill to the list of killmails in the fleet tab", "can be
folded into the next delivery for that page"; picked "Scroll inside" (mockup `Claude outputs/close_buttons_kill_list_mockup.html`).

- About six and a half rows show (the cut-off row says there's more); the rest scroll inside `.fk-picks`; at either end the wheel moves
  the page on (overscroll-behavior auto, LESSON #96).
- fkRender keeps the list's scroll through its redraws (fkPicksTop / fkPicksKeep); a kill opened while out of view is scrolled into view
  within the list, never the page (LESSON #119).
- ISK: zKillboard's value already on each Intel kill (`isk` on the pick, from `e.kill.value`), written as the Feed writes it (itIsk),
  amber; the exact value in its hover; none without a value. No new request.
- `tools/page_checks/close_buttons_check.py`.

## The kill list grouped into fleets (v2026.11.01.6)

The owner's backlog item "Intel kills grouped by shared attackers" ("later D = group kills by shared attackers ('2 fleets')"); the
spec in the Project doc roadmap/kill-groups-impact.md section 0, mockup claude/roadmap/kill-groups-mockup/.
- Only the kill picker (opened from Intel with 2+ kills). Intel, the per-kill analysis, the `#fleet=` link and the zKillboard budget
  are unchanged; grouping reads the killmails already in `fk.picks` (`fkGroupKills`, under 1 ms for 120 kills).
- Rule: 2 shared player attackers link two kills ("go with 2 shared pilots"), 1 when either kill had 1–2 ("keep the exception as you
  intended"); fleets are the chains; victims and NPCs never link; kills linked to nothing go last as "Not linked". Later, not now: a
  size-based mix with a percentage.
- Layout: a heading per fleet (`Fleet N · N pilots · N kills`, the ISK in amber, the newest kill's age, the victims as Near You
  counts them, the rule in its hover), Intel's chevron, `aria-expanded`; biggest first ("biggest first sounds good"); every group
  closed ("just have each fleet default to collapsed"), a lone group open (the owner: "Open it"); the fleet holding the kill analyzed
  says "analyzing"; an open fleet's heading stays at the top of the list while its kills scroll ("let's do the headers staying in
  place and add the expand/collapse"); open groups kept for this set of kills. Phone: one line, ISK, age and victims on a second line
  when open (the owner: "Second line when open").
- `tools/page_checks/kill_groups_check.py`; intel_fleet_check, fleet_kill_check and close_buttons_check extended; `check_ui_rules.py` (6).
- v2026.11.01.7 (the owner: "we should swap the fleet size and isk value placement"): each kill's pilots, then its ISK, so the ISK sits
  under its fleet heading's ISK (wide; at 390 px the ISK last on the second line).

## Fits on request, common fits for big fleets (v2026.11.02.1)

Project doc roadmap/fleet-fit-budget-plan.md (decisions D1–D6, build queue 004). The owner: "figure out how we can best avoid hitting
our 10 minute cap on zkill requests when dealing with fleets this large"; "what if we didn't automatically load the fits? default to
ship type/weapon and damage on the kill"; "a column added to the far right that has a Load All button/link and the rows have a Load
button/link"; "give an option to use common fits for large fleets"; "25 seems like a good starting point".
- Opening a fleet asks zKillboard nothing. Fits the share link carries (ESI) and fits kept from the last hour (a cache-only pass:
  pilot hull losses now kept 1 h in IndexedDB 'zkb' like every other zKillboard answer) load at once.
- **Damage** gets its own column beside the ship (where the owner's screenshot put it): what they did on this kill, its share of
  the ship's, the final blow. Rows stay in damage order until every pilot is in ("Stay put until all load"), then sort by DPS.
- **Fit column** on the far right: Load per row (1 request, 2 when the alliance's list isn't kept); once loaded, own / alliance /
  corp / unknown (the whole sentence on hover) and own? (their own losses, 1 request). A row is its button plus this cell, never a
  button in a button.
- **Load all** above the column: Common fits, the choice above 10 pilots (`FK_COMMON_FROM` 11), one request per alliance-and-hull
  pair not kept, and a pilot who is a victim in that list gets their own loss from it at no cost; Own fits (up to 10), the per-pilot
  rule, "N requests, up to M". The label is exact and says what's left. It keeps `FK_ZKB_RESERVE` (25) of the 100: the request that
  would eat into it is refused as it's counted in the queue (`zkbFetchNow`'s `o.reserve`), so it stops at exactly 75; then a
  countdown and one timer carry on. A row's Load and own? may use the whole 100.
- The summary before fits: pilots in ships, hulls, logistics, damage on the kill, "Load all" for the rest.
- The Systems tab fleet section unchanged (D5): `saHullFits` keeps its output; the killmails it read are a non-enumerable `.losses`.
- `tools/page_checks/fleet_fit_budget_check.py`; fleet_kill_check, fleet_vs_check and outside_links_check press Load all;
  `check_request_gates.py` allows the reserve (it can only lower the cap).
