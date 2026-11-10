#!/usr/bin/env python3
"""Ad hoc probes for suspected defects in the linter. Audit scaffolding, not shipped."""
import re
import sys
from pathlib import Path

sys.path.insert(0, "/home/ubuntu/docs-style/skill/docs-review/scripts")
sys.path.insert(0, "/home/ubuntu/docs-style/skill/docs-lint/scripts")
import lint as sc  # noqa: E402

CORPUS = Path("/home/ubuntu/style-corpus")
pages = [sc.parse_page(p) for p in sorted(CORPUS.rglob("*.md"))]


def head(label, rows, n=8):
    print(f"\n=== {label} ({len(rows)} hits)")
    for r in rows[:n]:
        print("  ", r)


# 1. CONTRACTION_RE on possessives
poss = [
    (str(p.path.name), s)
    for p in pages
    for _, s in sc.sentences(p)
    if (m := sc.CONTRACTION_RE.search(s)) and m.group(0).lower().endswith("'s")
]
head("contraction regex firing on -'s (possessive or contraction?)", [s for _, s in poss])

# 2. callout emoji heuristic: what markers does it flag?
markers = {}
for p in pages:
    for lineno, line in p.prose_lines:
        m = sc.CALLOUT_RE.match(line.strip())
        if not m:
            continue
        mk = m.group(1)
        if any(ord(ch) > 0x2000 for ch in mk) and not any(s in mk for s in sc.SANCTIONED_CALLOUTS):
            markers.setdefault(mk, []).append(f"{p.path.name}:{lineno} {line.strip()[:60]}")
print("\n=== callout-emoji flagged markers")
for mk, hits in sorted(markers.items(), key=lambda kv: -len(kv[1])):
    print(f"   {mk!r} U+{ord(mk[0]):04X} x{len(hits)}  e.g. {hits[0]}")

# 3. sentence splitting: abbreviation breakage
abbrev = [
    s
    for p in pages
    for _, s in sc.sentences(p)
    if re.search(r"\b(e\.g|i\.e|vs|etc|Inc|U\.S|No)\.$", s)
]
head("sentences ending at an abbreviation (bad split)", abbrev)

# 4. object-capitalization: how often is the title-exclusion the only thing suppressing it,
#    and does `break` hide additional violations?
multi = 0
for p in pages:
    for _, s in sc.sentences(p):
        hits = [o for o in sc.OBJECTS if re.search(rf"\b{o.lower()}s?\b", s)]
        if len(hits) > 1:
            multi += 1
print(f"\n=== sentences containing >1 lowercase object (only first reported): {multi}")

suppressed = [
    (p.path.name, o, s)
    for p in pages
    for _, s in sc.sentences(p)
    for o in sc.OBJECTS
    if re.search(rf"\b{o.lower()}s?\b", s) and o.lower() in p.title.lower()
]
head("lowercase object suppressed only because it appears in the page title", suppressed)

# 5. shorthand: contexts
for short in sc.SHORTHAND:
    hits = [s for p in pages for _, s in sc.sentences(p) if re.search(rf"\b{short}s?\b", s)]
    if hits:
        print(f"\n=== shorthand {short}: {len(hits)}")
        for s in hits[:3]:
            print("   ", s[:110])

# 6. acronym check claims "first use" but scans whole page
mismatch = []
for p in pages:
    prose = " ".join(line for _, line in p.prose_lines)
    for a in sc.ACRONYMS_NEEDING_DEFINITION:
        uses = [(ln, s) for ln, s in sc.sentences(p) if re.search(rf"\b{a}\b", s)]
        if not uses:
            continue
        defs = [m.start() for m in re.finditer(rf"\([^)]*{a}[^)]*\)", prose)]
        first_use = prose.find(a)
        if defs and min(defs) > first_use + 40:
            mismatch.append(f"{p.path.name}: {a} first used at {first_use}, defined at {min(defs)}")
head("acronym defined LATER than first use but still passes", mismatch)

# 7. currency: what triggers currency-mixed
cur = []
for p in pages:
    prose = " ".join(line for _, line in p.prose_lines)
    if re.search(r"\$\s?\d", prose) and set(re.findall(r"\b\d[\d,.]*\s?(USD|EUR|GBP|CAD|MXN|JPY|AUD|SGD)\b", prose)):
        cur.append(p.path.name)
head("currency-mixed pages", cur)

# 8. passive regex: mine (preposition-gated) vs write-good/Vale (participle list)
IRREG = "awoken been born beat become begun bent beset bet bid bidden bound bitten bled blown broken bred brought broadcast built burnt burst bought cast caught chosen clung come cost crept cut dealt dug dived done drawn dreamt driven drunk eaten fallen fed felt fought found fit fled flung flown forbidden forgotten forgone forgiven forsaken frozen gotten given gone ground grown hung heard hidden hit held hurt kept knelt knit known laid led leapt learned left lent let lain lighted lost made meant met misspelt mistaken mown overcome overdone overtaken overthrown paid pled proven put quit read rid ridden rung risen run sawn said seen sought sold sent set sewn shaken shaven shorn shed shone shod shot shown shrunk shut sung sunk sat slain slept slid slung slit smitten sown spoken sped spent spilt spun spit split spread sprung stood stolen stuck stung stunk stridden struck strung striven sworn swept swollen swum swung taken taught torn told thought thrived thrown thrust trodden understood upheld upset woken worn woven wed wept wound won withheld withstood wrung written".split()
WG = re.compile(r"\b(?:am|are|were|being|is|been|was|be)\b\s*(\w+ed|" + "|".join(IRREG) + r")\b", re.I)
mine = wg = both = 0
only_wg = []
for p in pages:
    for _, s in sc.sentences(p):
        a = bool(sc.passive_span(s))
        b = bool(WG.search(s))
        mine += a
        wg += b
        both += a and b
        if b and not a and len(only_wg) < 8:
            only_wg.append(s[:110])
print(f"\n=== passive: mine {mine}, write-good/Vale pattern {wg}, agree {both}")
for s in only_wg:
    print("   only write-good:", s)
