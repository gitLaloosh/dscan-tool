# R2Z2 relay plan (Intel kills through a small proxy)

Status: **proposed, 2026-10-29.** Nothing built yet. The owner reads this, then decides.

## Why

Intel's kills come from zKillboard's live feed, R2Z2: `https://r2z2.zkillboard.com/ephemeral/sequence.json` names the
newest number, and `ephemeral/<number>.json` is one kill each. Read from a web page, both go wrong at Cloudflare, which
sits in front of R2Z2:

1. **`sequence.json` is up to a day old.** Its documented cache is one day, and Cloudflare keeps a copy per website (per
   `Origin`). Checked 2026-10-29 ~16:40 UTC from the owner's browser at the same moment: asked from riftforeve.online,
   100278552 (Last-Modified that day 16:36); asked from gitlaloosh.github.io, 100263992 (Last-Modified the day before,
   17:56). zKillboard's FAQ says a new `sequence.json` is uploaded every 51 killmails, so a current copy is at most about
   50 behind.
2. **A number asked for before it is published stays "not found" for our site for about an hour.** Cloudflare keeps the
   404 for browser requests and doesn't clear it when the file appears. Controlled test, 17:16-17:19 UTC: 100279050 asked
   once from our site before it was published, then published (readable from another site), still not readable from
   ours; 100279052, not asked early, readable. Every "gap" seen that day (100274284-287, 100275281-299, 100277236-275,
   100278322-449) exists; each was a number our page had asked for too early. Following a live feed means asking for the
   next number before it exists, so the page loses exactly the newest kills, and v.29.5/29.6's read-ahead made it worse.

zKillboard's developer, in their Discord (#zkillboard-com), in July and again on 2026-10-29: it is a Cloudflare problem
with browser requests, and a proxy for both `sequence.json` and the kill files is the recommended path until Cloudflare
fixes it. Adding a query string to dodge the cache is refused (403); we saw the same.

RIFT (desktop, source read 2026-10-29) uses the same feed: start at `sequence.json`, read forward, wait 6 s on a 404,
and after 60 s with no kill re-read `sequence.json` and jump to it. A desktop app sends no `Origin`, so neither problem
reaches it. A relay gives the page the same view.

## zKillboard's guidance for readers (its Discord, July 2026, passed on by the owner)

- A 404 means the file isn't there: either not posted yet (sleep 6 s and ask again) or gone (files are kept at least
  24 hours; R2 doesn't remember that a file existed). Whether a 404 is "too soon" or "too late" is told by comparing the
  number with `sequence.json`.
- The developer's own reader: 404s on one number for 5 minutes or more (with the 6 s sleeps) means something has gone
  wrong, and it re-reads `sequence.json`. RIFT does the same after 60 s. Missed kills can be filled from the daily
  history dump (`history/raw/<date>.json`, now with full killmails), not needed for a 15-minute intel window.
- So with a current `sequence.json` a real gap is rare, and the page's reader can be the documented one plus a jump.

## What the relay is

A Cloudflare Worker (free plan), about 30 lines, in this repo at `tools/relay/r2z2-relay.js`, deployed by the owner to his
own Cloudflare account. The page asks the Worker; the Worker asks R2Z2 the way a desktop app does and hands the answer
back.

- **Two paths only:** `/sequence.json` and `/<number>.json` (digits only, at most 12). Anything else: 404, and nothing is
  fetched. Only `GET` (and `OPTIONS` for browsers). It never fetches any other host.
- **Upstream:** `https://r2z2.zkillboard.com/ephemeral/<same>`, with a descriptive User-Agent naming the tool and its
  repository (zKillboard asks for one; a blank one is blocked), no cookies, nothing from the visitor passed on.
- **Answers:** the upstream status (200, 404, 429) and body as they are; `Access-Control-Allow-Origin` only for `https://gitlaloosh.github.io` (and nothing for other sites);
  `Vary: Origin`.
- **Short caching at the relay, never a long-kept 404** (from an nginx reverse proxy another tool's author shared in
  zKillboard's Discord, which the owner passed on): the relay may keep `sequence.json` for 4 s, a kill file for 5 minutes
  (published files never change), a 404 for 6 s (zKillboard's own "wait 6 seconds"), a 429 for 12 s. Shared by everyone
  using the relay, that means fewer requests upstream. What reaches the browser: `sequence.json` and every 404 with
  `no-store`; a kill file may be kept by the browser (`max-age=300, immutable`). Done with the Worker's own cache
  options per status; to check against Cloudflare's docs that they work on a `workers.dev` address, and if not, no
  caching at the relay (fine for a few users).
- **Request headers whitelisted** (same source): only `Accept: application/json` and the User-Agent go upstream; the
  visitor's `Origin`, cookies, address and the rest are not passed on. Response headers from upstream are dropped except
  the body's type; Cloudflare's telemetry headers (`CF-RAY`, `NEL`, `Report-To` ...) are not passed back.
- **Query strings ignored,** so nobody can use the relay to dodge its cache.
- **No secrets, no storage, no logs of its own.** Nothing personal passes through it: kill numbers in, public killmails
  out. Cloudflare's own request logs are the only record (the owner's dashboard).

## Limits and costs

- Free plan: 100,000 Worker requests a day. One person with Intel on all day: about 15,000 (about one kill read and one
  "not yet" every 6 s). Enough for the owner and a few others; past that, the paid plan ($5 a month) or another way to
  share the load.
- zKillboard's limit is 15 requests a second per address. The page keeps its gate (one at a time, at most 10 a second),
  and with a current head it needs far fewer: about one request per new kill plus one every 6 s.
- To check before relying on it: whether R2Z2 sees all Worker requests as one address (Cloudflare's), and whether the
  Worker's requests are free of the stuck-404 problem. Test: through the Worker, ask for a number just before it is
  published, then just after.

## Page changes (one delivery, after the relay is live)

- A setting (the code, not the user) for the relay's address; R2Z2 read through it.
- RIFT's way, which the page could not use before:
  - start at `sequence.json`, read back about 15 minutes (as today) and forward to the newest;
  - live: ask for the next number; "not found", wait 6 s and ask again;
  - 60 s with no kill (RIFT's choice; zKillboard's developer uses 5 minutes): re-read `sequence.json`; if it is ahead of
    the number being waited on, the 404 was "too late" or a real gap: jump to it, reading the numbers in between that
    are still in the forget window. If it isn't ahead, the 404 is "too soon": keep waiting.
  - Removed: finding the newest by leaping and halving, the read-through, the windows further on, the back-off: all
    of it was a workaround for not knowing the head.
- The relay unreachable: a note on the Intel card with a new error code, and the page reads direct as a fallback
  (today's behaviour).
- `tools/check_request_gates.py` lists the relay as a new host behind `itKillTurn`.

## Checks

- The Worker: a Node test calling its handler with a stand-in `fetch`: only the two paths, only GET/OPTIONS, digits
  only, the headers above, the status passed through, never any other host.
- The page: `intel_kills_check.py` with the relay mocked: starts at `sequence.json`, reads forward, waits 6 s on a 404,
  jumps after 60 s without a kill, no number asked twice within 6 s, at most 12 a second, fallback with the note.
- Live, once deployed: the stuck-404 test above, then a few kills from RIFT checked against the Feed.

## The owner's steps (once the script is written)

1. Create a free Cloudflare account (cloudflare.com, sign up).
2. Workers & Pages, Create, "Hello World" Worker; name it, for example `eta-r2z2`.
3. Edit code, replace everything with `tools/relay/r2z2-relay.js`, Deploy.
4. Send the Worker's address (`https://eta-r2z2.<your-subdomain>.workers.dev`). It is not secret: the page will contain
   it, and the repository is public.

## Open questions

- The Worker's name and whether to use a custom domain later.
- Whether to keep the direct-read fallback once the relay has proved itself.
