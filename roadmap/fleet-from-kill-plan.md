# Fleet from a kill (plan, 2026-10-28)

the owner: "add a backlog item that allows the user to choose a row from the kills list (not a loss) in the pilot dossier.
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
- Later, after use: an "against your ship" view of a known fleet; the victim's side.
- Known simplification: a shared link's alliance fits are built from that variant's newest loss with its own charges (the
  tab itself uses the variant's most common charge per weapon, as the dossier does).
