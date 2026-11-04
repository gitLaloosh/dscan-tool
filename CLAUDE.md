# Notes for AI assistants working on this repo

**This repository is public. Nothing personal goes in it (LESSON #90).** No real names (the
owner's, his characters', other players', corporations' or alliances' from his screenshots, logs
or pastes), no paths from his computer (`C:\Users\<name>\...`), no e-mail addresses, no keys or
tokens, no screenshots and no raw intel (chat lines, D-Scan or Local pastes). Refer to him as "the
owner". Test data is made up; real pastes and logs are read for their format only. A mockup shows
the real page with made-up data, and every picture embedded in a page is looked at and listed in
`tools/pii_reviewed_images.json`. `python3 -I tools/check_pii.py` refuses all of it (a chain step
and a git pre-commit hook: `git config core.hooksPath tools/git-hooks`); personal names it looks for
are in the git-ignored `tools/pii_terms.local.txt` on the owner's computer.

**Never get the user's address blocked (LESSON #93).** zKillboard blocks an address that asks too fast
(its live feed: over 15 requests a second, for an hour). Every request to zKillboard goes through one
of two gates: `zkbFetch` (the API: one at a time, 1 s apart) or `itR2Fetch` (the live feed, v2026.10.30.3: its
`itKillTurn` gate, at most 5 a second by the clock, waits timed in a worker; a stop for an hour at the first 429, kept in
localStorage for every copy of the page; a tripwire; LESSON #106). zKillboard's developer has said the limit will be cut
further if abuse continues, so stay at a third of it. The API's pause after a failure is kept in localStorage (`dscanZkbPause`,
v2026.10.31.2) so a reload waits it out too, and every Retry after a zKillboard failure is `zkbRetryHtml` (a countdown while paused). Test against a stand-in, never by provoking the real service. Never pace requests with a batch of timers:
a hidden tab fires them together. Every `fetch()` is listed in `tools/check_request_gates.py` (a chain
step); `tools/page_checks/request_gates_check.py` tests both gates with the timers bunched. Probing a
live service from the owner's machine counts against his address too.

EVE Threat Assessment (ETA; called D-Scan Analyzer until v2026.10.14.60, and the repo, file and
saved-data names still say dscan) is a single-file tool (`index.html`) that estimates EVE Online
ship stats from killmails and EFT fits. Its calculations must match **pyfa**
exactly, using primary sources only: pyfa's source code and CCP's SDE / live ESI.

Before any calculation work, check that pyfa hasn't moved:
`PYFA_SRC=/path/to/Pyfa python3 -I tools/pyfa_update_check.py` (add `--run` for
the full verification chain). See `PYFA_CORE.md`.

**The rule (`PYFA_CORE.md`):** code fenced `PYFA CORE BEGIN/END` in `index.html`
replicates pyfa and is fingerprint-locked (`tools/pyfa_core_manifest.json`). The
tool may change what goes INTO the pyfa calculation (module states, assumed
charges, drones) or how results are SHOWN, never how the calculation works.
Change a core section only to match pyfa, then re-verify and run
`node tools/check_pyfa_core.mjs --update`. Every deliberate difference from pyfa
is listed in `DEVIATIONS.md`; an unlisted difference is a bug.

Before changing any calculation:

1. Read `LESSONS_LEARNED.md`, the catalog of mistakes already made here:
   its Index first (one line per entry, grouped by task), then the entries
   that apply. Follow its checklist **in order**: it's the definition of
   done, and the expected values are derived before any code is written.
   For page, Intel or process work, the matching Index groups are enough.
2. Use `tools/` (see `tools/README.md`):
   - `tools/pyfa_effects.py` runs pyfa's real effect handlers so you find all
     of them. Don't grep or regex `effects.py`.
   - `tools/independent_checks/` derives expected values without the tool's
     own tables. `tools/pyfa_fit_oracle.py` runs pyfa's handlers on a whole
     fit (hull, modules, charges, skills, mode) and is the reference for
     resistances; reuse it for any stat it covers.
3. Run `node regression_suite/run_regression.mjs index.html`. It must print
   ALL PASS. Add a constructed golden fit for every new mechanism.
4. Bump the version tag in `header.hero`: `vYYYY.MM.DD.N` is the delivery's own date (UTC)
   and its number that day, from 1 (`v2026.10.29.1`, then `.2`; the next day `.1`). Up to
   `v2026.10.14.104` the date never changed and N counted every delivery; users read that as an
   old build. Add a dated note to `dscan-tool-history/`.
   Exception: the pull requests `.github/workflows/jump-table.yml` opens (the stargate table, `INTEL_JUMPS`,
   when an EVE build changed a gate; `tools/jump_table_update.py`) change only that table and no version.
   After the owner merges one, work from the merged copy (he runs `git pull`).
5. End every delivery's reply with a commit message for the owner (he commits himself; the owner, 2026-10-30): a
   Summary line under 72 characters that starts with the version (or says "page unchanged" for tools and docs only)
   and a Description of short bullets. No names, paths or intel channel names.
6. Report index.html's gzipped size in every delivery (`gzip -9 -c index.html | wc -c`). Past 800 KB, stop and ask
   the owner before delivering (the owner, 2026-11-03: "At 800 KB"); the planned answer is a publish step that strips
   comments (about 38% of the gzipped page), not moving tables out of the page.

**Error messages carry codes** (`ERRORS.md`). Every error the page writes ends
with a code such as `(ZKB-01)`, defined once in `ERROR_CODES` in `index.html`
(what triggers it, what to check, why it exists, the build and history doc).
A new error message gets a new code there (never reuse or renumber one; retire
it instead), shown with `withCode()` / `codedError()`. Then run
`python3 -I tools/gen_errors_md.py --write`. Owner reports quote the code: look it up in
`ERRORS.md` first.

**My Ship** (v2026.10.14.33, `roadmap/my-ship-plan.md`): the user's own fit, saved in
the browser (`localStorage` `dscanMyShip`: EFT text, module states, the switch; never the
numbers, which are recomputed from the text). Code: the `MY SHIP` block at the end of the
script; classes `mys-*` (`ms-*` means module state). Start-up code must survive the suites'
stub DOM (LESSON #36). Check: `tools/page_checks/my_ship_check.py`.

**UI rules** (v2026.10.29.7; approved by the owner from mockups, 2026-10-29; LESSON #101). One of each, site-wide:
- **Tag** (chips, pills, labels): 3-4px corners, never round; a faint fill (`--tag-fill`), no visible border at rest;
  hover/open `--tag-fill-hover` with `--accent-edge`; pressed `--tag-on`. Empty states: the same fill, dim text, no dashes.
  Cyan is the one accent.
- **Switch** (`.dmg-sw`, `input.mys-sw`): 36x20 track, 3px corners, square 14px knob; off faint, on `#1f6f80`. One named exception
  (v2026.10.30.2, the owner): the Intel switch (`#intelSw`) off is amber and breathes (none with reduced motion), so new users find it.
- **Slider**: the global `input[type=range]` style, a 4px track filled cyan to an upright 10x18 handle. The fill is
  `--p`, set by `rangeFillSet` (input events, new sliders, and code that sets `.value`/`.max` calls it). No local slider CSS.
- **Text field** (text, search, select, textarea): `--bg` fill, `--field-border`, 4px corners; hover
  `--field-border-hover`; focus a cyan border and the `--accent-ring` ring (never amber, never the browser's own);
  disabled 45%. 36px tall, 32px in filter bars; paste boxes stay monospace.
- **Intel lists** (v2026.10.30.1, the owner): the jump count first; system names in a column as wide as the widest system name
  (measured in the drawn font, `itSysWidths`); the left edge only means "within your alert range", in the "N near" colour
  (amber); no background highlighting; standing colours on words and names (neutral a bright grey). Intel channel names are
  shown only under the gear, never elsewhere (the owner: "security reasons"). `tools/page_checks/intel_layout_check.py`.
  A line naming several systems is placed after the name lookups, never before (LESSON #105; `intel_place_check.py`).
  Your profile (v2026.11.01.1; roadmap/my-ship-plan.md "Your profile"): one control at the top right (portrait, name, the fit
  in use inside the "Use in assessments" switch) and its panel (Pilot, Standings, My Fits; the shared close button). Intel's
  mark lives on it (off, clear cyan, not working hollow, near amber, in system the Hostile red + pulse); the tokens --st-clear,
  --st-near, --st-in. "My Fit", never "My Ship", in what users read. `profile_check.py`.
  Intel's pilot chip (v2026.11.01.2, the owner's B2): standing (a tip only: standings aren't changed from a chip), name (Pilot
  Analyzer), corporation (logo + [TICKER]) and alliance (logo + <TICKER>) as separate parts; a group pressed filters the Feed by its
  ticker (`[CORP]` / `<ALLIANCE>` in the search box); hover: outline + dividers, the part under the pointer filled white; without
  hover the first tap shows the parts. `pilot_chip_check.py`.
  One close button (v2026.11.01.3): every info and settings panel (role="dialog") has the shared `button.x-close`, 32 px in its top
  right (44 px on a phone), at every width; Esc and a press outside still close, the focus back on the opener. Menus (⋮ fit actions,
  hull variants, slot menus, the My Fit picker on a wide window) have none. `check_ui_rules.py` (5), `close_buttons_check.py`.
  Drawing cost (v2026.11.01.4, LESSON #120): Intel's card is drawn only when what it shows changed (itQuickKey, then the built text
  compared) and only while it can be seen (itShown; drawn once on return); its ages move on their own timer (10 s / 30 s). Don't add
  writes to the page on a timer without the same compare. Endless animations: opacity or transform only. `intel_redraw_check.py`;
  measure with the Project's roadmap/perf-harness/ (before and after in one session).
  Layout D (v2026.10.31.6, the owner; Project doc roadmap/near-you-layout-d.md), both lists: line 1 jumps, the system (a button that
  filters the Feed only, never Near You), Near You's analyze icon (radar rings, always the System Analyzer), the tags, the time; Near
  You's kill badges on their own line, only when there are kills; then the toggle under the jumps and what was reported. No Assess
  column, no REPORT label; Clear, ESS (white at it, red linked), Bubble and camp are tags. A killmail's fleet size is drawn once
  (`fleetSizeHtml`, the dossier's). Check a layout with a busy row at every width (LESSON #113; `intel_layout_check.py`).
  v2026.10.31.7 (the owner's idea): the analyze icon has its own column right after the jumps, in Near You and on the Feed's reports
  (the whole system, not only that line; none on kill and clear rows); everything else starts after it, so a row without it has an
  empty cell. The jump column fits "88 Jumps" and In system (`--it-jw`). On a phone the icon sits under the jumps beside the toggle.
  Mockups size things the way the page does (LESSON #114).
  A word is a pilot only in its name's own capitals (one word typed by hand) or dragged in; report words (`IT_NOT_PILOT`) never
  otherwise (LESSON #111; `intel_words_check.py`).
  A word before "gate" is read among the gates of the system the line is in (LESSON #112); one tag per Near You row for a gate:
  red "Camp · X gate" from a report, orange from 2+ kills at that gate, grey a gate with no camp words (`intel_gates_check.py`).
- **Standing icon** (v2026.10.30.4, the owner): one drawing site-wide, `standIcon` / `standMark` (EVE-style: a star for your
  corporation and alliance, + friendly, = neutral, − hostile); never drawn again elsewhere. Beside its own word it is decoration:
  `standIcon(k, true)` / `SIDE_MARK_BY_WORD` (LESSON #107).
- **Links out of the site** (v2026.10.31.3, the owner): a zKillboard link is `zkLinkHtml` (a "zK" icon in cyan, the colour of
  leaving the site), never "zKillboard ↗" text or a hand-written `target="_blank"`; every link that leaves the page asks first
  (`leaveAsk`), with "Don't ask again" per site and "Ask again" under Intel's gear. `outside_links_check.py` counts them.
- **Names in colour** (v2026.10.31.3, the owner): a system's name in its security colour (`sysNameHtml`, Intel's rule); a person's
  name in its standing's colour with its icon (`standNameHtml` / `std-n`), victims included. A dossier kill from the past 4 hours has
  its time in amber (`PD_RECENT_MS`).
- **What was asked for stays on screen** (v2026.11.01.5, LESSON #121): the Pilot Dossier draws the hull asked for (a pilot opened
  from the Fleet tab, a typed hull, a System Analyzer row) as its first row in every size, tagged On this kill / Lost on this kill /
  Asked for with its rank; the 8 busiest follow; "Show N more hulls" is a button that draws every hull read. A Fleet-tab kill missing
  from zKillboard's list for the pilot is added from the killmail already open ("+ this one"). `dossier_pin_check.py`.
- **Kills grouped into fleets** (v2026.11.01.6, Project doc roadmap/kill-groups-impact.md §0, LESSON #122): the Fleet tab's kill picker
  (opened from Intel with 2+ kills) groups kills by shared player attackers: 2 shared pilots link two kills, 1 when either kill had
  1–2; chains are one fleet; victims and NPCs never link; "Not linked" last; biggest fleet first, newest kill first inside. Every
  group starts closed (a lone group open), headings with Intel's chevron stay pinned at the top of the list while their kills scroll
  (`top:-2px` over the list's padding); open groups are kept per set of kills. Only the picker: Intel, the analysis, `#fleet=` and
  the zKillboard budget don't change; no request. `kill_groups_check.py`; `check_ui_rules.py` (6) keeps list expanders on IT_CHEV.
- **Alert sounds** (v2026.11.01.8, Project doc roadmap/alert-sound-plan.md): two slots by jumps, Near You (1 jump to the alert range)
  and In system (0 jumps, kills too); five sounds made in code (Chime = the old sound exactly), or your own file (≤ 1 MB, ≤ 5 s,
  kept only in its own IndexedDB database `dscan-intel-sounds`, never the ESI cache); one master gain, loudness (volume/100)²; the
  notification is silent when the page's sound plays. No audio is made before a sound or a press. `alert_sound_check.py` (a stand-in
  AudioContext; generated tones only, never a real recording in the repo).
- **Intel map** (v2026.11.02.4, Project doc roadmap/intel-map-plan.md): layout B, the map beside Near You and the Feed below (a
  List | Map switch in Near You on a phone, `it.set.nearView`). `INTEL_MAP` (CCP position2D /1e14, security in hundredths, region)
  comes only from `tools/jump_table_update.py`, aligned to `INTEL_JUMPS` (its `jumps` = the jump table's md5; `gen_intel_tables.py`
  keeps it and says when it no longer fits). One canvas (`itm`), made once and moved into each card (`#itMapSlot`); drawn only when
  what it shows changed (`itMapRefresh`'s key), never while hidden. Reach: Jumps shown from Near You's reach to `IT_MAP_MAX` (the
  Feed's largest), following the Feed until set; Near You's reach is a setting (`nearRange`, alert range to the Feed's, default
  alert + 5). Rings: standing colour, gang size (1 / 2–10 / 11+). Routes: one per system (BFS, neighbours in index order), hover
  dashed, press kept. One stepper for every range (`RS`, `rsHtml`, `rsPaint`). `intel_map_check.py`.
  v2026.11.04.1 (roadmap/map-ly-hover-plan.md): `INTEL_MAP.p3` holds CCP's 3D positions (0.0001 LY, int24) for the hover's
  "N.NN LY from <you>" (`itMapLy`, `itMapLyText`: rounded UP to 0.01, the owner). Your system: a pin drawn last
  (`itMapPinDraw`), the only filled label (YOU · name), a 1.6 s beacon on its own canvas (`itMapBeacon`; first draw and a jump
  seen while Intel was in front, `it.me.sysAt`; none with reduced motion), the "You" edge arrow (`itMapYouArrow`); the
  crosshair centers at the same zoom (`itMapCenter`); a jump keeps the zoom and centers. `intel_map_you_check.py`.
- **Kills and losses in the system** (v2026.11.02.3, Project doc roadmap/system-activity-plan.md): one zKillboard request per
  system an hour (`/kills/systemID/<id>/pastSeconds/259200/`), then killmails from ESI newest first to the window or
  `SA_ACT_KM_MAX` (300). The system: an Intel Assess's, else ⚙ (`saSet`, localStorage dscanSaSet): your location from Intel or a
  typed gate system (SYS-03). Every group, corporation, pilot and hull counts its own kills (once, whole value) and losses; NPCs
  count for nobody; folds show none. Numbers that link out use `zkLinkHtml(url, what, text)`; inside a button they are text only.
  `system_activity_check.py`.
- **Ships on Scan** (v2026.11.02.2, Project doc roadmap/scan-rail-plan.md): the D-Scan's hulls in a rail left of Local's results
  (sticky, ~320 px; full width with no Local; stacked on a phone), by role from the ESI group (`SCAN_ROLES`); Cyno Capable and the
  cyno tag come from `CYNO_FIT` (tools/gen_cyno_table.py, never typed by hand). On grid ≤ `SCAN_GRID_KM`; a "-" is "no reading", its
  own count. One hover card (`#scanCard`), built when it opens, from the numbers the old per-type cards showed. No pilot is ever
  tied to a hull. `scan_rail_check.py`.
- **Fleet fits on request** (v2026.11.02.1, Project doc roadmap/fleet-fit-budget-plan.md): opening a fleet asks zKillboard nothing
  (fits from a share link or kept from the last hour load at once); Damage on the kill has its own column beside the ship; the Fit
  column has Load per row and Load all above it (Common fits above 10 pilots: one request per alliance-and-hull pair, victims in it
  get their own fit free; Own fits up to 10), its exact cost in its label. Load all keeps `FK_ZKB_RESERVE` (25) of `ZKB_BUDGET`,
  refused when counted (`zkbFetchNow` `o.reserve`, which can only lower the cap). Rows stay in damage order until all are in.
  `fleet_fit_budget_check.py`.
- **No time to kill for a whole fleet** (v2026.10.31.1, the owner: "given the fluidity of ranges in fleet battles ... we probably
  should not be giving a time to kill numbers"): a fleet's fits are guesses and each ship picks its own range, so the Fleet tab and
  the System Analyzer show what a fleet brings and how far it reaches, never how long you or they last (LESSON #108). One ship
  against one ship (the Matchup) keeps its numbers.
Checked by `tools/check_ui_rules.py` (chain) and `tools/page_checks/ui_rules_check.py`. Status colours (error, IN SYSTEM)
wait for the colour inventory (backlog).

When you find a new kind of mistake, add it to `LESSONS_LEARNED.md` (the next
unused number, and one line in its Index under the matching group:
`tools/check_lessons_index.py` checks it) and give the history doc a "Lesson
for future models" section. A lesson a later one overturns stays, marked
"Superseded by #n" at its top and in the Index. In code, mark the site
with a `// LESSON #n` comment that points at the entry.

**Checks: run what the change needs** (v2026.10.30.2, the owner: "yep, do it"; picked automatically since page-unchanged
v2026.10.31.7, the owner: "yes please" to the review's "choose the level from the changed files, not by hand").
`python3 -I tools/run_checks.py --auto --since <the repo as last delivered>` (or with a .git folder, `--auto` alone: changes
since the last commit) runs the fast lints, then the tier `tools/check_picker.py` picks from the changed lines and files:
the engine, a PYFA CORE section or a calculation input (regression_suite/, the generators, the pyfa tools) -> `calc`; one
area's functions, CSS or info text -> `area` with those areas; shared code or anything unmapped -> `all`; every 5th delivery
-> `all`. `--plan` only says what it would run. Pick a tier by hand only to run more than it picks. When a section moves or a
new area gets its own prefix, update REGIONS / PREFIX / CSS in check_picker.py (its `--self-test`, a fast lint, says so).
The fast lints include the regression suite, the D-Scan parse tests (seconds) and a check that PYFA_SRC is the verified pyfa commit (LESSON #116). A page check gets 5 minutes (`SLOW` for
more). A new page check gets its areas in `AREAS` (`--check-tags`, a chain step). A check that keeps failing under load gets
its cause fixed (LESSON #115); while that's under way it may go in the ledger's Quarantine table (a reason, at most 14 days;
an expired one fails the run). Run with `--ledger` and fill in "Caught" in `tools/check_ledger.md` before delivering; every 10
rows, review it with the owner (slow checks that never catch anything go to `all` only; repeat flakes get fixed). A new feature
still gets its own targeted check and mutants.

**How the numbers are worked out, for people:** `METHODOLOGY.md` (was the "How effective HP and DPS are
calculated" note on the page, removed in v2026.10.14.51); each card's short version is its ⓘ panel (`CARD_INFO`).
Change both when a calculation's assumptions change.

**After finishing any task,** check `todo-inbox/` for new requests the
owner wrote down while you were working: `new-bugs.txt` and
`new-backlog-items.txt`. If either file has entries, add each one to the bug
list or the backlog, then remove those entries from the text file and tell the
owner what you added. If both are empty, say nothing about it.

**Adding a backlog item or bug (when the owner asks).** The backlog is not in this repo. It lives in Claude's project memory for
this Project; new items go in the newest backlog file (`areas/dscan-backlog-2.md` today), written with the memory tools in the
format `**Severity | Scope — Name** — [stated] "<the owner's words>"`, plus what's known and "Not started". Bugs go in the same
file, starting with `**BUG | …`. Never put the backlog in a repo file: the repo is public and the backlog quotes the owner.
**If you don't have the memory tools, say so and stop.** Tell the owner you can't add it to the backlog from here; don't write it
anywhere else.
Build queue: the Project docs folder `claude/build-queue/` holds prompts waiting to be built; read its README when the owner says to take the next item.
**`todo-inbox/` is the owner's drop box.** Agents read it and empty it; agents never write new items into it.
