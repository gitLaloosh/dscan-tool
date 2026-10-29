# Pilot Dossier: what a pilot flies, by gang size (plan, 2026-10-27)

The owner: "i wonder if we should add a filter of some kind that let's you switch between what they fly solo vs small gang or
larger fleets. hunters generally fly in pairs or small gang for example. some ship types are used for large whaling
fleets (bombers, kikis, etc.) there is a lot to consider so maybe building a dossier of the pilot based on how many are
involved when they're flying each ship type?" It grows out of the backlog item "Pilot Analyzer: guess the hull from what
they kill in lately" (high priority). Mockup: `Claude outputs/pilot_dossier_mockup.html` (the real v.88 page; the dossier
and the changed System Analyzer lines mocked).

## Decisions (the owner, 2026-10-27: "your pick is fine for 1-3 ... for #4 that's fine but give users the option to switch between group sizes")

- **D1. Size groups:** Solo (1) / Small gang (2–10) / Fleet (11+): the player attackers on each of their kills.
- **D2. How far back:** their newest 50 kills and 30 losses (read from ESI, kept for good; no new zKillboard request).
- **D3. Pilot Analyzer:** the dossier open above the loss tabs; its rows choose the hull whose losses show below.
  Active hours in **the user's own time zone, always** ("the pilot's active hours info is displayed based on the user's
  local timezone rather than UTC at all times").
- **D4. System Analyzer pilot rows:** each pilot's size picked from how many of their group are in Local (1 solo,
  2–10 small gang, 11+ fleet), **with a switch to choose the size instead**.

## Follow-up decisions (the owner, 2026-10-27, all as recommended)

- **D5. System Analyzer switch:** one switch on the Pilots card: Auto / Solo / Small gang / Fleet / All. Auto (the
  default) picks each pilot's size from their own group's count in Local; the others apply one size to every row.
- **D6. "Their group" in Local:** their alliance, or their corporation when they have none (not every hostile together).
- **D7. Pilot Analyzer hull button:** the dossier's rows replace today's dropdown of hulls by losses (one hull picker).
- **D8. Order:** the Pilot Analyzer's dossier first (delivery 1), then the System Analyzer rows reusing it (delivery 2).

## How it's worked out (from the mockup)

Gang size on a kill = its player attackers (NPCs left out; third parties included). Losses count toward a hull, not a
size. Weapons seen = each attacker's credited weapon_type_id on their kills; flies with = the other attackers' hulls;
kills mostly = the victims' ship classes; active hours and usual systems from their kills (systems from losses too). A
hull they never lost: their alliance's common fit (one zKillboard request, shared, kept an hour) or "fit unknown". Every
number a count, so thin data shows as thin. zKillboard's own size labels, if its lists carry them, to be checked.

## Status

- **Delivery 1 (v2026.10.14.90): done.** The Pilot Dossier in the Pilot Analyzer (D1–D3, D7): one kills list shared with
  the Last Kill line; the rows replace the hull dropdown; a hull with no loss of theirs shows their alliance's (else
  corporation's) common fit, said as not theirs; active hours in the browser's time zone. `tools/page_checks/dossier_check.py`.
- **v2026.10.14.91 fix:** the fallback's tab now links to the alliance's / corporation's loss its fit was read from (it
  linked to killmail "undefined"), and its loss row says whose loss it is.
- **Delivery 2 (v2026.10.14.92): done.** The System Analyzer's pilot rows read each pilot's newest 50 kills and 30
  losses (the dossier's data; the same 2 zKillboard requests per pilot) and pick the possible ship for a gang size: the
  hull with the most of their kills in it, tagged; a ship of theirs on the D-Scan still first; no kill in that size:
  v.84's rule. One switch on the Pilots card (Auto default, kept in the browser); Auto = their alliance's (else
  corporation's) count in Local. A row opens the dossier on the same size and hull. `tools/page_checks/sa_size_check.py`.
- **Kills under a row (v2026.10.14.93): done.** the owner's backlog item "expand a hull row to list its kills"; mockup
  `Claude outputs/pilot_kills_list_mockup.html`, all four answers as recommended: **K1** a ▶ button per row (the row
  still picks the hull); **K2** the list follows the switch; **K3** Show 10 more keeps reading older killmails from ESI
  past the dossier's 50 (zKillboard's list is already asked; Try again for any ESI couldn't return, PILOT-09); **K4**
  columns as drawn (when in your time, victim, players, system, their weapon, with them, zKillboard's value, link).
  `tools/page_checks/dossier_kills_check.py`.
- Still to check against a real pilot: whether zKillboard's lists carry their own size labels (the dossier counts the
  player attackers itself).
