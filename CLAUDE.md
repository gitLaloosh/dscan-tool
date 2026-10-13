# Notes for AI assistants working on this repo

D-Scan Analyzer is a single-file tool (`index.html`) that estimates EVE Online
ship stats from killmails and EFT fits. Its calculations must match **pyfa**
exactly, using primary sources only: pyfa's source code and CCP's SDE / live ESI.

Before changing any calculation:

1. Read `LESSONS_LEARNED.md`, the catalog of mistakes already made here.
   Follow its checklist **in order**: it's the definition of done, and the
   expected values are derived before any code is written.
2. Use `tools/` (see `tools/README.md`):
   - `tools/pyfa_effects.py` runs pyfa's real effect handlers so you find all
     of them. Don't grep or regex `effects.py`.
   - `tools/independent_checks/` derives expected values without the tool's
     own tables.
3. Run `node regression_suite/run_regression.mjs index.html`. It must print
   ALL PASS. Add a constructed golden fit for every new mechanism.
4. Bump the version tag in `header.hero` (`vYYYY.MM.DD.N`). Add a dated note
   to `dscan-tool-history/`.

When you find a new kind of mistake, add it to `LESSONS_LEARNED.md` and give
the history doc a "Lesson for future models" section. In code, mark the site
with a `// LESSON #n` comment that points at the entry.
