// PYFA CORE lock (see PYFA_CORE.md).
//
//   node tools/check_pyfa_core.mjs [index.html]            check (exit 1 on any problem)
//   node tools/check_pyfa_core.mjs [index.html] --update   record new fingerprints -- ONLY after
//                                                          running every section's `verify` commands
//
// index.html fences the code that replicates pyfa with
//   // ==== PYFA CORE BEGIN <id> ==== ...
//   // ==== PYFA CORE END <id> ====
// tools/pyfa_core_manifest.json lists every section with a SHA-256 of the lines
// between its markers, what pyfa code it mirrors, and how to verify it. The lock
// can't stop an edit; it makes an edit FAIL the regression suite until someone
// re-verifies the section against pyfa and records the new fingerprint, so a
// core change is always deliberate. Tool-specific behaviour (inputs, presentation)
// belongs OUTSIDE the fences.
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
export const MANIFEST_PATH = path.join(here, 'pyfa_core_manifest.json');
const BEGIN = /^\s*\/\/ ==== PYFA CORE BEGIN ([a-z0-9-]+) ====/;
const END = /^\s*\/\/ ==== PYFA CORE END ([a-z0-9-]+) ====\s*$/;

export function extractSections(htmlText) {
  const lines = htmlText.replace(/\r\n?/g, '\n').split('\n');
  const sections = {}, errors = [];
  let open = null;
  lines.forEach((line, i) => {
    const b = line.match(BEGIN), e = line.match(END);
    if (b) {
      if (open) errors.push(`line ${i + 1}: BEGIN ${b[1]} inside open section ${open.id}`);
      else if (sections[b[1]]) errors.push(`line ${i + 1}: section ${b[1]} appears twice`);
      else open = { id: b[1], start: i + 1, body: [] };
    } else if (e) {
      if (!open || open.id !== e[1]) errors.push(`line ${i + 1}: END ${e[1]} without matching BEGIN`);
      else { sections[open.id] = { start: open.start, end: i + 1, body: open.body.join('\n') }; open = null; }
    } else if (open) open.body.push(line);
  });
  if (open) errors.push(`section ${open.id} (line ${open.start}) has no END`);
  for (const s of Object.values(sections)) s.sha256 = crypto.createHash('sha256').update(s.body).digest('hex');
  return { sections, errors };
}

export function checkPyfaCore(htmlText, manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'))) {
  const { sections, errors } = extractSections(htmlText);
  const problems = [...errors], changed = [];
  for (const id of Object.keys(manifest.sections)) {
    if (!sections[id]) problems.push(`section ${id} is in the manifest but not fenced in index.html`);
    else if (sections[id].sha256 !== manifest.sections[id].sha256) changed.push(id);
  }
  for (const id of Object.keys(sections)) if (!manifest.sections[id]) problems.push(`section ${id} is fenced but not in the manifest`);
  for (const id of changed) problems.push(`section ${id} (lines ${sections[id].start}-${sections[id].end}) CHANGED since it was verified against pyfa ${manifest.pyfa.version}. ` +
    `Re-verify: ${manifest.sections[id].verify.join(' ; ')} -- then run check_pyfa_core.mjs --update`);
  return { ok: problems.length === 0, problems, sections, changed };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const htmlPath = args.find(a => !a.startsWith('--')) || path.join(here, '..', 'index.html');
  const html = fs.readFileSync(htmlPath, 'utf8');
  const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
  if (args.includes('--update')) {
    const { sections, errors } = extractSections(html);
    if (errors.length) { console.log(errors.join('\n')); process.exit(1); }
    for (const [id, s] of Object.entries(sections)) {
      if (!manifest.sections[id]) { console.log(`new section ${id}: add mirrors/kind/verify to the manifest by hand first`); process.exit(1); }
      if (manifest.sections[id].sha256 !== s.sha256) console.log(`updated ${id}`);
      manifest.sections[id].sha256 = s.sha256;
    }
    fs.writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + '\n');
    console.log('manifest written. Record what you verified in the history doc.');
  } else {
    const r = checkPyfaCore(html, manifest);
    console.log(r.ok ? `PYFA CORE: ${Object.keys(r.sections).length} sections match the manifest (verified against pyfa ${manifest.pyfa.version}, data ${manifest.pyfa.clientBuild})`
                     : 'PYFA CORE: PROBLEMS\n  ' + r.problems.join('\n  '));
    process.exit(r.ok ? 0 : 1);
  }
}
