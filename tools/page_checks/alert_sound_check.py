"""Intel's alert sounds: two slots, five sounds, your own file, one volume (v2026.11.01.8).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/alert_sound_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "volume control for the intel alerts. they're a little quiet. would like to be able to turn them up manually" and "add
ability for user to pick their own alert sound for the intel alerts"; his answers in the Project doc roadmap/alert-sound-plan.md:
"the five", "different sounds for near you and in system would be fantastic", 70% to start ("sure"), your own file up to 1 MB and
5 s ("yes"). No real audio anywhere: the page gets a stand-in AudioContext that records every node, frequency, gain and start/stop
time (files are decoded by the browser's own OfflineAudioContext), and the only sound files are tones generated here. Checks:
  * switching Intel on wakes the audio (the press), so the first alert isn't silent;
  * the slot by jumps: a threat in your own system (a kill too) plays In system (Klaxon), one 1 jump or more Near You (Chime);
  * each of the five builds and lasts about a second at most; Chime is today's sound, number for number (880 then 660 Hz, the
    same envelope and times), and at 50% its loudness is today's 0.25;
  * the volume: the one master gain is (p/100)² (70% to start: 0.49); 0% plays nothing; the Sound switch off plays nothing;
  * the notification is silent when the page's own sound plays, not when Sound is off;
  * the gear: Near You and In system, each with its sound and ▶ Test, the volume with its %, disabled while Sound is off;
    ▶ Test plays that slot and wakes the audio;
  * your own file: a generated 1-second WAV is decoded and played, a 7-second one stops at 5 s; over 1 MB is refused (INTEL-09),
    something that isn't sound is refused (INTEL-10), the slot keeping its sound; it's kept in its own IndexedDB database
    (dscan-intel-sounds, not the ESI cache; one made without its store gets it) and survives a reload; a kept file that
    can't be played falls back (INTEL-10);
    × removes it and its entry;
  * settings saved before this version load with the defaults (70%, Chime, Klaxon);
  * 390 px: the rows inside the box, 44 px controls; no page errors; nothing sent anywhere.
v2026.11.01.7 fails (one sound, no volume, no slots).
"""
import sys, os, re, io, json, math, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

def wav(seconds, rate=8000, f=440):   # a generated tone (never a real recording)
    n = int(seconds * rate)
    data = b''.join(struct.pack('<h', int(8000 * math.sin(2 * math.pi * f * i / rate))) for i in range(n))
    return b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVEfmt ' + struct.pack('<IHHIIHH', 16, 1, 1, rate, rate * 2, 2, 16) + b'data' + struct.pack('<I', len(data)) + data

STAND_IN = r"""(() => {
  const P = class { constructor(){ this._v = 1; this.ev = []; } set value(v){ this._v = v; this.ev.push(['set', v]); } get value(){ return this._v; }
    setValueAtTime(v, t){ this.ev.push(['at', v, t]); } exponentialRampToValueAtTime(v, t){ this.ev.push(['exp', v, t]); } linearRampToValueAtTime(v, t){ this.ev.push(['lin', v, t]); } };
  class N { constructor(c, k){ this.context = c; this.kind = k; this.out = []; c.log.push(this); } connect(n){ this.out.push(n); return n; } }
  class O extends N { constructor(c){ super(c, 'osc'); this.type = 'sine'; this.frequency = new P(); } start(t){ this.t0 = t; } stop(t){ this.t1 = t; } }
  class G extends N { constructor(c){ super(c, 'gain'); this.gain = new P(); } }
  class S extends N { constructor(c){ super(c, 'src'); this.buffer = null; } start(t){ this.t0 = t; } stop(t){ this.t1 = t; } }
  class C { constructor(){ this.log = []; this.currentTime = 10; this.state = 'suspended'; this.destination = {kind: 'dest'}; window.__ac = this; window.__acN = (window.__acN || 0) + 1; }
    createOscillator(){ return new O(this); } createGain(){ return new G(this); } createBufferSource(){ return new S(this); }
    resume(){ this.state = 'running'; window.__resumed = (window.__resumed || 0) + 1; return Promise.resolve(); }
    decodeAudioData(ab){ return new OfflineAudioContext(1, 1, 8000).decodeAudioData(ab); } }
  window.AudioContext = C; window.webkitAudioContext = C;
  window.__notes = [];
  window.Notification = class { constructor(t, o){ window.__notes.push([t, o]); } static get permission(){ return 'granted'; } static requestPermission(){ return Promise.resolve('granted'); } };
})();"""
SOUND = """(mark) => { const L = window.__ac ? window.__ac.log.slice(mark) : [], t = window.__ac ? window.__ac.currentTime : 0;
  const osc = L.filter(n => n.kind === 'osc'), src = L.filter(n => n.kind === 'src');
  return {osc: osc.map(o => ({type: o.type, f: o.frequency.ev, t0: +(o.t0 - t).toFixed(3), t1: +(o.t1 - t).toFixed(3)})),
    gains: L.filter(n => n.kind === 'gain' && n !== window.__master).map(g => g.gain.ev.map(e => e.map(x => typeof x === 'number' ? +(x - (x > 5 ? t : 0)).toFixed(4) : x))),
    src: src.map(s => ({t0: +(s.t0 - t).toFixed(3), t1: +(s.t1 - t).toFixed(3), dur: s.buffer && +s.buffer.duration.toFixed(2)})),
    master: typeof itMasterG !== 'undefined' && itMasterG ? +itMasterG.gain.value.toFixed(4) : null}; }"""
MARK = "() => window.__ac ? window.__ac.log.length : 0"
FAKE_ALERT = """([j, kill]) => { window.__j = j; window.itThreat = () => true; window.itMySys = () => 30004759; window.itJumps = () => window.__j;
  it.alerted = new Map(); it.set.range = 3;
  const e = kill ? {kind: 'kill', kill: {victim: {name: 'Made Up', ship: {name: 'Rifter'}}, value: 0}} : {kind: 'line', who: 'Scout', raw: 'made-up report'};
  window.__notes = []; itAlert({sys: 30000100 + j, kind: 'seen'}, e); return window.__notes.map(n => n[1].silent); }"""

with sync_playwright() as p:
    b = p.chromium.launch()
    errs, reqs = [], []
    def new_ctx(w):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}); ctx.add_init_script(STAND_IN)
        ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx)
        ctx.on('request', lambda r: reqs.append(r.url) if r.url.startswith('http') and 'images.evetech' not in r.url and 'fonts.' not in r.url else None)
        return ctx
    ctx = new_ctx(1480)
    pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(600)
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(300)
    d = pg.evaluate("() => [it.set.volume, it.set.soundNear, it.set.soundHere, it.set.sound, !!window.__ac]")
    check(d == [70, 'chime', 'klaxon', True, False], f'defaults: 70%, Near You Chime, In system Klaxon, Sound on; no audio made before a sound {d}')
    pg.evaluate("() => itStart()"); pg.wait_for_timeout(200)   # the switch pressed (here without a folder: it stops at "choose the folder")
    w = pg.evaluate("() => [!!window.__ac, window.__ac && window.__ac.state, window.__resumed || 0]")
    check(w == [True, 'running', 1], f'Intel switched on: the audio woken by that press, so the first alert isn\'t silent {w}')
    # ---- the slots by jumps
    m = pg.evaluate(MARK); n0 = pg.evaluate(FAKE_ALERT, [0, False]); s0 = pg.evaluate(SOUND, m)
    m = pg.evaluate(MARK); nk = pg.evaluate(FAKE_ALERT, [0, True]); sk = pg.evaluate(SOUND, m)
    m = pg.evaluate(MARK); n2 = pg.evaluate(FAKE_ALERT, [2, False]); s2 = pg.evaluate(SOUND, m)
    check(s0['osc'] and all(o['type'] == 'sawtooth' for o in s0['osc']) and sk['osc'] and all(o['type'] == 'sawtooth' for o in sk['osc'])
          and [o['f'][0][1] for o in s2['osc']] == [880, 660], f'In system (0 jumps, a kill too): Klaxon; 2 jumps: Near You, Chime ({[o["type"] for o in s0["osc"]]}, {[o["type"] for o in sk["osc"]]}, {[o["f"] for o in s2["osc"]]})')
    check(n0 == [True] and nk == [True] and n2 == [True], f'the notification is silent when the page played its sound {n0} {nk} {n2}')
    # ---- Chime: today's numbers; the master gain
    pg.evaluate("() => { it.set.volume = 50; }")
    m = pg.evaluate(MARK); pg.evaluate("() => itPlaySound('near')"); c = pg.evaluate(SOUND, m)
    want_osc = [{'type': 'sine', 'f': [['set', 880]], 't0': 0, 't1': 0.18}, {'type': 'sine', 'f': [['set', 660]], 't0': 0.18, 't1': 0.36}]
    want_g = [[['at', 0.0001, 0], ['exp', 1, 0.02], ['exp', 0.0001, 0.16]], [['at', 0.0001, 0.18], ['exp', 1, 0.2], ['exp', 0.0001, 0.34]]]
    check(c['osc'] == want_osc and c['gains'] == want_g and c['master'] == 0.25, f"Chime is today's sound: 880 then 660 Hz, the same envelope and times; at 50% its peak is today's 0.25 ({c['master']})\n      page {c['osc']} {c['gains']}")
    for v, want in ((70, 0.49), (30, 0.09), (100, 1.0)):
        pg.evaluate("(v) => { it.set.volume = v; }", v); pg.evaluate("() => itPlaySound('near')")
        mg = pg.evaluate("() => +itMasterG.gain.value.toFixed(4)")
        check(mg == want, f'volume {v}%: the master gain is (p/100)² = {want} ({mg})')
    pg.evaluate("() => { it.set.volume = 0; }")
    m = pg.evaluate(MARK); r0 = pg.evaluate("() => itPlaySound('near')"); z = pg.evaluate(SOUND, m); nz = pg.evaluate(FAKE_ALERT, [2, False])
    check(r0 is False and not z['osc'] and nz == [False], f'0%: nothing played, the notification not silent {r0} {z["osc"]} {nz}')
    pg.evaluate("() => { it.set.volume = 70; it.set.sound = false; }")
    m = pg.evaluate(MARK); nf = pg.evaluate(FAKE_ALERT, [0, False]); zf = pg.evaluate(SOUND, m)
    check(not zf['osc'] and nf == [False], f'Sound off: nothing played; the notification as today (not silent) {nf}')
    pg.evaluate("() => { it.set.sound = true; }")
    # ---- the five
    five = {}
    for k in ('chime', 'ping', 'triple', 'klaxon', 'sonar'):
        pg.evaluate("(k) => { it.set.soundNear = k; }", k)
        m = pg.evaluate(MARK); pg.evaluate("() => itPlaySound('near')"); x = pg.evaluate(SOUND, m)
        five[k] = (len(x['osc']), max(o['t1'] for o in x['osc']) if x['osc'] else None, sorted({o['type'] for o in x['osc']}))
    check(all(v[0] >= 1 and v[1] is not None and 0.1 <= v[1] <= 1.0 for v in five.values()) and five['triple'][0] == 3 and five['klaxon'][2] == ['sawtooth'] and five['sonar'][0] == 3 and five['ping'][0] == 1,
          f'the five each build and last about a second at most {five}')
    pg.evaluate("() => { it.set.soundNear = 'chime'; it.set.volume = 70; itWriteSet(); itRender(); }"); pg.wait_for_timeout(200)
    # ---- the gear's rows
    G = """() => { const r = [...document.querySelectorAll('#intelPanel .it-snd-r')]; return r.map(x => [x.querySelector('.it-snd-l').textContent, (x.querySelector('select') || {}).value || null,
      !!x.querySelector('[data-it-test]'), (x.querySelector('.it-vol-v') || {}).textContent || null, [...x.querySelectorAll('select, button, input')].every(c => c.disabled)]); }"""
    g = pg.evaluate(G)
    check(g == [['Near You', 'chime', True, None, False], ['In system', 'klaxon', True, None, False], ['Volume', None, False, '70%', False]], f'the gear: Near You and In system with their sound and ▶ Test, the volume with its % {g}')
    pg.click('#intelPanel [data-it-set="sound"]'); pg.wait_for_timeout(200)
    g2 = pg.evaluate(G); op = pg.evaluate("() => getComputedStyle(document.querySelector('#intelPanel .it-snd')).opacity")
    check(all(r[4] for r in g2) and op == '0.45', f'Sound off: the sound rows disabled, at 45% {[r[4] for r in g2]} {op}')
    pg.click('#intelPanel [data-it-set="sound"]'); pg.wait_for_timeout(200)
    pg.evaluate("() => { if(window.__ac) window.__ac.state = 'suspended'; window.__resumed = 0; }")
    m = pg.evaluate(MARK); pg.click('#intelPanel [data-it-test="here"]'); pg.wait_for_timeout(100); t = pg.evaluate(SOUND, m)
    check(t['osc'] and all(o['type'] == 'sawtooth' for o in t['osc']) and pg.evaluate("() => window.__resumed") >= 1, f'▶ Test (In system): Klaxon at this volume, the audio woken {len(t["osc"])}')
    pg.select_option('#intelPanel [data-it-snd="near"]', 'sonar'); pg.wait_for_timeout(200)
    sv = pg.evaluate("() => [it.set.soundNear, JSON.parse(localStorage.getItem('dscanIntel')).soundNear, document.activeElement && document.activeElement.dataset.itSnd]")
    check(sv == ['sonar', 'sonar', 'near'], f'a sound picked: kept, saved, the focus still on it {sv}')
    pg.evaluate("() => { const r = document.querySelector('#intelPanel [data-it-vol]'); r.value = 40; r.dispatchEvent(new Event('input', {bubbles: true})); r.dispatchEvent(new Event('change', {bubbles: true})); }"); pg.wait_for_timeout(200)
    vv = pg.evaluate("() => [it.set.volume, document.querySelector('#intelPanel .it-vol-v').textContent, JSON.parse(localStorage.getItem('dscanIntel')).volume]")
    check(vv == [40, '40%', 40], f'the volume slider: 40%, shown and saved {vv}')
    pg.select_option('#intelPanel [data-it-snd="near"]', 'chime'); pg.wait_for_timeout(200)
    # ---- your own file
    def pick(slot, name, data, mime):
        with pg.expect_file_chooser() as fc:
            pg.select_option(f'#intelPanel [data-it-snd="{slot}"]', 'file')
        fc.value.set_files(files=[{'name': name, 'mimeType': mime, 'buffer': data}]); pg.wait_for_timeout(1200)
    ROW = "(sl) => [it.set[sl === 'here' ? 'soundHere' : 'soundNear'], (document.querySelector(`#intelPanel [data-it-snd=\\\"${sl}\\\"]`) || {}).value, [...document.querySelectorAll('#intelPanel .it-snd-f span')].map(x => x.textContent), [...document.querySelectorAll('#intelPanel .it-snd-e')].map(x => x.textContent)]"
    IDB = """(k) => indexedDB.databases().then(l => !l.some(d => d.name === 'dscan-intel-sounds') ? null : new Promise(res => { const r = indexedDB.open('dscan-intel-sounds'); r.onsuccess = () => { const db = r.result; if(!db.objectStoreNames.contains('sounds')) return res(null); const g = db.transaction('sounds').objectStore('sounds').get(k); g.onsuccess = () => res(g.result ? [g.result.name, g.result.blob.size] : null); g.onerror = () => res('err'); db.close(); }; r.onerror = () => res('err'); }))"""
    big = wav(70)
    pick('near', 'big-horn.wav', big, 'audio/wav')
    rb = pg.evaluate(ROW, 'near')
    check(len(big) > 1048576 and rb[0] == 'chime' and rb[1] == 'chime' and rb[3] and 'INTEL-09' in rb[3][0] and pg.evaluate(IDB, 'near') is None, f'over 1 MB ({len(big)} bytes): refused (INTEL-09), Near You keeps Chime {rb}')
    pick('near', 'notes.mp3', b'this is not sound ' * 200, 'audio/mpeg')
    rn = pg.evaluate(ROW, 'near')
    check(rn[0] == 'chime' and rn[3] and 'INTEL-10' in rn[3][0], f'not sound: refused (INTEL-10), Near You keeps Chime {rn}')
    one = wav(1)
    pick('near', 'tone-1s.wav', one, 'audio/wav')
    r1 = pg.evaluate(ROW, 'near'); db1 = pg.evaluate(IDB, 'near')
    m = pg.evaluate(MARK); pg.evaluate("() => itPlaySound('near')"); f1 = pg.evaluate(SOUND, m)
    check(r1[0] == 'file' and r1[1] == 'file' and r1[2] == ['tone-1s.wav'] and not r1[3] and db1 == ['tone-1s.wav', len(one)] and f1['src'] == [{'t0': 0, 't1': 1.0, 'dur': 1.0}] and not f1['osc'],
          f'a 1-second WAV: decoded, kept in dscan-intel-sounds, shown with ×, played whole {r1} {db1} {f1["src"]}')
    seven = wav(7)
    pick('here', 'tone-7s.wav', seven, 'audio/wav')
    m = pg.evaluate(MARK); pg.evaluate("() => itPlaySound('here')"); f7 = pg.evaluate(SOUND, m)
    check(f7['src'] == [{'t0': 0, 't1': 5.0, 'dur': 7.0}], f'a 7-second file: stopped at 5 s {f7["src"]}')
    caches = pg.evaluate("() => indexedDB.databases ? indexedDB.databases().then(l => l.map(d => d.name)) : null")
    check(caches is None or ('dscan-intel-sounds' in caches), f'its own database {caches}')
    # reload: kept
    pg.reload(); pg.wait_for_timeout(1200); pg.click('#tabBtnIntel'); pg.wait_for_timeout(400)
    rr = pg.evaluate(ROW, 'near')
    m = pg.evaluate(MARK); pg.evaluate("() => itPlaySound('near')"); pg.wait_for_timeout(500); fr = pg.evaluate(SOUND, m)
    check(rr[0] == 'file' and rr[2] == ['tone-1s.wav', 'tone-7s.wav'] and fr['src'] and fr['src'][0]['dur'] == 1.0, f'after a reload: still your files, read once and played {rr} {fr["src"]}')
    # × removes it and its entry
    pg.click('#intelPanel [data-it-sndx="near"]'); pg.wait_for_timeout(400)
    rx = pg.evaluate(ROW, 'near'); dbx = pg.evaluate(IDB, 'near')
    check(rx[0] == 'chime' and rx[1] == 'chime' and rx[2] == ['tone-7s.wav'] and dbx is None, f'× removes the file and its entry: back to Chime {rx} {dbx}')
    # a kept file that can't be played: falls back
    pg.evaluate("""() => new Promise(res => { const r = indexedDB.open('dscan-intel-sounds'); r.onsuccess = () => { const tx = r.result.transaction('sounds', 'readwrite');
      tx.objectStore('sounds').put({blob: new Blob(['broken'], {type: 'audio/mpeg'}), name: 'old.mp3'}, 'near'); tx.oncomplete = () => res(1); }; })""")
    pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('dscanIntel')); s.soundNear = 'file'; s.sndPrev = {near: 'ping', here: 'klaxon'}; localStorage.setItem('dscanIntel', JSON.stringify(s)); }")
    pg.reload(); pg.wait_for_timeout(1200); pg.click('#tabBtnIntel'); pg.wait_for_timeout(400)
    m = pg.evaluate(MARK); pg.evaluate("() => itPlaySound('near')"); pg.wait_for_timeout(600); fb = pg.evaluate(SOUND, m); rf = pg.evaluate(ROW, 'near')
    check(rf[0] == 'ping' and rf[3] and 'INTEL-10' in rf[3][0] and fb['osc'] and fb['osc'][0]['f'][0][1] == 1320 and pg.evaluate(IDB, 'near') is None,
          f'a kept file that can\'t be played: Near You falls back to its sound before (Ping), says so (INTEL-10), and the file goes {rf} {[o["f"] for o in fb["osc"]]}')
    # settings from before this version
    pg.evaluate("() => localStorage.setItem('dscanIntel', JSON.stringify({channels: [], range: 3, sound: true, notify: true, forget: 15}))")
    pg.reload(); pg.wait_for_timeout(800)
    od = pg.evaluate("() => [it.set.volume, it.set.soundNear, it.set.soundHere, it.set.sndPrev]")
    check(od == [70, 'chime', 'klaxon', {'near': 'chime', 'here': 'klaxon'}], f'settings saved before this version: the defaults {od}')
    ctx.close()
    # ---- phone
    ctx = new_ctx(390); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(600)
    # a database of that name already there without its store (made by something else): the page adds the store
    pg.evaluate("() => new Promise(res => { const r = indexedDB.open('dscan-intel-sounds', 1); r.onsuccess = () => { r.result.close(); res(1); }; })")
    pg.reload(); pg.wait_for_timeout(600); pg.click('#tabBtnIntel'); pg.wait_for_timeout(300)
    pick('near', 'tone-1s.wav', one, 'audio/wav')
    check(pg.evaluate(IDB, 'near') == ['tone-1s.wav', len(one)], 'a database of that name without its store: the page adds it and keeps the file')
    pg.click('#intelPanel [data-it-sndx="near"]'); pg.wait_for_timeout(300)
    ph = pg.evaluate("""() => { const box = document.querySelector('#intelPanel .it-snd').closest('.it-box').getBoundingClientRect();
      const c = [...document.querySelectorAll('#intelPanel .it-snd select, #intelPanel .it-snd button')].map(x => x.getBoundingClientRect());
      return [c.every(r => r.height >= 44), c.every(r => r.right <= box.right + 1 && r.left >= box.left - 1), document.documentElement.scrollWidth]; }""")
    check(ph[0] and ph[1] and ph[2] <= 390, f'390 px: 44 px controls inside the box, nothing off the page {ph}')
    ctx.close()
    reqs = [u for u in reqs if not re.match(r'https://esi\.evetech\.net/latest/status/\?datasource=tranquility$', u)]   # v2026.11.04.3: the page's own, once per load (item data after a patch)
    check(not reqs, f'nothing sent anywhere by the sounds {reqs[:3]}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
