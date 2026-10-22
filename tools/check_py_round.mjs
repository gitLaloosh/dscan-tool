// Fuzz check: index.html's pyRound(x, nd) must round exactly like Python's round(x, nd), which is what pyfa's
// display rounding (eos/utils/round.py roundToPrec) uses: the exact binary value, ties to even.
// JavaScript's Math.round / toFixed / toLocaleString round ties up, so 262.5 would show 263 where pyfa shows 262.
// Also checks formatDurationShort() (time to empty) against pyfa's capacitorViewFull.py: "%ds" % t, or
// "%dm%ds" % divmod(t, 60) above 60 s -- both TRUNCATE, so 40.8 s shows "40s".
// Usage: node tools/check_py_round.mjs index.html   -> last line "N mismatches (M cases)"
import { readFileSync } from 'fs';
import { execFileSync } from 'child_process';

const html = readFileSync(process.argv[2] || 'index.html', 'utf8');
const m = html.match(/function pyRound\(x, nd = 0\)\{[\s\S]*?\n\}/);
if (!m) { console.log('pyRound not found in index.html'); console.log('1 mismatches (0 cases)'); process.exit(1); }
const pyRound = new Function(m[0] + '; return pyRound;')();

// Cases: exact ties at 0/1/2 decimals, values one ulp either side, the known tie values from golden fits, random values.
const cases = [];
const known = [262.5, 562.5, 312.5, 356.25, 81.25, 81.35, 2.675, 0.5, 1.5, 2.5, -2.5, -0.5, 12.5, 38.5, 0, -0.04, 1e-9, 123456.5];
for (const x of known) for (const nd of [0, 1, 2]) cases.push([x, nd]);
let seed = 12345;
const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
for (let i = 0; i < 3000; i++) {
  const nd = i % 3;
  const tie = (Math.floor(rnd() * 200000) + 0.5) / 10 ** nd;   // an exact decimal tie (not always exact in binary)
  cases.push([tie, nd], [tie * (1 + Number.EPSILON), nd], [tie * (1 - Number.EPSILON), nd]);
  cases.push([(rnd() - 0.3) * 10 ** Math.floor(rnd() * 7), nd]);
}
const py = 'import json,sys\nc=json.load(sys.stdin)\nprint(json.dumps([round(x,n) for x,n in c]))';
const ref = JSON.parse(execFileSync('python3', ['-I', '-c', py], { input: JSON.stringify(cases) }).toString());
let bad = 0;
cases.forEach(([x, nd], i) => {
  const got = pyRound(x, nd), want = ref[i];
  if (got !== want && !(got === 0 && want === 0)) { if (bad < 10) console.log(`  pyRound(${x}, ${nd}) = ${got}, Python round = ${want}`); bad++; }
});
// Time to empty, as pyfa shows it
const fm = html.match(/function formatDurationShort\(totalSec\)\{[\s\S]*?\n\}/);
const fds = fm ? new Function(fm[0] + '; return formatDurationShort;')() : null;
const times = [0, 0.4, 1, 40.8, 59.99, 60, 60.5, 61, 115.57, 2947.8];
for (let i = 0; i < 2000; i++) times.push(Math.round(rnd() * 400000) / 100);
const pyT = 'import json,sys\nprint(json.dumps([("%dm%ds" % divmod(t, 60)) if t > 60 else ("%ds" % t) for t in json.load(sys.stdin)]))';
const refT = JSON.parse(execFileSync('python3', ['-I', '-c', pyT], { input: JSON.stringify(times) }).toString());
times.forEach((t, i) => {
  const got = fds ? fds(t) : null;
  if (got !== refT[i]) { if (bad < 20) console.log(`  formatDurationShort(${t}) = ${got}, pyfa = ${refT[i]}`); bad++; }
});
console.log(`${bad} mismatches (${cases.length + times.length} cases)`);
process.exit(bad ? 1 : 0);
