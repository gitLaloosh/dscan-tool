"""LESSONS_LEARNED.md's index lists every entry once (v2026.10.30.2). In the update-check chain.

    python3 -I tools/check_lessons_index.py [LESSONS_LEARNED.md]          # must end with "0 problems"

The owner, 2026-10-30, on the file's size: "how much work is that for an agent? ... is it all still relevant?" The file is read
through its index (one line per entry, grouped by task); the entries keep their permanent numbers (`// LESSON #n` comments). Fails
when an entry is missing from the index or listed twice, the index names a number with no entry, two entries share a number, a
number is skipped, or an index line's words no longer match its entry's title (rename one, rename both).
"""
import sys, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
path = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'LESSONS_LEARNED.md'))
s = open(path, encoding='utf-8').read()
problems = []
m = re.search(r'^## Index \(read this first\)\n(.*?)\n---\n', s, re.M | re.S)
if not m: sys.exit('LESSONS_LEARNED.md has no "## Index (read this first)" section ending with ---')
idx, body = m.group(1), s[m.end():]
heads = re.findall(r'^## (\d+)\. (.+)$', body, re.M)
nums = [int(n) for n, _ in heads]
title = {}
for n, t in heads:
    if int(n) in title: problems.append(f'#{n}: two entries share the number')
    title[int(n)] = t.strip()
for n in sorted(set(range(1, max(nums) + 1)) - set(nums)): problems.append(f'#{n}: no entry with this number (numbers are permanent; never skip or reuse one)')
listed = re.findall(r'^- #(\d+) (.+)$', idx, re.M)
seen = {}
for n, text in listed:
    n = int(n); seen[n] = seen.get(n, 0) + 1
    if n not in title: problems.append(f'index #{n}: no entry with this number'); continue
    if not text.startswith(title[n].rstrip('.?:')): problems.append(f'index #{n}: "{text[:50]}" no longer matches the entry\'s title "{title[n][:50]}"')
for n, c in seen.items():
    if c > 1: problems.append(f'index #{n}: listed {c} times')
for n in sorted(set(title) - set(seen)): problems.append(f'#{n} "{title[n][:60]}": not in the index')
for p in problems: print('PROBLEM', p)
print(f'LESSONS INDEX: {len(title)} entries, {len(listed)} index lines; {len(problems)} problems')
sys.exit(1 if problems else 0)
