# Intel feed (plan, 2026-10-28)

the owner via todo-inbox: "add Intel - this is likely the most important source of information that will go into this tool
... the tool actively polls the game's chat log for the intel channel and tracks neutral and hostile ships that are
reported via that channel. the user specifies what they want to see in the intel feed, when they want to be notified of
an incoming threat and how to present it. see tools like RIFT and https://voidsonar.space/. this is a big one." Then: "it
needs to have an on/off mechanism. once started it will be watching that chat log constantly so an off switch is a must
as well." Mockup: `Claude outputs/intel_mockup.html` (revised to the answers below).

## Decisions (the owner, 2026-10-28)

- **I1. Where:** "the tab has the feed in a card. settings button (little gear icon or something), prefer a slider for
  off/on similar just like 'use in assessments' and prop mods for consistency." An Intel tab with one Intel card (Near
  you + Feed) and a gear; the Intel slider beside Standings on every tab, with an "N near" badge while on. First time,
  the card opens its settings (folder, channels, you, alerts). v.96 also had a "Watching" slider on the card (the same
  switch); the owner: "shouldn't one slider control it?" -> "keep the intel slider": removed in v2026.10.14.97.
- **I2. Jumps:** a built-in table, "as long as it is accurate and doesn't get out of sync with eve updates" (see Jumps).
- **I3. Order:** two deliveries.
- **I4. Real logs:** read for the format only (read only; never committed; test logs synthetic, no real names).

## What the real logs showed

- File `<Channel>_<YYYYMMDD>_<HHMMSS>_<characterID>.txt`, UTF-16 LE with BOM (each line starts with U+FEFF). Header:
  dashes, `Channel ID:`, `Channel Name:`, `Listener:`, `Session started:`. Lines `[ yyyy.mm.dd hh:mm:ss ] Speaker >
  message` in EVE time (UTC). The character ID in the file name tells characters apart.
- Local: `EVE System > Channel changed to Local : <system>` on each jump. An intel log's first line can be an MOTD.
- EVE writes promptly: the file's mtime matched its last line within about 1 s.
- OneDrive can move Documents, leaving an old Chatlogs folder that stops getting files: show the chosen folder and the age
  of its newest log.
- Report shapes: mostly `SYSTEM pilot names ship [nv|clr|+N]`; also `*` after linked items, shortened systems (the start of a name),
  `Pilot (Ship) jumped A from B`, lower-case ship names, Chinese ship names. A word that can't be placed stays plain text,
  never guessed; the raw line is always shown. Shortened systems resolve to the nearest match to you.

## Jumps

- Source: the EVE client's own `res:/staticdata/jumps.static` (via `C:\CCP\EVE\tq\resfileindex.txt` →
  `C:\CCP\EVE\ResFiles\...`). Format (its `jumps.schema`): a 4-byte count, then 65-byte items: jumpID, stargateID,
  fromSystemID, toSystemID (uint32 LE at 0/4/8/12), jumpType (1 byte at 16: system/constellation/region), two double
  vec3 coordinates. Each connection is stored once (one direction). Build 3654997: 6,989 connections, 5,268 systems.
  Checked against ESI stargates for 1DQ1-A (4) and Jita (7): exact.
- Names from ESI `POST /universe/names` the first time Intel starts (6 requests), kept in IndexedDB `eta-intel` per table
  md5 (the client file has IDs only). The table is 51 KB in the page.
- The page stores the build; on start it reads ESI `/status/` `server_version` (equals the client build: 3654997 on
  2026-10-28) and says so in the card line when EVE has been patched since.
- Chain step: compare the table with the client's `jumps.static` fingerprint (md5 in resfileindex) when the computer is
  linked; fail on any change; "skipped" when not linked.
- Stargates only: no Ansiblex bridges (player structures), no wormholes. Later: the user's own bridge list.
- Chinese/other-language ship names: pyfa's `types.*.json` `typeName` has every language.

## How it works

- No EVE login: ESI has no chat. **Log Chat to File** (Settings → Chat) must be on.
- File System Access API (Chrome/Edge, https): pick the folder once; after a restart one click resumes. Only the new end
  of each chosen log is read every 2 s, from a worker (hidden tabs throttle ordinary timers); a relog's new file is
  picked up.
- Reports: systems, pilots (ESI, coloured by Standings), ships, counts, keywords (clr, nv, status?, ...).
- Alerts: sound + desktop notification for hostile/neutral within N jumps; never friendlies; reports age out.
- Privacy: logs never leave the browser (ESI name lookups only); never saved to the repository.

## Deliveries

1. The tab and card, both sliders, the gear and settings, reading the folder from a worker, your system from Local, the
   feed with recognition, Near you with jumps (table + chain step), alerts.
2. Intel to assessment: a reported pilot opens the Pilot Analyzer; a system's pilots to the System Analyzer rows.
3. Later: a small map; alert rules by ship type; several characters at once; jump bridges.

## Status

- **v2026.10.14.96: delivery 1 done.** `it*` in index.html (the tab, card, sliders, gear, worker ticker, report reading,
  Near You, Feed, alerts); `tools/gen_intel_tables.py` (INTEL_JUMPS from the client, INTEL_SHIPS from pyfa) and its
  chain step; `tools/page_checks/intel_check.py` (made-up logs only: no raw intel in the repository, the owner 2026-10-28).
  INTEL-01..04.
- To prove on the owner's machine: alerts with the tab hidden (the worker), the folder handle after a browser restart, real
  report shapes the made-up logs don't cover.
- v2026.10.14.97: one switch, the Intel slider at the top (the card's "Watching" slider removed); the "N near" pill is its
  own button and opens the Intel tab (it sat inside the slider's label and switched Intel off); the settings' lists readable
  on Windows.
- Next: delivery 2 (a reported pilot to the Pilot Analyzer; a system's pilots to the System Analyzer rows).

## Delivery 2 (mockup `Claude outputs/intel_assess_mockup.html`, 2026-10-28)

the owner: "proceed with #1 and #2" (#1 delivery 2, #2 his feedback from real use, with no raw intel in the repository).
- Pilot names in Feed and Near You open the Pilot Analyzer; in the paired ship when the line pairs one pilot with one ship
  (or "Pilot (Ship)"), with a "From Intel" line and Back to Intel.
- Assess ▸ on a Near You row: the System Analyzer with Local = the system's reported pilots, D-Scan = its reported ships,
  analyzed; "Restore my paste" when it replaced the user's own.
- Intel's pairing as a pilot's possible ship in the System Analyzer ("reported in it on Intel").
- Copy shape: a Feed line with systems/pilots/unplaced words replaced (SYS, PILOT, WORD), ship names and keywords kept,
  plus what the page read; for the owner to send misreads without raw intel.
- Questions: Q1 pilot links open in the paired ship; Q2 a system's pilots = everyone reported in the window until a clear
  (today Near You shows only the latest report); Q3 Intel's pairing wins in the System Analyzer; Q4 the copy-shape button.
- the owner: all four as recommended ("Paired ship", "Everyone until clear", "Intel's pairing wins", "Add it"). Also: "the feed
  keeps growing on the intel page. we should probably drop entries older than 15 minutes" (the Feed keeps the time set).
- **v2026.10.14.98: delivery 2 done.** itPairs, itLive (a system's union until a clear), itOpenPilot / itAssess /
  itAssessEnd, itShape / itCopyShape, the From Intel lines (#pilotFromIntel, #saFromIntel), sa.intel in saRowPick;
  `tools/page_checks/intel_assess_check.py`.

## Next (the owner, 2026-10-28)

With a screenshot of EVE's own Intel Feed window (kill rows: system, time, victim ship and corp ticker, killer; filters
Location / Distance / Types / Sorting): "a layout reference and we might want to use some of the same concepts for
communicating standing, alliance/corp, etc. data source as well."
- N1. The Feed's layout and how it shows standing and alliance / corporation, modeled on that window (mockup first).
- N2. Whether those kill events can be read by the page at all (client files, ESI): to be checked, not assumed.
- the owner: all four as recommended ("Paired ship", "Everyone until clear", "Intel's pairing wins", "Add it").
- **v2026.10.14.98: done.** itPairs, itLive (the union), itOpenPilot / itAssess / itShape; saRowPick takes `sa.intel`
  pairs first; `tools/page_checks/intel_assess_check.py`.
- Next (the owner 2026-10-28, a screenshot of EVE's own Intel Feed window): "a layout reference and we might want to use some
  of the same concepts for communicating standing, alliance/corp, etc. data source as well." Layout ideas: standing icon,
  corp/alliance logo and ticker per pilot, one-row events, filter chips (location, distance, types, sorting, search).
  Data source: nearby kills; research how a page can get them before promising (the client may not write them anywhere
  a page can read; zKillboard's live kill stream is a candidate). Mockup first.

