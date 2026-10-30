# Check ledger

One row per delivery (`python3 -I tools/run_checks.py ... --ledger` appends it; fill in "Caught" by hand before delivering).
"Caught" is what a check stopped from reaching the repository: a real bug, named with the check that found it. Expectation
updates for intended changes and flaky runs are not catches. Reviewed every 10 rows (CLAUDE.md "Checks"): a slow check that
never catches anything moves to the `all` tier only; a check that keeps showing up as flaky gets fixed.

| Date (UTC) | Version | Run | Page checks | Minutes | Failed | Flaky (passed alone) | Caught |
|---|---|---|---|---|---|---|---|
| 2026-10-30 | v2026.10.30.2 | all, by hand before the runner existed | 48 | ~65 (chain ~40) | none (intel_check: 2 expectations updated for intended changes) | busy_check, request_gates_check, extension_check | intel_place_check + its 10 mutants (the new placement rules); check_pii (a ship-name term in an old lesson); screenshots (none this time). The chain and the other 47 page checks: nothing. |
