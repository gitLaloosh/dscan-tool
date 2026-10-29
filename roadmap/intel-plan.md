# Intel feed (plan, 2026-10-28)

The owner via todo-inbox: "add Intel - this is likely the most important source of information that will go into this tool
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

The owner: "proceed with #1 and #2" (#1 delivery 2, #2 his feedback from real use, with no raw intel in the repository).
- Pilot names in Feed and Near You open the Pilot Analyzer; in the paired ship when the line pairs one pilot with one ship
  (or "Pilot (Ship)"), with a "From Intel" line and Back to Intel.
- Assess ▸ on a Near You row: the System Analyzer with Local = the system's reported pilots, D-Scan = its reported ships,
  analyzed; "Restore my paste" when it replaced the user's own.
- Intel's pairing as a pilot's possible ship in the System Analyzer ("reported in it on Intel").
- Copy shape: a Feed line with systems/pilots/unplaced words replaced (SYS, PILOT, WORD), ship names and keywords kept,
  plus what the page read; for the owner to send misreads without raw intel.
- Questions: Q1 pilot links open in the paired ship; Q2 a system's pilots = everyone reported in the window until a clear
  (today Near You shows only the latest report); Q3 Intel's pairing wins in the System Analyzer; Q4 the copy-shape button.
- The owner: all four as recommended ("Paired ship", "Everyone until clear", "Intel's pairing wins", "Add it"). Also: "the feed
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

Findings (2026-10-28), mockup `Claude outputs/intel_feed_kills_mockup.html`:
- The screenshot matches RIFT's Intel Feed (RIFT Intel Fusion Tool, a desktop app): "live intel, whether from intel
  reports or killboard feeds", coloring "based on your standings"; its kills come from zKillboard. Nothing found saying
  the EVE client has a kill feed a page could read.
- zKillboard's live feed is R2Z2 (RedisQ shut down 2026-05-31). API docs (zkillboard.com/api/docs/): sequence.json, then
  <n>.json until a 404; "Filter locally after retrieval"; wait 6 s after a 404; 15 requests/s per IP; non-empty
  User-Agent; files kept 24 h. Tried from the GitHub Pages origin in the owner's browser: the page can read it (CORS allowed);
  a record = killmail_id, hash, esi (attackers, killmail_time, solar_system_id, victim), zkb (locationID, values, points,
  npc, solo, awox, labels, attackerCount, href), uploaded_at, sequence_id; about 2.5 KB.
- Volume: 13,000-20,000 kills a day (history/totals.json, 18-25 Oct), about 10-15 requests a minute while Intel is on.
- Mockup questions: Q1 kills in the Feed from R2Z2 within range; Q2 a kill marks its system in Near You (attackers as
  reported, same alert rule); Q3 who's who (standing mark, logos, coloured name, tickers); Q4 Types / Distance / Sort /
  Search filters. The owner: all four as recommended.
- **v2026.10.14.99: done.** itKillPump (sequence.json, then one file at a time, 12 per 2 s tick at most, 6 s after a 404,
  backoff 30 s to 5 min on errors, INTEL-05), itKills / itAddKill (kept within max(alert range, Distance), NPC kills
  and >forget-window kills dropped, killmail_id deduped; friendlies' ships not counted), itNearAdd (one place for
  reports and kills; "N kill" on the row), who's who (itWhoHtml: mark, logos, coloured name, tickers), itSecFetch
  (security colour, ESI /universe/systems/, kept), the filter bar (it.set.feed, it.q; itRenderLists keeps focus).
  `tools/page_checks/intel_kills_check.py`.
- Also in v.99, from the owner's live use ("ESS refers to the Encounter Surveillance System that null sec systems have"):
  place and intel words (ESS, jump bridge, structures, belt, anom, site, MTU, d-scan, probes, hunter, roam...) are
  keywords, and inside / outside / sitting / holding and other plain words are filler, so they never reach the pilot
  lookup (real characters are named "Inside" and "ESS"); a ship named on its own and again in brackets after a pilot
  counts once. LESSON #88.
- The owner: all four as recommended ("Paired ship", "Everyone until clear", "Intel's pairing wins", "Add it").
- **v2026.10.14.98: done.** itPairs, itLive (the union), itOpenPilot / itAssess / itShape; saRowPick takes `sa.intel`
  pairs first; `tools/page_checks/intel_assess_check.py`.
- Next (the owner 2026-10-28, a screenshot of EVE's own Intel Feed window): "a layout reference and we might want to use some
  of the same concepts for communicating standing, alliance/corp, etc. data source as well." Layout ideas: standing icon,
  corp/alliance logo and ticker per pilot, one-row events, filter chips (location, distance, types, sorting, search).
  Data source: nearby kills; research how a page can get them before promising (the client may not write them anywhere
  a page can read; zKillboard's live kill stream is a candidate). Mockup first.


## The Feed's look and the kill feed's real behaviour (v2026.10.14.100)

The owner, on a Feed row: "i dont like any of the pill stuff on the feed ... the bright borders just draw your attention away
from the actual information." Mockups `Claude outputs/intel_feed_style_mockup.html` (A/B/C), `intel_feed_hybrids_mockup.html`
(H1-H4), `intel_feed_h2_h3_mockup.html`, `intel_feed_h2_final_mockup.html`. His picks: H2 ("Let's go with H2"), with:
1. the line as typed behind "a subtle button to expand the text to be at the bottom" (who sent it, the line, the channel;
   the copy-shape button moved into that strip);
2. system names in the security colour of the actual system (EVE's colour per tenth; 0.0 < sec < 0.05 shows 0.1);
3. "x Jumps" in the quiet grey, and "a callout like 'IN SYSTEM'" for your own system (an amber tag; in Near You its text
   lines up with the jumps below);
4. EVE's standing icons instead of the old marks: the client's `res:/ui/texture/classes/flagicon/*.png` are white 9x9
   symbols tinted on a 12x12 square (`bgframe.png`); the page draws its own (not CCP's files): a star for your
   corporation (green) and alliance (blue), + friendly, = neutral, - hostile. The page knows friendly or hostile, not
   +5 or +10;
5. kills by who died: Friendly lost (blue), Hostile killed (red), Neutral killed (plain), on the label and the row; Near
   You's badges in the same words (the owner: "Near You's badges should be inline with the Feed"). And: "Definitely show
   enemy kills as well": a kill by friendlies only of a hostile or a neutral shows with "hide friendly" on (no alert, no
   Near You row).

The owner: "are we actually capturing kills right now? i haven't seen any in the feed". Read from the GitHub Pages origin
(2026-10-28 21:06 UTC): `sequence.json` said 100263992 (last-modified 17:56 UTC) while kills uploaded to 21:06 were
numbered 3,000+ past it; a file not there yet answers 404 without the CORS header (a `no-cors` request to it succeeds,
a normal one throws), so the page never saw a 404. v.99 started three hours back (~10 minutes to reach live) and then
took each "nothing new yet" for the feed being down (INTEL-05, waits of 30 s up to 5 minutes). LESSON #89.

- **v2026.10.14.100: done.** itKillFindHead (from `sequence.json`, steps of 64, 128 ... then halving; ~15-20 requests,
  80 ms apart), the read-back in batches of 28 started 80 ms apart (240 in ~20 s), itKillGet (a blocked or 404 answer =
  not there yet), a `sequence.json` check after each miss (only when that fails too: INTEL-05), finding the newest again
  when the kills read were uploaded over an hour ago (at most once per 5 minutes). The H2 Feed and Near You;
  itStandIcon / itStandKind, itSecKey / itSecText / itSysTitle, itJumpsHtml, itKillWord / itKillBadges,
  itFriendlyOnlyRow, it.rawOpen. `intel_kills_check.py` answers R2Z2 as the real one does.
- Open: whether `sequence.json` stays stale (a zKillboard issue or by design); the page no longer depends on it.

## Three rings: kill range, alert range, in system (v2026.10.29.3)

The owner, 2026-10-29, after a kill 9 jumps away (seen in RIFT) never reached the Feed: "i didn't understand that kills were
limited only to the Alert range. i definitely want to see kills well before enemies reach the alert range. i think of this in
three stages ... I'd consider feed range as the ring of awareness, alert range is my ring of being alert and then the 'IN
SYSTEM' badge to say, hey, they're here." He chose a setting under the gear.

- **v2026.10.29.3: done.** Gear box 4 is "Range and alerts": "Feed: kills within N jumps" (3, 5, 7, 10, 15, 20, 30; default
  10; kept as killRange in dscanIntel) and "Alert: within N jumps" as before. Kills are kept within the larger of the two
  (itKillRange); the Feed's Distance no longer widens it, and its list goes to 30. Chat reports still show at any distance.
  A widened range applies to kills read from then on.
- Requests don't change: the page reads every kill on the live feed either way and keeps the near ones; a wider ring only
  adds name lookups on ESI for the kills kept.

## The switch back on the card (v2026.10.29.1)

The owner, via the inbox, 2026-10-29: "high prio - move the intel toggle back inside the intel tab next to the settings
button. leave the pill that shows up to alert the user to enemies inside of their alert range. feedback from other users,
they didn't see how to turn intel on while on the intel tab."

- **v2026.10.29.1: done.** The one on/off switch is on the Intel card, beside the gear (#intelSwLabel / #intelSw, "On" or
  "Off"); the header keeps only the "N near" pill (#intelNear), which opens the tab. The setup text and the card's info
  panel say where the switch is.
- Versions now carry the delivery's date (UTC) and its number that day: v2026.10.29.1 follows v2026.10.14.104.

## Head counts and sighting words (v2026.10.14.104)

The owner's bug report (a screenshot of the Feed, 2026-10-29): `<system>* 1red` showed a pilot "1red", and `<system>
<pilot> (recently seen as stabber)` showed a pilot "Recently" (both are real characters' names) with "as" left plain.

- **v2026.10.14.104: done.** A number with red / reds / hostile(s) / neut(s) / neutral(s), as one word ("1red") or two
  ("2 reds"), is a head count (p.count; chip "1 red"; Near You counts the larger of the named pilots + "+N" and the head
  count, "neutral" when every count was neut). recently, lately, as, was, were, been, last, saw, also, again, same,
  probably, prob, maybe, possibly, think are filler. A pilot pairs with the ship inside their brackets when the words
  between are filler or keywords ("A (recently seen as sabre)").
- Every zKillboard request is checked to go through its gate (`tools/check_request_gates.py`, chain step;
  `request_gates_check.py`, page check). CLAUDE.md states the rule.

## Kills that keep arriving (v2026.10.14.103)

The owner, 2026-10-29: "the intel feed is still not showing any kills". Read live from his browser (the GitHub Pages
page, the built-in browser pane, 2026-10-29 about 03:20 UTC):

- `sequence.json` at his edge still said 100263992, the same as 2026-10-28 17:56 UTC, while fetched from elsewhere it
  said 100271220. Finding the newest from it worked.
- Finding the newest stopped at 100270556, an hour old: 100270557 and 100270558 failed from his browser while
  100270559 through +500 answered. Fetched from elsewhere, 557 and 558 were there. Either way, a reader can meet a number
  that fails while later ones answer, and v.100 then waited on it for ever.
- A read-back started as 28 timers in a hidden tab (the browser pane was hidden) went out together. After it, every
  file and `sequence.json` failed from his address: zKillboard blocks an address over 15 requests a second for an hour
  (its R2Z2 docs, FAQ). The page did the same in any hidden tab, the usual case while playing.

- **v2026.10.14.103: done.** itKillTurn: every R2Z2 request through one gate, one at a time, 100 ms apart by the clock,
  the wait timed by a worker (itSleep), so at most 10 a second in a hidden tab too, and no slower there. Holes: a missing
  number with a kill in the next 3 is skipped and asked for again at 6 s, 30 s, 2 min and 5 min (kf.holes); finding the
  newest looks past where halving stops; the read-back keeps the kills after a missing one. INTEL-05 now says the address
  may be blocked for up to an hour.

## No system, no report (v2026.10.14.102)

The owner's bug report (a screenshot of the Feed, 2026-10-29): two rows with no system, one "CLEAR" and one "STATUS?", and
a "Probe" ship chip. The lines behind them, read in his log for their shape only: `78 status?` (a system shortened to two
characters, too short to place), then a bare `clr` (its answer), and `<system> <pilot> probe` followed three seconds
later by `<system> clr`: a pilot passing through in a Probe frigate, read correctly. The owner: "we shouldn't generate a
'report' if it doesn't contain a valid system name."

- **v2026.10.14.102: done.** itReports drops a line with no system it can read before anything else: no Feed row, no
  Near You change, its words not looked up as pilots (no /universe/ids/ request for them); it still counts as the
  channel's last line. itParse no longer makes "status?" from a question with no system (it could not reach a row).
- Not done: tying an answer ("clr") to the question it answers ("78 status?"). A two-character system can't be placed,
  and a guessed answer could clear the wrong system.
