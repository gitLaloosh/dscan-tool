"""The page's Content-Security-Policy names its one inline script by sha256 (v2026.11.07.3, build queue 023; Project doc
roadmap/sso-hardening-plan.md; LESSON #145). Every edit to that script changes the hash, so this tool keeps it right.

    python3 -I tools/csp_hash.py --check [index.html]   -> 'CSP: ... 0 problems' (exit 1 on any problem)
    python3 -I tools/csp_hash.py --write [index.html]   -> puts the current script's hash in the meta tag
    python3 -I tools/csp_hash.py --self-test            -> the line-ending and policy cases below

Run --write after the last edit to index.html (CLAUDE.md's delivery steps); run_checks.py and the pre-commit hook run --check.

It fails when:
  * the hash in the meta tag isn't the hash of the script as the browser hashes it;
  * there isn't exactly one <script>, or the CSP meta tag doesn't come before it, or there's no referrer meta tag;
  * the policy isn't EXPECTED below (a change to the policy is a change to this file, reviewed with it), or script-src
    has 'unsafe-inline' or 'unsafe-eval'.

How the browser hashes it: the element's text, UTF-8. HTML parsing first turns CR LF and a lone CR into LF, so a copy checked
out on Windows with CRLF line endings (.gitattributes `text=auto`) still gets the hash of the LF text that GitHub Pages
serves. This tool does the same; hashing the raw CRLF bytes would write a hash that stops the live page from running.
"""
import sys, os, re, hashlib, base64

EXPECTED = ("default-src 'none'; script-src 'sha256-{hash}'; style-src 'unsafe-inline'; img-src https://images.evetech.net data: blob:; "
            "connect-src https://esi.evetech.net https://login.eveonline.com https://r2z2.zkillboard.com https://zkillboard.com; "
            "worker-src blob:; base-uri 'none'; form-action 'none'; object-src 'none'")
META_RX = re.compile(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">')
SCRIPT_RX = re.compile(r'<script\b[^>]*>(.*?)</script', re.S | re.I)


def script_hash(html):
    """The base64 sha256 the browser computes for the page's one inline script."""
    body = SCRIPT_RX.search(html).group(1)
    body = body.replace('\r\n', '\n').replace('\r', '\n')   # HTML's newline normalization, before the text is hashed
    return base64.b64encode(hashlib.sha256(body.encode('utf-8')).digest()).decode()


def problems(html):
    out = []
    scripts = list(re.finditer(r'<script\b', html, re.I))
    if len(scripts) != 1: out.append(f'{len(scripts)} <script> tags (the CSP allows exactly one, by hash)')
    m = META_RX.search(html)
    if not m: return out + ['no Content-Security-Policy meta tag']
    if scripts and m.start() > scripts[0].start(): out.append('the CSP meta tag comes after the script (it must come first)')
    if '<meta name="referrer" content="no-referrer">' not in html[:m.end() + 200]: out.append('no <meta name="referrer" content="no-referrer"> beside the CSP')
    pol = m.group(1)
    hm = re.search(r"script-src 'sha256-([A-Za-z0-9+/=]+|PENDING)'", pol)
    src = re.search(r'script-src ([^;]*)', pol)
    if src and re.search(r"'unsafe-(inline|eval)'", src.group(1)): out.append("script-src allows 'unsafe-inline' or 'unsafe-eval'")
    if not hm: return out + ["script-src has no 'sha256-...' source"]
    if pol != EXPECTED.format(hash=hm.group(1)): out.append('the policy differs from EXPECTED in tools/csp_hash.py (change both, deliberately)')
    if scripts and hm.group(1) != script_hash(html): out.append('the script hash is stale: run python3 -I tools/csp_hash.py --write')
    return out


def write(html):
    h = script_hash(html)
    return META_RX.sub(lambda m: f'<meta http-equiv="Content-Security-Policy" content="{EXPECTED.format(hash=h)}">', html, count=1), h


def self_test():
    page = '<head>\n<meta http-equiv="Content-Security-Policy" content="x">\n<meta name="referrer" content="no-referrer">\n</head><body><script>\nlet a = 1;\nlet b = 2;\n</script></body>'
    lf, h = write(page)
    bad = []
    if problems(lf): bad.append(f'a fresh hash has problems: {problems(lf)}')
    crlf = lf.replace('\n', '\r\n')
    if problems(crlf): bad.append(f'the CRLF copy of the same page fails: {problems(crlf)}')
    if write(crlf)[1] != h: bad.append('--write on a CRLF copy gives another hash than on the LF page')
    if not problems(lf.replace('let b = 2', 'let b = 3')): bad.append('an edited script passes with the old hash')
    if not problems(lf.replace("script-src '", "script-src 'unsafe-inline' '")): bad.append("'unsafe-inline' in script-src passes")
    if not problems(lf.replace('</body>', '<script>x()</script></body>')): bad.append('a second <script> passes')
    if not problems(lf.replace('zkillboard.com https', 'example.com https')): bad.append('a changed policy passes')
    if not problems(lf.replace('<meta name="referrer" content="no-referrer">', '')): bad.append('no referrer meta passes')
    print('CSP HASH SELF-TEST:', 'ok' if not bad else bad)
    return 1 if bad else 0


def main(argv):
    if '--self-test' in argv: return self_test()
    args = [a for a in argv if not a.startswith('--')]
    path = args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'index.html')
    raw = open(path, 'rb').read().decode('utf-8')
    if '--write' in argv:
        new, h = write(raw)
        if new != raw: open(path, 'wb').write(new.encode('utf-8'))
        print(f'CSP: script sha256-{h[:12]}... written' if new != raw else f'CSP: script sha256-{h[:12]}... already current')
        argv = ['--check']
    ps = problems(open(path, 'rb').read().decode('utf-8'))
    for x in ps: print('CSP ', x)
    print(f'CSP: {len(ps)} problems')
    return 1 if ps else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
