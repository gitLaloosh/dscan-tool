# Local and fleet assessment (plan, decided 2026-10-27; steps 1-3 built in v2026.10.14.81-.83)

Started 2026-10-27. the owner, after "what do you think is the biggest gap in the tool right now?" (the tool sizes up one
pilot at a time; a fight is usually against a group) and "what happens when there are 100+ people in system?": "I've been
contemplating how to do something like this as a way to assess matchups in doctrines at a larger scale. this seems like a
good place to start. we'll also want to have the ability for the user to have their own alliance affiliation saved so any
friendly pilots can be filtered out when assessing potential threats."

## What exists today

- **Pilot Analyzer:** one pilot; their likely hull from their recent losses; the fit of each of their last 3 losses in
  that hull, every number pyfa's; the Matchup against your ship. Opens from links (#pilot=, #zkill=, the extension).
- **D-Scan tab:** the hulls on scan and their counts, base resists by hull. It doesn't know who flies them.
- **My Ships:** up to 20 saved fits, one in use.
- **The engine:** any fit (pasted or from a killmail) to pyfa's numbers; one ship against one ship (damage application,
  webs and scrams, time to kill).

## Facts the plan rests on (checked 2026-10-27)

- ESI `POST /universe/ids/`: names to IDs with their category (characters, corporations, alliances, types). The tool
  already sends at most 500 names per request, so a big local goes in batches.
- ESI `POST /characters/affiliation/`: up to 1000 character IDs per request, giving each one's corporation, alliance
  (left out when the corporation has none) and faction warfare faction. It fails as a whole if any ID isn't a character,
  so only IDs that /universe/ids/ called characters go in.
  ([esi-issues #719](https://github.com/esi/esi-issues/issues/719))
- In-game standings and contacts can't be read without logging in (ESI's contacts endpoints need EVE SSO), so the
  friendly list is what the user enters. Logging in could fill it later; see L7.
- zKillboard's API ([wiki](https://github.com/zKillboard/zKillboard/wiki/API-(Killmails))): modifiers combine in any order,
  so `/losses/allianceID/<id>/shipTypeID/<id>/` gives one alliance's losses in one hull; results are killmail ID + hash
  (zkbOnly), newest first, up to 1000 per page; `/pastSeconds/` up to 7 days in whole hours. No published rate limit:
  "Do not hammer the server with API requests. Be polite", space requests out, cache locally. CORS is enabled. (A browser
  can't set a User-Agent header, as the wiki asks of tools; requests come with the browser's own.)
- Killmails themselves come from ESI with the ID and hash, cached by the tool forever (they never change).

## The two inputs (the owner 2026-10-27)

the owner's picture: "a local system tab with two inputs for a dscan and a copy/paste of the local chat window ... identified
non-blues in system and what they're likely flying. best case, gives an outline of what kind of fleet is there and it's
makeup." And on how far each can be trusted: "a dscan result is going to be far less reliable in the following sense: it
has a very limited range in system from the player's ship (~14 AU). The local chat window will show everyone in the
entire system, in space or docked up."

So:
- **Local is the complete list of who's in system** (in space or docked), but says nothing about what they're flying.
- **D-Scan is a partial view** (about 14 AU around your ship) of ships really in space now, but says nothing about who
  flies them.
- The system-wide picture (who, and what they likely fly) is built from **local**; D-Scan only adds "this much of it is
  in space near you now" (and a ✓ on a pilot whose likely hull is on scan). The fleet outline is never read off the scan
  alone: a scan that shows 5 Ferox doesn't mean the fleet is 5 Ferox, and a pilot not on scan may be docked or out of
  range, not gone.

## Phases (proposed)

**L1. Your side (friendlies), saved.** Enter your pilot name: the tool looks up its corporation and alliance (ESI
affiliation) and saves them. Add more friendly alliances or corporations by name (coalition, blues). Saved in this
browser only. Used everywhere: a friendly pilot opened in the Pilot Analyzer says so; friendlies are set aside in local.

**L2. Local list.** Paste local's member list (select the members in the Local window, Ctrl+C). The tool resolves every
name and its affiliation (two ESI requests for up to 500 pilots) and shows the hostiles grouped by alliance, then
corporation, with counts; unaffiliated pilots listed; friendlies collapsed into one count. ESI only, a second or two.
Every pilot opens the Pilot Analyzer.

**L3. Small gangs: one row per hostile pilot.** Up to a threshold (D3), each hostile gets a row: their likely hull and fit
summary (DPS by type, EHP, weakest resist, tackle / EWAR). zKillboard requests go through one polite queue, spaced out,
cached in the browser; rows fill in as answers come, likeliest threats first. With a D-Scan pasted too, each pilot's
likely hulls are matched against what's on scan. The hull guess also uses their recent kills (what they fly now; a good
pilot rarely dies, so losses alone can be old).

**L4. Fleets: by alliance, not by pilot.** Above the threshold, the makeup is estimated per hostile alliance (and large
corporation) in local, from what that group has been flying lately: its recent kills and losses on zKillboard (one
request each, then the killmails from ESI, cached; the hulls its pilots flew, by count), so "Alliance A, 62 in local,
lately flying mostly Ferox with Scimitar logi". For each of those hulls, the alliance's recent losses in it give the
common fit (D5), run through the engine. The D-Scan then says how much of that is in space near you (e.g. "on scan: 18
Ferox, 4 Scimitar") without being taken as the whole fleet (see "The two inputs"). Individual pilots stay one click away.
(Revised 2026-10-27 after the owner's note on D-Scan range: the first draft read the fleet's makeup off the scan.)

**L5. Their fleet against your ship.** Combined incoming DPS by damage type, webs / points / neuts, their logistics; how
long you last under it. Against a fleet that's seconds, so the useful answers are "don't take this", what to kill first,
what counters it.

**L6. Doctrine matchups (the owner's larger goal).** Your fleet against theirs: your side as a set of fits with counts (My
Ships, or your alliance's own common fits by the L4 method) against their composition. Fleet-level numbers each way:
total DPS by type against their resists, how fast each side breaks the other's ships, application (signature and speed
against weapon types), logistics. pyfa has no fleet simulation, so these are the tool's own numbers built from pyfa's
per-ship numbers (DEVIATIONS.md section 3, like the time to kill). Needs its own design discussion.

**L7 (later, optional). Log in with EVE.** EVE SSO (no secret needed in a public repo: the PKCE flow) to read your
alliance's contacts and fill the friendly list from real standings. the owner 2026-10-27: "not something i'd like to do now
because we'll need to do some real security analysis of the tool first". What it would take (CCP's docs, checked
2026-10-27: [SSO](https://developers.eveonline.com/docs/services/sso/),
[native / PKCE flow](https://docs.esi.evetech.net/docs/sso/native_sso_flow.html)):

- **Register the app** on CCP's developer portal (the owner's account): name, the callback address (the GitHub Pages URL),
  the scopes; an app can only ever request the scopes it was registered with. The client ID it gets is public and can sit
  in the repo; with PKCE there is no secret.
- **Log in with EVE button:** to login.eveonline.com with a PKCE code challenge (S256, the only method accepted; a code
  verifier of 32 random bytes, base64url) and a `state` value (against forged logins); the pilot is picked and the scopes
  approved there; back on the page with a one-time code (5 minutes), traded for tokens with the code verifier and client
  ID. **To confirm first:** that CCP's token endpoint answers a browser page (CORS); their PKCE doc is written for desktop
  and mobile apps.
- **Checking the login:** the access token is a JWT signed by the SSO (RSA): check the signature against the keys at the
  `jwks_uri` of CCP's metadata endpoint, `iss` (https://login.eveonline.com/ or login.eveonline.com), `aud` (the client ID
  and "EVE Online"), `exp`. `sub` is `EVE:CHARACTER:<id>`, `name` the pilot, `scp` the scopes granted.
- **Tokens:** an access token lasts 20 minutes; the refresh token is long-lived and "volatile" (a new one may come with
  every refresh). Where it's kept is the main security decision: memory / the browser session (log in each visit) or
  local storage (stays logged in; readable by any script that gets onto the page). Log out revokes it.
- **What it would unlock** (scope names to confirm at registration): contacts and standings
  (`esi-alliances.read_contacts.v1` and the corporation / character ones) for the friendly list (L1);
  saved fittings (`esi-fittings.read_fittings.v1`) as My Ships; the ship you're in (`esi-location.read_ship_type.v1`) as
  My Ship; your skills (`esi-skills.read_skills.v1`) instead of all V: the biggest gain and the biggest job (the engine
  assumes V everywhere; it would need pyfa-matched work and checks of its own).
- **Security analysis before it** (the owner's condition): an audit that every piece of zKillboard / ESI text shown is escaped
  (script injection is what would expose tokens); a Content Security Policy as a meta tag (GitHub Pages can't send
  headers) limiting which hosts the page may talk to and blocking injected scripts; the fewest scopes, each added with the
  feature that needs it; tokens sent only to ESI, never to zKillboard or anything else; the browser extension never
  touching tokens (it only opens links); a clear log-out that revokes.
- **Size:** about one delivery for the login and the friendly list from contacts, after the security pass; each further
  scope a small feature; real skills a project of its own.

## Decisions to make (one at a time)

- **D1. Where it lives — decided:** one tab with both inputs (the owner: "a local system tab with two inputs") that replaces
  the D-Scan tab (the owner: "it should replace it"); with only a scan pasted it does what the D-Scan tab does today. Named
  **"System Analyzer"** (the owner: "System Analyzer sounds fine"), in the D-Scan tab's place (last).
- **D2. Friendlies — decided** (the owner: "your suggestion for friendlies sounds fine for now"): your pilot name sets your corp
  and alliance (ESI affiliation, saved in this browser); more friendly alliances / corporations added by name; friendlies
  collapsed into one line you can open; a friendly opened in the Pilot Analyzer is tagged. **Neutral and hostile shown
  separately** (the owner: "just for the sake of evaluating accuracy or identifying gaps initially. if it doesn't seem
  necessary, we can combine the two later"). Open: what makes a pilot hostile rather than neutral, since standings can't
  be read without a login (D2b).
- **D2b. Hostile vs neutral — decided** (the owner: "that sounds right"): both, the user's list winning. (1) A hostile list the
  user enters (alliances / corporations, like the friendly list). (2) Evidence from zKillboard: groups that killed your
  side lately (your alliance's recent losses: one zKillboard request for the list, then the killmails from ESI, cached;
  their attackers' alliances and corporations), shown with the reason ("killed 3 of yours this week"). Everyone else not
  friendly = neutral. **After the EVE login (L7):** real standings replace the hand-entered lists for pilots who log in
  (negative standing = hostile). The hand-entered lists stay for anyone who doesn't log in (the login is optional). The
  zKillboard evidence stays too: standings say who your side has declared hostile, the evidence says who has actually
  been shooting you, so a neutral with kills on your side is still worth flagging. the owner asked whether this part would be
  deprecated then: to decide when L7 is built.
- **D3. Small gang / fleet threshold — decided** (the owner: "let's have it be configurable but default to 15. that way we can
  easily change it later on w/out a code change"): up to 15 hostile + neutral pilots in local, one row each (L3); more than
  that, the fleet view (L4). The number is a setting in the System Analyzer, saved in this browser beside the friendly and
  hostile lists; the default (15) is one constant in the code.
- **D4. zKillboard pacing, cache and limits — decided** (the owner asked "should we add constraints to prevent users from
  flooding zkillboard with requests from the tool? some of these systems can have hundreds of names in local", then
  "sounds good, record them as D4"). Each number is one constant, set low on purpose, to loosen after real use:
  - **Per paste:** per-pilot lookups only in small-gang mode; the threshold setting (D3, default 15) can't go above
    **30**. The fleet view looks up only the **5 largest** hostile / neutral groups (alliance, or corporation without one):
    1 request for each group's recent activity + at most **3** for its main hulls' common fits, so **~20 requests at
    most** however big local is; smaller groups and loners show names and affiliations (ESI only) with a click to look
    one up. A **per-paste ceiling of 30** zKillboard requests; past it, "load more" instead of carrying on.
  - **Across the page:** **one zKillboard queue** for everything (System Analyzer, Pilot Analyzer, last kill, shared
    links): one request at a time, **about 1 second apart**, identical requests merged. A **rolling budget of 100
    requests per 10 minutes per browser**, kept across reloads; when spent, "zKillboard limit reached, more in N min",
    with everything cached or ESI-only still working.
  - **Back-off:** an error or timeout pauses the queue 60 s (ZKB_COOLDOWN_MS today), longer on each repeat, up to
    **about 10 minutes**.
  - **Not asking twice:** zKillboard answers cached **1 hour** in the browser (the tool's existing IndexedDB cache);
    killmails cached forever (they never change); a Refresh button skips the cache. **Nothing in the background**:
    every request follows something the user did (no auto-refresh, no polling).
  - These are in a public page's code, so they keep normal use polite, as zKillboard asks; they can't stop someone
    who edits the code, and zKillboard has its own protections.
- **D5. "Common fit" — decided** (the owner: "i'd like this method", plus the top three variants: "some groups have similar
  fits for AB variants vs MWD variants for example. similar fits but propulsion could change the dynamic of the encounter
  drastically. or long range sniping fits vs up close blaster fits for the same hull"):
  - **Source:** the group's **20 most recent losses** in that hull, whatever their age (zKillboard's time filter stops at 7
    days, too few losses for most groups); the span shown, e.g. "from 20 losses, Sep 2 – Oct 26".
  - **Method:** fits grouped by their **exact set of fitted modules** (drones included, cargo not); loaded ammo = the most
    common charge in each weapon among the fits of that group. Ties: the most recent first.
  - **Up to three variants**, most common first, each with its share ("9 of 20", "6 of 20", "3 of 20") and **what differs
    from the first** (e.g. "MWD instead of AB", "railguns instead of blasters", "2 Damage Control → Multispectrum"), so an AB
    and an MWD version, or a sniper and a brawler version, of the same hull show as separate choices. The user picks the
    variant that feeds the fleet numbers; the most common one by default. A variant needs at least 2 losses; if no fit
    repeats, the latest loss is shown with "fits vary: showing the latest".
  - **No per-slot majority:** every fit shown is a real one from a real killmail (stitching each slot's most common module
    can make a fit nobody flew).
  - The share is the confidence: 15 of 20 is a strict doctrine, 3 of 20 a rough guide.
- **D6. Order of building — decided** (the owner: "that works"): **L1 + L2** first (friendlies and the local list; ESI only,
  useful alone), then **L3** (small-gang rows from the Pilot Analyzer), then **L4 + L5** (fleets and common fits, under
  the D4 limits; the fleet against you), then **L6** (doctrine matchups). L7 (EVE login) waits for the security analysis.
  Each step is its own version, mocked up first for the owner to decide on.

- **D7. Step 1 details — decided** (the owner's answers to the mockup, 2026-10-27): **Your Side is a chip beside My Ship**,
  on every tab ("A: chip by My Ship"); **the zKillboard evidence comes in step 1** ("Yes, in step 1"); for coalitions,
  **"Paste a list of alliances"** and **"Suggested friendlies"** both; up to 6 pilot names per corporation then
  "+N more", and the names System Analyzer / Your Side / Hostile / Neutral / Friendly / On Scan ("Both fine").

- **D8. Step 2 (L3) details — decided** (the owner's answers to the pilot-rows mockup, 2026-10-27, all as recommended):
  **"A: Pilots / Groups switch"** (in a small gang the rows replace the columns; Groups brings them back); likely ship
  **"Most recently seen"** (newest ship on a kill or loss in 30 days, a ship of theirs on the D-Scan first, else the
  hull lost most); **"Hull only, fit unknown"** when they have no loss of that hull; order **"Hostile first, then DPS"**.

- **D9. Step 3 (L4) details — decided** (the owner's answers to the fleet-view mockup, 2026-10-27, all as recommended): a
  group's hulls lately from its **"Newest 50 kills"** (1 request); **"Show ≈ counts"** (share × the group's count in
  local, labeled an estimate); the **"Their fleet, estimated"** summary now; **"L4 now, L5 next"** (their fleet against
  your ship is its own version).

- **D10. Step 4 (L5) details — decided** (the owner's answers to the "Against your ship" mockup, 2026-10-27, all as
  recommended; mockup `Claude outputs/against_your_ship_mockup.html`): the card in **the Fleet and the Pilots views**
  (a small gang added up the same way, each row's fit counted once); **all estimated ships by default, with an "On
  scan" switch** and the on-scan time beside; **one range for all of them** (5 / 10 / 20 / 30 / 50 km, starting at
  your own guns' best range) plus **Still / MWD on**; **kill order by the damage each puts on you per second of your
  fire**, logistics first. Without a saved ship the card asks for My Ship.

## Step 1 as built (v2026.10.14.81)

- **Tab:** the D-Scan tab is the System Analyzer (CARD_NAMES `sysan`), last; Local and D-Scan boxes side by side, one
  Analyze (both run together; either alone works), Clear, Show parsed rows. The scan's contacts are unchanged, under
  "On Scan" (`onscan`). A scan or a fit pasted in the Local box: SYS-02.
- **Your Side** (`side`, localStorage `dscanSide`): your pilot (SIDE-01 if unknown) sets corp + alliance, looked up again
  on every Analyze of Local; friendly and hostile lists by name, one at a time or a pasted list (tickers in < > or [ ]
  ignored; not found SIDE-02; your own groups refused); a group added to one list leaves the other; suggested friendlies
  (on a button: your side's kills in 7 days, the newest 50 killmails, groups on 2+ of them, not already listed, 8 at
  most); pilot rows up to (1-30, default 15). A phone shows the chip as your ticker and the panel as a bottom sheet.
- **Sides** (`sideOf`): corporation entries first (yours, friendly list, hostile list), then alliance entries, then the
  evidence, else neutral. A hostile corporation inside a friendly alliance is hostile and grouped by itself.
- **Local:** /universe/ids/ (500 names each), /characters/affiliation/ (1000 each; SYS-01), /universe/names/; tickers
  from /alliances/{id}/ and /corporations/{id}/ afterwards (IndexedDB `orgs`, a week). Summary: total, a bar and counts
  per side, "Fleet" / "Small gang" by the threshold, names not found. Hostile and Neutral columns by alliance then
  corporation, largest first; NPC corporations one neutral group; with more than 6 neutral groups the groups of 1-2
  pilots share one row; Friendly one line (closed). Each name opens the Pilot Analyzer.
- **Evidence (D2b):** zKillboard /losses/allianceID/{id}/pastSeconds/604800/ (or corporationID without an alliance), kept
  an hour (IndexedDB `zkb`), the newest 50 killmails from ESI (IndexedDB `killmails`, forever); every attacking pilot's
  alliance (or corporation) counts once per killmail; NPCs and NPC corporations never. "Killed N of yours in 7 days"
  ("of your last 50 losses" when there were more). Refresh skips the hour's copy; a failure leaves the lists working
  and says why (ZKB-05 or the zKillboard code).
- **zKillboard queue (D4), for the whole page:** one request at a time, 1 s apart; the same URL at once asked once;
  100 per 10 minutes per browser (localStorage `dscanZkbBudget`), then ZKB-04; the pause after a failure doubles from
  60 s up to 10 minutes. The 1-hour copy covers the System Analyzer's requests; the Pilot Analyzer keeps its own
  per-visit lists and its Refresh losses button as before.
- **Pilot Analyzer:** a Friendly / Hostile tag beside the pilot's name when Your Side is set (one affiliation request).
- **Checks:** `tools/page_checks/system_analyzer_check.py` with `sa_mocks.py` (made-up data; expected values worked out
  in Python).

## Step 2 as built (v2026.10.14.82)

- **Pilots** (`pilots`, the card in a small gang: hostile + neutral at most "pilot rows up to"), with a Pilots / Groups
  switch on the summary line. One row per pilot: side, name, alliance ticker and corporation; likely ship with its class
  and why ("on a kill 2 h ago", "lost one 3 d ago", "on scan; ...", "2 of 3 losses, latest 40 d ago"); DPS (the Pilot
  Analyzer's rule: a range when charges are guessed from cargo) with a bar by damage type; EHP; weakest resist; EWAR
  letters (T D C B); "✓ on scan". A row opens the Pilot Analyzer on that pilot and hull. A phone shows each as a card.
- **v2026.10.14.84:** the column is **"Possible ship"**, not "Likely ship" (the owner: "for now, we need to change 'likely
  ship' to 'possible ship'. some of the suggestions are from data that is months old"). The info panel says the
  fallback (the hull lost most) can be months old and that the line under the ship says when it was seen.
- **Per pilot:** zKillboard /kills/characterID/{id}/ and /losses/characterID/{id}/ (kept an hour, through the queue),
  the newest 5 kills and 10 losses from ESI (kept forever). Capsules, shuttles, rookie ships and MTUs don't count. The
  numbers: their newest loss in that hull through `estimateHpAndDps` (as the Pilot Analyzer); no loss of it among those
  10: the bare hull, "fit unknown", no DPS. No history: "No kills or losses on zKillboard: a new pilot or an alt".
- **Batches (D4):** 15 pilots per paste (2 requests each = 30), then "Load N more pilots". Rows keep the order they were
  asked in (hostile groups first) while they fill, then sort once: hostile first, then DPS (fit unknown, then no
  history, last). Three pilots are looked up at a time; the zKillboard queue keeps them 1 s apart.
- **Checks:** `tools/page_checks/pilot_rows_check.py` (histories built from golden-fit killmails: DPS and EHP checked
  against the pyfa-verified pins; the ship rules against `sa_mocks.expected_rows()`).

## Step 3 as built (v2026.10.14.83)

- **Fleet** (`fleet`): above "pilot rows up to", a Fleet / Groups switch (Fleet first). The 5 largest hostile / neutral
  groups (not NPC corporations or the folded small groups) are looked up, shown hostile first then neutral, largest
  first; the rest under "Not looked up" with a Look up button each.
- **A group:** its 50 newest kills (zKillboard, kept an hour; killmails from ESI, kept forever); every attacker of
  that group with a pilot counts the hull flown (ships only; capsules, shuttles, rookie ships, MTUs left out). The 3
  main hulls: share, "≈" = share × the group's count in local, "✓ N on scan" (the D-Scan's count of that type).
- **Common fit (D5)** per main hull: the group's 20 newest losses in it (1 request); exact set of fitted modules
  (high, mid, low, rigs, subsystems; drone and fighter types without counts; charges, scripts and cargo not part of
  it); variants of 2+ losses, up to 3, by count (ties: newest); the newest loss of the variant with each weapon given
  the variant's most common charge; "what differs" in short words (MWD / AB, railguns / blasters, scram / point / web,
  or the module's name); "a strict doctrine" at 3 of 4 or more; no variant: the newest loss ("Fits vary"); no losses:
  "fit unknown". Numbers through `estimateHpAndDps`; › opens the fit in the Fit Analyzer (EFT).
- **Their fleet, estimated:** over the main hulls with a fit, ≈ count × the picked variant: raw DPS and damage types,
  the weakest resist of most counted ships, ships with T / D / C / B, logistics (hull classes Logistics / Force
  Auxiliary).
- **Requests (D4):** 4 per group at most (kills + 3 hulls' losses), so 20 for the 5; Look up adds 4.
- **Checks:** `tools/page_checks/fleet_view_check.py` (kills and losses built from golden-fit killmails; numbers
  against the pyfa-verified pins, shares / counts / summary against `sa_mocks.expected_fleet()`). Next step: L5,
  their fleet against your ship.

## Step 4 as built (v2026.10.14.85)

- **Where (D10):** the card **Against Your Ship** (`vs`) under "Their fleet, estimated" in the Fleet view, and above the
  rows in the Pilots view (each row with a fit counted once; "fit unknown" rows not). No ship saved: it asks for My
  Ship (its button opens the panel); "Use in assessments" off: it says to turn it on.
- **Settings:** Range 5 / 10 / 20 / 30 / 50 km, starting at the step nearest your guns' best range (dmgDefaultRangeM, as
  the Damage Application card); You: Still / MWD on (orbiting at full speed, your prop on); Count: All ≈N / On Scan: N
  (min of the D-Scan count and the ≈ count per hull). A new ship in My Ship starts again from its best range.
- **Per ship:** the Matchup's pieces (mysFight: pyfa's application both ways, their webs and paints, assumed charges;
  "they last" by the time-to-kill rule). **Added up:** their applied DPS by damage type × count, "you last" through
  your layers by the same rule, your capacitor by pyfa's capSim with their running neuts and nosferatus in reach added
  as pyfa adds projected ones (amount × calculateRangeFactor, cycle = duration, one drain per copy per ship).
  DEVIATIONS.md says what isn't applied (your Energy Warfare Resistance, a capital neut's signature resolution).
- **Shown:** the verdict ("Don't take this fight." when you go before the first ship on the list breaks; "You'd break
  about N before you go."; "You could break all of them first."; "You hold against all of it here."), You last (the
  other count's time beside), DPS applied to you with the damage-type bar and how much of their raw DPS lands, Holding
  you (T: scram or web reaching you; C: neuts or nosferatus), Your capacitor, Their logistics, and Kill first (6 rows:
  logistics, then their DPS on you ÷ the time you take to break one; why in a few words).
- **Checks:** `tools/page_checks/vs_check.py` (every number worked out again in the page through `mysMatchup`,
  `capSimPyfa` and drains written from pyfa; 11 mutants caught). Next: L6 (doctrine matchups) needs its own design
  talk; L7 (login) later.

## Step 4 status: hidden (v2026.10.14.88)

the owner (todo-inbox, 2026-10-27): "The assumptions in the 'against your ship' section on the system analyzer tab just aren't
reliable. in limited use so far, I've found it to be inaccurate and even misleading. probably need to back it out until it
can be refined a bit more." Then: "a lot of pilots simply fly a wide variety of hulls and/or do not get killed very often.
taking a guess and what ship multiple pilots could be flying and getting any number of those wrong, can result in some
wildly inaccurate assumptions resulting in poor decision making."

- The card is switched off (`saVsOn = false`); its code and `vs_check.py` stay, so a refined version starts from tested
  pieces. Nothing else changed: the Pilots / Fleet views still say "Possible ship" and "≈".
- Why it misled: every counted ship is a guess twice over (the hull from killmail history, the fit from losses), and the
  card adds the guesses up into one verdict, so wrong guesses compound instead of averaging out.
- To discuss before it comes back (not decided): count only what's certain (hulls on your D-Scan, with the fit as
  the only guess), say how much of the fleet the numbers cover, no verdict when that's low; ties to the backlog items on
  hulls seen on kills, non-combat ships and ships named after a pilot in Local.
- the owner's context for that talk (2026-10-27): "in some cases you might see a 50:50 split between friendlies and enemies in
  local while maybe 10% or 20% of that number shows up as ships on d-scan (maybe less). friendlies will fly many of those
  same hulls because good pvp hulls are good pvp hulls." So a hull on D-Scan can't be pinned to a side or a pilot by its
  type alone, and D-Scan shows a small part of Local: "only what's certain" may cover very little.

## Checks (as for every delivery)

ESI and zKillboard mocked as in `killmail_mocks.py` (enforcing the real contracts: 500 / 1000 limits, affiliation failing
on a non-character, LESSON #71); page checks per phase; the engine's numbers stay pyfa's (the per-ship checks); the
common-fit method checked against a hand-built set of losses; fleet-level numbers against an independent calculation.

## Status: building, login stays L7 (2026-10-27)

the owner: "go ahead with the System Analyzer but do not make the login the first step. I will think about the login bit at a
later time but for now let's go ahead and build the rest out. login can remain as #7". So the D6 order stands (L1 + L2,
L3, L4 + L5, L6; L7 later); the "login first" proposal below is not taken. The mockup questions below still need answers
before step 1 is built.

## Earlier status: on hold (2026-10-27), after the step 1 mockup

Mockup of step 1 (L1 + L2): `Claude outputs/system_analyzer_mockup.html` (the real v2026.10.14.80 page; the System
Analyzer part mocked with made-up names). It shows two inputs side by side (Local, D-Scan) with one Analyze; a local
summary (total, hostile / neutral / friendly bar, "Fleet: N hostile + neutral" over the D3 threshold, names not found);
Hostile and Neutral columns grouped by alliance then corporation (NPC corporations their own neutral group; each pilot
opens the Pilot Analyzer); Friendly collapsed to one line; "On Scan" = today's D-Scan contacts unchanged; a Friendly tag
beside the pilot's name in the Pilot Analyzer. Colours: hostile = --danger, friendly = new #4f8fe0 (the pair passes
validate_palette.js on #161c22 and #12171c), neutral grey on purpose; every side also has a shape (− square, ○ circle,
+ square) and its name.

the owner: "is it worth waiting to do this until we have eve login? seems like the usefulness would greatly increase. i am in a
large coalition and this implementation will have a lot of non-alliance coalition members resolve to being neutrals."
Then: "preserve what we have decided so far ... maybe we can work on something else while i think about this one."

Proposed, then declined by the owner (above): build the login (L7) **before** step 1, since the alliance's contacts carry the coalition's
blues; everything in step 1 except where friendlies come from is the same either way. Order: (1) **check first** that
CCP's token endpoint (`https://login.eveonline.com/v2/oauth/token`) accepts a browser page's request (CORS); CCP's docs
describe PKCE for "mobile and desktop applications" and don't mention browsers or CORS; if it doesn't, a login needs a
small server of our own and this plan changes. Not checkable from Claude's workspace (its network can't reach CCP); can be
run from the browser pane on the owner's computer with one harmless request. (2) the security pass (L7). (3) app registration
on the owner's account; confirm there that any member can read the alliance contacts (no in-game role). (4) login + friendly /
hostile lists from standings. (5) step 1 with standings, the hand-entered lists for anyone not logged in (D2b).

Ideas for coalitions without a login (not decided): paste a whole list of alliance names into the friendly list at once;
**suggested friendlies** from zKillboard: alliances that often appear alongside yours on your alliance's kills ("on 14
of your kills this week"), added with one click; same single request as the D2b evidence, reading kills not losses.

Open questions from the mockup (unanswered): Q1 Your Side as a chip beside My Ship on every tab (A, recommended) or a
card in the System Analyzer (B); Q2 the zKillboard evidence in step 1 or with L3 (1 request per Analyze, cached 1 hour,
up to the 50 most recent losses from ESI); Q3 up to 6 pilot names per corporation then "+N more"; Q4 new CARD_NAMES:
"System Analyzer", "Your Side", "Hostile", "Neutral", "Friendly", "On Scan".
