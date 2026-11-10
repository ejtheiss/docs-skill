#!/usr/bin/env python3
"""Differential test: the linter's stdlib parser vs markdown-it-py (CommonMark reference).

Run with the venv python (needs markdown-it-py). Audit scaffolding, not shipped: it exists to prove
the hand-rolled parser sees the same fences, headings and list nesting as a real CommonMark parser.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "/home/ubuntu/docs-style/skill/docs-review/scripts")
sys.path.insert(0, "/home/ubuntu/docs-style/skill/docs-lint/scripts")
import lint as sc  # noqa: E402
from markdown_it import MarkdownIt  # noqa: E402

MD = MarkdownIt("commonmark").enable("table")
CORPUS = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/style-corpus")


def oracle(text: str, body_start: int) -> dict:
    """Fences, headings and max list depth per CommonMark, in absolute page line numbers."""
    tokens = MD.parse(text)
    fences: list[tuple[int, str]] = []
    headings: list[tuple[int, int]] = []
    depth = 0
    max_depth = 0
    for t in tokens:
        if t.type == "fence" and t.map:
            fences.append((t.map[0] + body_start, (t.info or "").strip()))
        elif t.type == "heading_open" and t.map:
            headings.append((t.map[0] + body_start, int(t.tag[1])))
        elif t.type in ("bullet_list_open", "ordered_list_open"):
            depth += 1
            max_depth = max(max_depth, depth)
        elif t.type in ("bullet_list_close", "ordered_list_close"):
            depth -= 1
    return {"fences": fences, "headings": headings, "list_depth": max_depth}


def mine(page: sc.Page) -> dict:
    headings = [
        (lineno, len(m.group(1)))
        for lineno, line in page.prose_lines
        if (m := sc.HEADING_RE.match(line))
    ]
    indents: list[int] = []
    max_depth = 0
    in_html = False
    for _, line in page.prose_lines:
        if sc.HTML_BLOCK_OPEN_RE.match(line):
            in_html = True
        elif sc.HTML_BLOCK_CLOSE_RE.match(line):
            in_html = False
        m = sc.LIST_ITEM_RE.match(line)
        if not m:
            if not line.strip():
                indents = []
            continue
        if in_html:
            continue
        indent = len(m.group(1).replace("\t", "    "))
        while indents and indent < indents[-1]:
            indents.pop()
        if not indents or indent > indents[-1]:
            indents.append(indent)
        max_depth = max(max_depth, len(indents))
    return {"fences": page.fences, "headings": headings, "list_depth": max_depth}


def main() -> int:
    files = sorted(CORPUS.rglob("*.md"))
    disagree: Counter[str] = Counter()
    samples: dict[str, list[str]] = {}

    def note(kind: str, detail: str) -> None:
        disagree[kind] += 1
        samples.setdefault(kind, []).append(detail)

    for path in files:
        page = sc.parse_page(path)
        text = "\n".join(page.lines)
        ref = oracle(text, page.body_start)
        got = mine(page)

        if [f[0] for f in ref["fences"]] != [f[0] for f in got["fences"]]:
            note("fence-lines", f"{path.name}: ref {[f[0] for f in ref['fences']][:6]} got {[f[0] for f in got['fences']][:6]}")
        elif [f[1] for f in ref["fences"]] != [f[1] for f in got["fences"]]:
            note("fence-info", f"{path.name}: ref {[f[1] for f in ref['fences']][:4]} got {[f[1] for f in got['fences']][:4]}")
        if ref["headings"] != got["headings"]:
            only_ref = [h for h in ref["headings"] if h not in got["headings"]]
            only_got = [h for h in got["headings"] if h not in ref["headings"]]
            note("headings", f"{path.name}: only-ref {only_ref[:4]} only-mine {only_got[:4]}")
        if ref["list_depth"] != got["list_depth"]:
            note("list-depth", f"{path.name}: ref {ref['list_depth']} mine {got['list_depth']}")

    print(f"{len(files)} pages compared against markdown-it-py")
    if not disagree:
        print("no disagreements")
        return 0
    for kind, n in disagree.most_common():
        print(f"\n{kind}: {n}")
        for detail in samples[kind][:10]:
            print("   ", detail)
    return 1


if __name__ == "__main__":
    sys.exit(main())
