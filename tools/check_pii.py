"""Personal data in the repository: block it before it is committed (v2026.10.14.101, LESSON #90).

    python3 -I tools/check_pii.py [repo folder]          every file in the folder (not .git), as the chain step does
    python3 -I tools/check_pii.py --staged               only the files staged for the next commit (the git pre-commit hook)

The repository is public (GitHub Pages). The owner, 2026-10-28: personal data must never be saved to it, and "any saved
data (including screen shots)" must be called out or refused. This check fails on:

  * a home folder with a real user name in it: C:\\Users\\<name>\\..., /Users/<name>/..., /home/<name>/... (a placeholder
    such as "...", "<user>" or %USERNAME% is fine);
  * an e-mail address (example.com / example.org and noreply addresses are fine);
  * something that looks like a credential: a private-key block, an EVE SSO / JWT token, a GitHub token, "Bearer <token>",
    or api_key / client_secret / refresh_token / access_token / password set to a value;
  * an image file anywhere but the two folders of game icons (img/fighter-abilities/, browser-extension/icons/): a
    screenshot never goes in the repository;
  * an image embedded in a page or document (a data: URI of 2 KB or more) that nobody has reviewed. Mockups show the
    real page with MADE-UP data; after looking at each picture (no real pilot, corporation, alliance, channel or chat
    text, no desktop or file paths), add its SHA-256 to tools/pii_reviewed_images.json with what it shows;
  * a personal term from tools/pii_terms.local.txt: one term per line (names, character names, the user name in a
    path, an alliance...). That file is git-ignored and stays on the owner's computer, so the list itself never becomes
    public; without it this rule is skipped and the check says so. PII_TERMS=<file> points at another copy.

Exit code 1 and one line per problem (file:line) when anything is found.
"""
import base64, hashlib, json, os, re, subprocess, sys

ROOT = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))
STAGED = '--staged' in sys.argv
SKIP_DIRS = {'.git', '__pycache__', 'node_modules'}
IMAGE_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tif', '.tiff', '.heic')
IMAGE_DIRS = ('img/fighter-abilities/', 'browser-extension/icons/')
TEXT_EXT = ('.html', '.htm', '.md', '.txt', '.json', '.js', '.mjs', '.py', '.css', '.eft', '.csv', '.yml', '.yaml', '.sh', '.sha256', '')
TERMS_FILE = os.environ.get('PII_TERMS') or os.path.join(ROOT, 'tools', 'pii_terms.local.txt')
REVIEWED = os.path.join(ROOT, 'tools', 'pii_reviewed_images.json')
SELF = {'tools/check_pii.py', 'tools/pii_reviewed_images.json', 'tools/pii_terms.local.txt'}

PLACEHOLDER = r'(?!\.\.\.|<|%USERNAME%|USERNAME\b|YOU\b|you\b|Public\b|Default\b|All Users\b|runner\b|claude\b)'
RULES = [
    ('a home folder with a user name', re.compile(r'\b[A-Za-z]:[\\/]{1,2}(?:Users|Documents and Settings)[\\/]{1,2}' + PLACEHOLDER + r'[^\\/\s"\'<>`]+', re.I)),
    ('a home folder with a user name', re.compile(r'(?<![\w.])/(?:Users|home)/' + PLACEHOLDER + r'[A-Za-z0-9._-]+')),
    ('an e-mail address', re.compile(r'\b[A-Za-z0-9._%+-]+@(?!example\.(?:com|org)\b)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b')),
    ('a private key', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('a token (JWT / EVE SSO)', re.compile(r'\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}')),
    ('a GitHub token', re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{30,}')),
    ('a bearer token', re.compile(r'\bBearer\s+[A-Za-z0-9._~+/-]{20,}')),
    ('a credential', re.compile(r'(?i)\b(?:api[_-]?key|client[_-]?secret|refresh[_-]?token|access[_-]?token|password|passwd)\b["\']?\s*[:=]\s*["\'][^"\'\s]{8,}["\']')),
]
NOREPLY = re.compile(r'noreply|no-reply', re.I)

def files():
    if STAGED:
        out = subprocess.run(['git', '-C', ROOT, 'diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z'], capture_output=True, text=True, check=True).stdout
        return [f for f in out.split('\0') if f]
    found = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn: found.append(os.path.relpath(os.path.join(dp, f), ROOT).replace(os.sep, '/'))
    return sorted(found)

def load_terms():
    if not os.path.exists(TERMS_FILE): return None
    terms = []
    for line in open(TERMS_FILE, encoding='utf-8'):
        t = line.strip()
        if t and not t.startswith('#'): terms.append(t)
    return re.compile(r'(?<![\w])(?:' + '|'.join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r')(?![\w])', re.I) if terms else None

def main():
    reviewed = json.load(open(REVIEWED, encoding='utf-8')).get('images', {}) if os.path.exists(REVIEWED) else {}
    terms = load_terms()
    problems, seen_images, n = [], set(), 0
    for rel in files():
        p = os.path.join(ROOT, rel)
        if rel in SELF or '.local.' in os.path.basename(rel) or rel.startswith('todo-inbox/') or not os.path.isfile(p): continue   # git-ignored: stays on this computer
        low = rel.lower()
        if low.endswith(IMAGE_EXT):
            if not low.startswith(IMAGE_DIRS): problems.append(f'{rel}: an image file outside the game-icon folders (a screenshot never goes in the repository)')
            continue
        if not low.endswith(TEXT_EXT): continue
        try: s = open(p, encoding='utf-8').read()
        except (UnicodeDecodeError, OSError): continue
        n += 1
        # embedded images: each one must have been looked at
        for m in re.finditer(r'data:image/[a-zA-Z+.-]+;base64,([A-Za-z0-9+/=]+)', s):
            raw = base64.b64decode(m.group(1) + '=' * (-len(m.group(1)) % 4))
            if len(raw) < 2048: continue
            h = hashlib.sha256(raw).hexdigest(); seen_images.add(h)
            if h not in reviewed:
                problems.append(f'{rel}:{s.count(chr(10), 0, m.start()) + 1}: an embedded image ({len(raw) // 1024} KB, sha256 {h[:12]}...) nobody has reviewed: look at it, then list it in tools/pii_reviewed_images.json')
        text = re.sub(r'data:image/[a-zA-Z+.-]+;base64,[A-Za-z0-9+/=]+', 'data:image', s)
        for why, rx in RULES:
            for m in rx.finditer(text):
                if why == 'an e-mail address' and NOREPLY.search(m.group(0)): continue
                problems.append(f'{rel}:{text.count(chr(10), 0, m.start()) + 1}: {why}: {m.group(0)[:60]!r}')
        if terms:
            for m in terms.finditer(text):
                problems.append(f'{rel}:{text.count(chr(10), 0, m.start()) + 1}: a personal term from pii_terms.local.txt')
    stale = sorted(set(reviewed) - seen_images) if not STAGED else []
    for p in problems: print('PII ', p)
    note = '' if terms else ' (no tools/pii_terms.local.txt here: personal names were not checked)'
    print(f'PERSONAL DATA: {n} text files read, {len(seen_images)} embedded images reviewed, {len(problems)} problems{note}'
          + (f'; {len(stale)} reviewed images no longer in any file (can be removed from the list)' if stale else ''))
    return 1 if problems else 0

if __name__ == '__main__':
    sys.exit(main())
