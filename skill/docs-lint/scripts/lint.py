#!/usr/bin/env python3
"""docs-lint: what one page can be judged on by itself.

Checks a ReadMe markdown page (or a whole tree) against the Modern Treasury documentation style
guide: base rules apply everywhere, overlay rules depend on which project the page belongs to. This
is the file-local tier — frontmatter, headings, fences, JSON syntax, links, terminology, voice — so
it needs nothing but the file, which is why it can run on a page that does not exist yet. Continuity
and coverage are `docs-content`, reuse is `docs-maintain`, and anything that has to be true of the
API is `docs-test`.

    pip install markdown-it-py PyYAML
    python3 lint.py path/to/page.md
    python3 lint.py docs/ --project payments
    python3 lint.py docs/ --strict-only        # only rules we never bend
    python3 lint.py docs/ --format json

Exit status is 1 when any strict rule fails, 2 on a usage error, so this can gate a review.

No rule's severity, threshold, scope, word list or message text appears in this file. They are read
through `policy.py` from `config/rules.yaml` beside this checker, `config/language.yaml` it includes,
and `docs-review/config/policy.yaml` under both; every report names the resulting policy id. What is
in this file is how a rule decides — the channel it reads, the pattern it looks for, and the fix it
suggests, which is a transformation of the page's own text rather than authored prose.

Parsing is delegated to markdown-it-py so that fences, headings, lists and inline code are resolved
by a CommonMark implementation rather than by line-level regexes; rules only ever see the channel
they are about.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

SHARED = Path(__file__).resolve().parents[2] / "docs-review" / "scripts"
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

try:
    import yaml
    from markdown_it import MarkdownIt
except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
    sys.exit(f"missing dependency: {exc.name}. Run: pip install markdown-it-py PyYAML")

import policy as policy_module  # noqa: E402
from findings import (  # noqa: E402
    EVIDENCE_LIMIT,
    Finding,
    clip_evidence,
    collect_files,
    detect_project as _detect_project,
    input_error as _input_error,
    policy_stamp,
    render_finding,
    render_text,
    report_order,
    rule_counts,
    scorecard as _scorecard,
)

# --------------------------------------------------------------------------------------------------
# Policy. Nothing below is a decision: every value, severity, scope and threshold is read from
# `config/rules.yaml` and `config/language.yaml` beside this checker, merged over
# `docs-review/config/policy.yaml`. Changing the guide changes a verdict without changing this file,
# and a table that drifts away from the guide cannot hide in Python.
# --------------------------------------------------------------------------------------------------

# The rule ids this subskill knows how to decide. This *is* code, not policy: it is the checker's
# capability, and it is declared so a rule deleted from the policy file is a loud refusal rather than
# a severity read from nothing.
EMITS = frozenset({
    "acronym-undefined", "body-h1", "callout-emoji", "contractions", "currency-mixed",
    "fence-language", "fence-language-unknown", "fence-untagged", "filler", "filler-please",
    "frontmatter-excerpt", "frontmatter-title", "heading-formatting", "heading-repeats-title",
    "heading-skip", "image-alt", "json-parse", "link-absolute-internal", "link-anchor-empty",
    "link-anchor-vague", "link-bare-url", "list-depth", "mt-shorthand", "no-ordered-lists",
    "object-capitalization", "object-shorthand", "passive-voice", "reference-no-shell",
    "sentence-length", "url-query-separator",
})

try:
    POLICY = policy_module.load("docs-lint")
    POLICY.require(EMITS)
except policy_module.PolicyError as exc:  # pragma: no cover - exercised through the CLI
    sys.exit(f"policy error: {exc}")

ARTIFACT = POLICY.path

# Rule id -> (strict, provenance). Strict rules never bend; flexible ones are reviewer judgment.
# Reported severity is what a run prints; the guide may grade a rule harder than the checker reports
# it, which is recorded on the row and printed by `--list-rules`.
RULES: dict[str, tuple[bool, str]] = {
    rule_id: (POLICY.rules[rule_id].strict, POLICY.rules[rule_id].provenance)
    for rule_id in sorted(EMITS)
}
# Rules that only apply to some projects: rule id -> projects it applies to.
OVERLAY_RULES = {rule_id: POLICY.rules[rule_id].scope for rule_id in sorted(EMITS)
                 if "all" not in POLICY.rules[rule_id].scope}

PROJECTS = POLICY.projects()
# docs.moderntreasury.com path prefix that means "this page's own repo".
PROJECT_URL_PREFIX = POLICY.mapping("project_url_prefixes")

OBJECTS = POLICY.words("object_names")
SHORTHAND = POLICY.words("object_shorthand")
MT_SHORTHAND = POLICY.mapping("mt_shorthand")

# ReadMe renders a blockquote as a callout when its first paragraph starts with an emoji, and maps a
# fixed set of emoji to themes (rdmd @readme/markdown, components/Callout: themes map). These are the
# emoji Modern Treasury sanctions; any other ReadMe-recognised callout emoji is a finding.
SANCTIONED_CALLOUTS = POLICY.words("callout_emoji")

# Filler: word -> the replacement to suggest, or None when the fix is to delete it. A word whose
# exception pattern is set is only filler outside that pattern (`just` is filler as a minimiser, not in `just as`, `just like`, `just in time`).
FILLER_WORDS = POLICY.mapping("filler_words")
FILLER_EXCEPTIONS = {word: re.compile(pattern, re.IGNORECASE)
                     for word in FILLER_WORDS
                     if (pattern := POLICY.exception("filler_words", word))}
PLEASE_WORDS = POLICY.words("filler_please")
PLEASE_EXCEPTIONS = {word: re.compile(pattern, re.IGNORECASE)
                     for word in PLEASE_WORDS
                     if (pattern := POLICY.exception("filler_please", word))}

VAGUE_ANCHORS = POLICY.words("vague_anchors")

STANDARD_FENCE_LANGS = set(POLICY.words("fence_languages"))
FENCE_LANG_FIXES = POLICY.mapping("fence_language_fixes")
# Acronym -> pattern matching its expansion. A regex rather than initials matching: several of these
# are not initialisms of their expansion (FX, IAT, KYC/KYB), so deriving the expansion from the
# letters reported "Foreign Exchange (FX)" as undefined.
ACRONYM_EXPANSIONS = POLICY.mapping("acronym_expansions")

MAX_SENTENCE_WORDS = POLICY.threshold("sentence-length")
MAX_LIST_DEPTH = POLICY.threshold("list-depth")


def says(rule_id: str, key: str = "", **fields: object) -> str:
    """What a finding for `rule_id` says, from the policy.

    Message text is authored prose about the reader's page, so it belongs beside the rule rather than
    inline here. What stays in this file is the `fix`: a fix is not prose but a transformation of the
    page's own text - `re.sub` over a heading, a slice of the object name - and a template language
    that could express those would be a worse programming language than this one.
    """
    return POLICY.rules[rule_id].says(key, **fields)

# --------------------------------------------------------------------------------------------------
# Patterns. These only ever run on a resolved channel (prose text, a fence info string, an href),
# never on raw markdown lines.
# --------------------------------------------------------------------------------------------------

BARE_URL_RE = re.compile(r"(?<![\w@])https?://[^\s)>\]\"'`]+")

# JSON examples. The docs write bodies four ways a strict parser rejects and a reader does not: a
# `//` or `/* */` annotation, a trailing comma, a `<placeholder>` or `{{handlebar}}` in a value
# position, and an elision (`...` on its own line, or `{ ... }` standing in for a nested object).
# Each is normalised away before parsing, so what remains unparseable is a genuine syntax error.
JSON_FENCE_LANGS = set(POLICY.words("json_fence_languages"))
JSON_DATA_FLAG_RE = re.compile(r"(?:--data(?:-raw|-binary)?|-d)\s*'")
JSON_COMMENT_RE = re.compile(r'"(?:[^"\\\n]|\\.)*"|//[^\n]*|/\*.*?\*/', re.S)
JSON_PLACEHOLDER_RE = re.compile(r"(?<=:\s)(<[^>\n]{1,80}>|\{\{[^}\n]{1,80}\}\})")
JSON_ELISION_RE = re.compile(r"^\s*(?:\.\.\.|\u2026)\s*,?\s*$", re.M)
JSON_INLINE_ELISION_RE = re.compile(
    r"\{\s*(?:\.\.\.|\u2026|<[^>\n]{1,80}>)\s*\}|\[\s*(?:\.\.\.|\u2026)\s*\]"
)
JSON_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
JSON_NAME_LIST_RE = re.compile(r'(\s*"[^"]+"\s*,?)+')
# A fence tagged `json` whose body is a command or an HTTP request line is a mislabelled fence, which
# `fence-language` already covers; parsing it as JSON would report a second, misleading finding.
NOT_JSON_BODY_RE = re.compile(
    r"^\s*(?:" + "|".join(re.escape(p) for p in POLICY.words("non_json_fence_prefixes")) + r")\b"
)
# `&` opening a query string. `?` anywhere earlier means the query string is well formed.
URL_QUERY_SEPARATOR_RE = re.compile(r"https?://[^\s'\"`)]*?/api/[^\s'\"`?)]*&[^\s'\"`)]*")

# Vale Google.Passive / write-good: a be-verb followed by a past participle. The irregular list is
# write-good's (lib/passive/lexicon.js), which Vale's Google.Passive rule also uses.
IRREGULAR_PARTICIPLES = POLICY.words("irregular_participles")
# A prefixed participle ("pre-filled", "auto-ledgered", "re-issued") is one participle. A hyphenated
# form whose first element is a noun ("user-defined", "bank-issued") is a compound adjective instead,
# which is why only the prefixes are allowed here.
PARTICIPLE = (r"(?:(?:(?:pre|re|auto|co|de|mis|non|over|under|un)-)?\w+ed"
              f"|{'|'.join(IRREGULAR_PARTICIPLES)})")

# `'s` is a contracted `is` only after these words; anywhere else it is a possessive.
CONTRACTED_S_HOSTS = "|".join(POLICY.words("contracted_s_hosts"))

# Words that stand between the auxiliary and the participle. Any -ly adverb, plus the closed class of
# non-ly ones the corpus uses: negation, aspect, focus, and a coordination of two adverbs
# ("automatically or manually reconciled").
INTERVENING = r"(?:\w+ly|" + "|".join(POLICY.words("intervening_adverbs")) + r")"

# A be-verb, negated or contracted, then up to two intervening words, then a past participle. `'ve`
# and `'ll` are excluded because they are have and will, which take an active perfect or future
# ("you've entered", "you'll set").
BE_PASSIVE_RE = re.compile(
    r"(?:\b(?:am|are|were|being|is|been|was|be)(?:n['\u2019]t)?\b"
    rf"|\b(?:{CONTRACTED_S_HOSTS})['\u2019]s\b|(?<=\w)['\u2019](?:re|m)\b)"
    rf"(?:\s+{INTERVENING}\b){{0,2}}\s+{PARTICIPLE}\b",
    re.IGNORECASE,
)

# The get-passive, which Vale's Google.Passive misses: "funds get returned", "revenue gets recognized".
GET_PASSIVE_RE = re.compile(rf"\bget(?:s|ting)?\b(?:\s+{INTERVENING}\b){{0,2}}\s+{PARTICIPLE}\b",
                            re.IGNORECASE)

# An -ed word after a copula that is an adjective rather than a participle, so the clause is not
# passive. There is no way to tell by word shape, so the list is explicit.
ADJECTIVAL_RE = re.compile(
    r"\b(?:am|are|were|being|is|been|was|be)\s+(?:not\s+)?"
    r"(?:interested|related|unverified|unchecked)\b",
    re.IGNORECASE,
)

# The actor a passive sentence names. This rule asks a writer to name one, so a sentence that already
# does satisfies it and reporting it is a false positive — 5 of the 120 findings in the adjudicated
# sample were exactly that. Only a `by`-phrase counts: it is the agent marker English passives have,
# and it is decidable without a parse, which a file-local checker cannot afford to load.
AGENT_BY_RE = re.compile(
    r"\bby\s+(?P<determiner>(?:(?:the|a|an|its|their|our|your|his|her|any|another|each|every|this"
    r"|these|those|all|both|either|some|no)\s+)+)?"
    r"(?P<phrase>[`\"\w][\w'\u2019.\-]*(?:\s+[\w'\u2019.\-]+){0,2})",
    re.IGNORECASE,
)
# Characters between the end of the participle and the `by`. An agent phrase follows its participle
# closely ("is settled by the bank"); a `by` further off belongs to another clause ("is settled the same
# business day, by which time the report exists"), so the window is what separates the two senses.
AGENT_WINDOW = 48
# `by` phrases that are not actors by shape rather than by vocabulary: a number is a quantity or a
# deadline ("by 5pm"), and an identifier is a field name ("sorted by `created_at`", "grouped by
# ledger.id") — neither is someone doing something.
NON_AGENT_SHAPE_RE = re.compile(r"(?:[`\"].*|\d[\w:.,%$]*|\w*_\w*|[a-z]+\.[a-z_.]+)$", re.IGNORECASE)
# A bare gerund after `by` is the means, not the actor: "created by calling the endpoint". With a
# determiner in front it is a modifier of the actor instead — "denied by the receiving party" — which is
# the distinction that keeps this from suppressing half the corpus, and it needs no parse to see.
GERUND_RE = re.compile(r"\w+ing$", re.IGNORECASE)

# Get-idioms with no actor, which is what this rule asks the writer to name.
GET_IDIOM_RE = re.compile(
    r"\bget(?:s|ting)?\s+(?:"
    + "|".join(re.escape(idiom).replace(r"\ ", r"\s+").replace(" ", r"\s+")
                for idiom in POLICY.words("get_idioms"))
    + r")\b",
    re.IGNORECASE,
)
# `by` heads that are not actors by vocabulary: a means ("paid by check"), a deadline ("by the end of
# the day"), a manner ("by default"), or a relative pronoun opening another clause ("by which time").
NON_AGENT_HEADS = frozenset(word.lower() for word in POLICY.words("non_agent_by"))

# Contractions. Suffix forms are unambiguous once an all-caps host is excluded, since those are code
# operators ("conditions are AND'd together"), not contractions. `'s` is only a contraction after the
# hosts above, so possessives ("the Ledger Account's balance") are never flagged.
CONTRACTION_SUFFIX_RE = re.compile(r"\b\w*[a-z]\w*(?:'|\u2019)(?:t|re|ll|ve|d|m)\b")
CONTRACTION_S_RE = re.compile(rf"\b({CONTRACTED_S_HOSTS})(?:'|\u2019)s\b", re.IGNORECASE)

# Sentence splitting: a terminator followed by whitespace and an opening character, unless the
# terminator belongs to a known abbreviation, an initial, or a hand-typed list number.
# A decimal needs no guard: `3.14` has no whitespace after the point, so it is never a boundary.
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])[\"')\]]?\s+(?=[\"'(\[`A-Z0-9])")
ABBREVIATIONS = frozenset(POLICY.words("abbreviations"))
# Alt text stand-in for an image marked decorative, which WAI exempts from needing alt text.
DECORATIVE = "\u0000decorative"
ENUMERATOR_TAIL_RE = re.compile(r"^\d{1,3}\.$")
INITIAL_TAIL_RE = re.compile(r"(?:^|\s)[A-Z]\.$")

CURRENCY_CODES = tuple(POLICY.words("currency_codes"))
DOLLAR_AMOUNT_RE = re.compile(r"\$\s?\d[\d,.]*")
ISO_AMOUNT_RE = re.compile(r"\b\d[\d,.]*\s?(" + "|".join(CURRENCY_CODES) + r")\b")

# A blockquote becomes a ReadMe callout when its first paragraph starts with an emoji followed by
# whitespace or end of paragraph (rdmd @readme/markdown, processor/transform/callouts.ts:
# `^(${emoji_regex().source}|\u26A0)(\s+|$)`). These are the emoji rdmd maps to a callout theme
# (components/Callout, `themes`); the generic emoji ranges below cover any other emoji rdmd accepts
# and are pinned against the emoji-regex package rdmd itself uses by tests/differential/.
README_CALLOUT_EMOJI = tuple(POLICY.words("readme_callout_emoji"))
# Longest first, so ⚠️ matches before ⚠.
CALLOUT_EMOJI_BY_LENGTH = sorted(README_CALLOUT_EMOJI, key=len, reverse=True)
# Emoji code points, generated from Unicode emoji-data.txt by dev/experiments/gen_emoji_ranges.py,
# the same property data the emoji-regex package rdmd uses is generated from. Emoji_Presentation
# characters are emoji on their own; the Emoji-but-not-Emoji_Presentation characters are emoji
# only when U+FE0F follows them (UTS #51, ED-9/ED-10).
# Generated from Unicode emoji-data.txt (2025-07-25, 17:54:31 GMT).
EMOJI_PRESENTATION_RANGES = POLICY.table("emoji_presentation")

# Generated from Unicode emoji-data.txt (2025-07-25, 17:54:31 GMT).
EMOJI_TEXT_RANGES = POLICY.table("emoji_text")

REGIONAL_INDICATORS = POLICY.table("regional_indicators")[0]
SKIN_TONES = POLICY.table("skin_tones")[0]
TAG_CHARACTERS = POLICY.table("tag_characters")[0]
KEYCAP_BASES = frozenset(POLICY.words("keycap_bases"))
VARIATION_SELECTOR = "\uFE0F"
KEYCAP = "\u20E3"
ZWJ = "\u200D"


def _stands_alone(text: str, length: int) -> bool:
    """True when `text[:length]` is followed by whitespace or ends the text, as rdmd requires."""
    return len(text) == length or text[length].isspace()


def _in_ranges(char: str, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(low <= ord(char) <= high for low, high in ranges)


def _emoji_element(text: str) -> int:
    """Length of one emoji at the start of `text`, without ZWJ continuation; 0 if there is none.

    UTS #51 emoji_core_sequence: a flag pair, a keycap sequence, or an emoji base with its optional
    presentation selector, skin tone modifier or subdivision tag characters.
    """
    if not text:
        return 0
    if _in_ranges(text[0], (REGIONAL_INDICATORS,)):
        return 2 if len(text) > 1 and _in_ranges(text[1], (REGIONAL_INDICATORS,)) else 0
    presentation = _in_ranges(text[0], EMOJI_PRESENTATION_RANGES)
    if not presentation and not _in_ranges(text[0], EMOJI_TEXT_RANGES):
        return 0
    # A skin tone modifier makes its base an emoji on its own (UTS #51 emoji_modifier_sequence).
    if len(text) > 1 and _in_ranges(text[1], (SKIN_TONES,)):
        return 2
    end = 1
    if text.startswith(VARIATION_SELECTOR, end):
        end += 1
    elif not presentation:
        return 0  # a text-presentation character is an emoji only with U+FE0F after it
    if text[0] in KEYCAP_BASES:
        return end + 1 if text.startswith(KEYCAP, end) else 0
    if end < len(text) and _in_ranges(text[end], (SKIN_TONES,)):
        end += 1
    while end < len(text) and _in_ranges(text[end], (TAG_CHARACTERS,)):
        end += 1
    return end


def _emoji_run(text: str) -> int:
    """Length of the emoji starting `text`, following ZWJ into a joined sequence; 0 if none."""
    end = _emoji_element(text)
    if not end:
        return 0
    while text.startswith(ZWJ, end):
        joined = _emoji_element(text[end + 1:])
        if not joined:
            break
        end += 1 + joined
    return end


def starts_with_emoji(text: str) -> str:
    """Return the leading emoji of `text` (with modifiers), or "" when it does not start with one.

    Matches rdmd's callout test: the emoji must be followed by whitespace or end the paragraph.
    """
    text = text.lstrip()
    if not text:
        return ""
    known = next((e for e in CALLOUT_EMOJI_BY_LENGTH
                  if text.startswith(e) and _stands_alone(text, len(e))), "")
    if known:
        return known
    end = _emoji_run(text)
    return text[:end] if end and _stands_alone(text, end) else ""


# --------------------------------------------------------------------------------------------------
# Page model
# --------------------------------------------------------------------------------------------------


@dataclass
class Block:
    """A run of prose with its resolved text: no code, no image alt, no markdown syntax."""

    line: int
    kind: str  # paragraph | heading
    text: str
    line_of_offset: list[tuple[int, int]] = field(default_factory=list)
    link_spans: list[tuple[int, int]] = field(default_factory=list)  # anchor text, not prose to scan

    def line_at(self, offset: int) -> int:
        line = self.line
        for start, lineno in self.line_of_offset:
            if start <= offset:
                line = lineno
            else:
                break
        return line


@dataclass
class Page:
    path: Path
    project: str
    frontmatter: dict
    title: str
    blocks: list[Block] = field(default_factory=list)
    headings: list[tuple[int, int, str]] = field(default_factory=list)
    fences: list[tuple[int, str]] = field(default_factory=list)
    code: list[tuple[int, str, str]] = field(default_factory=list)  # line, info, content
    links: list[tuple[int, str, str]] = field(default_factory=list)
    images: list[tuple[int, str, str]] = field(default_factory=list)
    callouts: list[tuple[int, str]] = field(default_factory=list)
    list_items: list[tuple[int, int, bool]] = field(default_factory=list)  # line, depth, ordered


class HtmlChannels(HTMLParser):
    """Pulls links and images out of raw HTML blocks, which markdown-it passes through verbatim."""

    def __init__(self, base_line: int) -> None:
        super().__init__(convert_charrefs=True)
        self.base_line = base_line
        self.links: list[tuple[int, str, str]] = []
        self.images: list[tuple[int, str, str]] = []
        self._open_link: tuple[int, str] | None = None
        self._link_text: list[str] = []

    def _line(self) -> int:
        return self.base_line + self.getpos()[0] - 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {k.lower(): (v or "") for k, v in attrs}
        if tag == "img":
            alt = values.get("alt", "")
            if values.get("aria-hidden") == "true" or values.get("role") == "presentation":
                alt = alt or DECORATIVE
            self.images.append((self._line(), alt, values.get("src", "")))
        elif tag == "a":
            self._open_link = (self._line(), values.get("href", ""))
            self._link_text = []

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if self._open_link:
            self._link_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._open_link:
            line, href = self._open_link
            self.links.append((line, "".join(self._link_text).strip(), href))
            self._open_link = None


def detect_project(path: Path, override: str | None) -> str | None:
    """Which project's overlay rules a page is judged under, from the projects the policy knows."""
    return _detect_project(path, override, PROJECTS)


def _yaml_mapping(raw: str) -> dict:
    """Parse `raw` as a YAML mapping; malformed or non-mapping frontmatter reads as empty."""
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def split_frontmatter(text: str) -> tuple[dict, int, str]:
    """Return (frontmatter, 1-based line number of the first body line, body text)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, 1, text
    end = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() in ("---", "...")), 0)
    if not end:
        return {}, 1, text
    return _yaml_mapping("\n".join(lines[1:end])), end + 2, "\n".join(lines[end + 1:])


def _inline_channels(page: Page, token, base_line: int, kind: str) -> None:
    """Walk an inline token, collecting prose text plus links, images and offset->line mapping."""
    text_parts: list[str] = []
    offsets: list[tuple[int, int]] = []
    link_spans: list[tuple[int, int]] = []
    line = base_line
    length = 0
    link_stack: list[tuple[int, str, int, list[str]]] = []

    def emit(chunk: str, anchor: str | None = None) -> None:
        """Add `chunk` to the prose text; add `anchor` (default: `chunk`) to any open anchor text."""
        nonlocal length
        text_parts.append(chunk)
        length += len(chunk)
        for entry in link_stack:
            entry[3].append(chunk if anchor is None else anchor)

    for child in token.children or []:
        if child.type == "text":
            emit(child.content)
        elif child.type == "code_inline":
            # Inline code is not prose, but `code` is a legitimate link anchor.
            emit(" ", anchor=child.content)
        elif child.type in ("softbreak", "hardbreak"):
            emit(" ")
            line += 1
            offsets.append((length, line))
        elif child.type == "image":
            alt = "".join(c.content for c in (child.children or []) if c.type == "text")
            page.images.append((line, alt, child.attrGet("src") or ""))
        elif child.type == "link_open":
            link_stack.append((line, child.attrGet("href") or "", length, []))
        elif child.type == "link_close" and link_stack:
            link_line, href, start, anchor_parts = link_stack.pop()
            page.links.append((link_line, "".join(anchor_parts).strip(), href))
            link_spans.append((start, length))
        elif child.type == "html_inline":
            _feed_html(page, child.content, line)

    text = "".join(text_parts)
    if text.strip():
        page.blocks.append(Block(line=base_line, kind=kind, text=text, line_of_offset=offsets,
                                 link_spans=link_spans))


def _feed_html(page: Page, html: str, line: int) -> None:
    """Collect the links and images inside a raw HTML run, which markdown-it passes through."""
    parser = HtmlChannels(line)
    parser.feed(html)
    page.links.extend(parser.links)
    page.images.extend(parser.images)


def _record_callout(page: Page, blocks_before: int) -> None:
    """A blockquote whose first paragraph opens with an emoji renders as a ReadMe callout."""
    if len(page.blocks) <= blocks_before:
        return
    block = page.blocks[-1]
    if emoji := starts_with_emoji(block.text):
        page.callouts.append((block.line, emoji))


def _walk_tokens(page: Page, tokens: list, body_start: int) -> None:
    """Fill the page's channels from markdown-it's token stream.

    List depth, blockquote depth and the open heading level only exist while walking, which is why
    the rules never see them: they see `page.list_items`, `page.headings` and `page.callouts`.
    """
    depth = 0
    ordered_stack: list[bool] = []
    heading_line = heading_level = 0
    pending_callout = False  # set on blockquote_open, so it also means "inside a blockquote"

    for token in tokens:
        line = body_start + (token.map[0] if token.map else 0)
        if token.type == "fence":
            page.fences.append((line, (token.info or "").strip()))
            page.code.append((line, (token.info or "").strip(), token.content or ""))
        elif token.type == "heading_open":
            heading_line, heading_level = line, int(token.tag[1])
        elif token.type in ("bullet_list_open", "ordered_list_open"):
            depth += 1
            ordered_stack.append(token.type == "ordered_list_open")
        elif token.type in ("bullet_list_close", "ordered_list_close"):
            depth -= 1
            ordered_stack.pop()
        elif token.type == "list_item_open":
            page.list_items.append((line, depth, ordered_stack[-1]))
        elif token.type == "blockquote_open":
            pending_callout = True
        elif token.type == "html_block":
            _feed_html(page, token.content, line)
        elif token.type == "inline":
            before = len(page.blocks)
            _inline_channels(page, token, line, "heading" if heading_level else "paragraph")
            if heading_level:
                page.headings.append((heading_line, heading_level, token.content.strip()))
                heading_level = 0
            elif pending_callout:
                pending_callout = False
                _record_callout(page, before)


def parse_page(path: Path, project_override: str | None = None) -> Page:
    raw = path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
    frontmatter, body_start, body = split_frontmatter(raw)
    page = Page(
        path=path,
        project=detect_project(path, project_override) or "platform",
        frontmatter=frontmatter,
        title=str(frontmatter.get("title") or "").strip(),
    )
    _walk_tokens(page, MarkdownIt("commonmark").enable("table").parse(body), body_start)
    return page


# --------------------------------------------------------------------------------------------------
# Sentences
# --------------------------------------------------------------------------------------------------


def split_sentences(text: str) -> list[tuple[int, str]]:
    """Split prose into (character offset, sentence) pairs. Abbreviations do not end a sentence."""
    out: list[tuple[int, str]] = []
    start = 0
    for match in SENTENCE_BOUNDARY_RE.finditer(text):
        head = text[start:match.start()]
        tail = head.rstrip("\"')]")
        last = tail.rsplit(" ", 1)[-1].lstrip("([\"'“‘").rstrip(".!?").lower() if tail else ""
        if last in ABBREVIATIONS or ENUMERATOR_TAIL_RE.match(tail) or INITIAL_TAIL_RE.search(tail):
            continue
        if head.strip():
            out.append((start, head.strip()))
        start = match.end()
    if text[start:].strip():
        out.append((start, text[start:].strip()))
    return out


def heading_text(page: Page) -> list[tuple[int, str]]:
    """(line, text) for every heading. Terminology rules read this too; readability rules do not,
    because a heading is a fragment and sentence length, passive voice and filler misfire on one."""
    return [(block.line, block.text.strip()) for block in page.blocks
            if block.kind == "heading" and block.text.strip()]


def sentences(page: Page) -> list[tuple[int, str]]:
    """(line, sentence) for every prose sentence outside headings."""
    out: list[tuple[int, str]] = []
    for block in page.blocks:
        if block.kind == "heading":
            continue
        for offset, sentence in split_sentences(block.text):
            if len(sentence.split()) > 2:
                out.append((block.line_at(offset), sentence))
    return out


# --------------------------------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------------------------------


def applies(rule: str, project: str) -> bool:
    return project in OVERLAY_RULES[rule] if rule in OVERLAY_RULES else True


# add(line, rule, message, evidence="", fix="", span=None) -- records a finding, or drops it when the
# rule does not apply to this page's project. `span` is the (start, end) offsets of the offending
# words inside `evidence`, which the report underlines. Rule functions never touch `findings`.
Add = Callable[..., None]


def check(page: Page) -> list[Finding]:
    findings: list[Finding] = []
    rel = str(page.path)

    def add(line: int, rule: str, message: str, evidence: str = "", fix: str = "",
            span: tuple[int, int] | None = None) -> None:
        if not applies(rule, page.project):
            return
        text, col, end_col = clip_evidence(evidence, span)
        # Severity is per page, not per rule: a rule may carry an override for this page's project
        # ("where an overlay contradicts base style, the overlay wins for that project"). With no
        # override - the state of every shipped rule - this is exactly `RULES[rule][0]`.
        strict = POLICY.rules[rule].strict_for(page.project)
        findings.append(Finding(rel, line, rule, strict, message, text, fix, col, end_col))

    prose = sentences(page)
    check_frontmatter(page, add)
    check_headings(page, add)
    for lineno, text in heading_text(page):
        check_terminology(add, lineno, text)
    check_fences(page, add)
    check_json(page, add)
    check_urls(page, add)
    check_lists(page, add)
    check_links(page, add)
    check_images(page, add)
    check_bare_urls(page, add)
    check_callouts(page, add)
    for lineno, sentence in prose:
        check_sentence(add, lineno, sentence)
    check_currency(page, add)
    check_acronyms(prose, add)
    return findings


def check_frontmatter(page: Page, add: Add) -> None:
    if not page.title:
        add(1, "frontmatter-title", says("frontmatter-title"))
    # D7 inverts this rule: Modern Treasury does not use excerpts, so a page carrying one has a field to
    # delete, and a page without one is correct. The finding is the removal, not the absence.
    if excerpt := str(page.frontmatter.get("excerpt") or "").strip():
        add(1, "frontmatter-excerpt", says("frontmatter-excerpt"), excerpt)


def check_headings(page: Page, add: Add) -> None:
    """ReadMe renders the frontmatter title as the page h1, so body headings start at h2 and the
    title counts as the level above them (markdownlint MD025 + MD001 with front_matter_title)."""
    previous = 1
    for lineno, level, text in page.headings:
        if level == 1:
            add(lineno, "body-h1", says("body-h1"),
                text, fix=f"## {text}")
        if level > previous + 1:
            add(lineno, "heading-skip", says("heading-skip", previous=previous, level=level), text)
        previous = level
        markup = re.search(r"(\*\*|__|<u>)", text)
        if markup or re.fullmatch(r"_[^_]+_", text.strip()):
            add(lineno, "heading-formatting", says("heading-formatting"), text,
                fix=re.sub(r"(\*\*|__|</?u>)", "", text),
                span=markup.span() if markup else None)
        if page.title and text.strip().lower() == page.title.strip().lower():
            add(lineno, "heading-repeats-title", says("heading-repeats-title"), text)


def check_fences(page: Page, add: Add) -> None:
    for lineno, info in page.fences:
        lang = info.split()[0].lower() if info else ""
        if not lang:
            add(lineno, "fence-untagged", says("fence-untagged"))
            continue
        if lang in FENCE_LANG_FIXES:
            target = FENCE_LANG_FIXES[lang]
            add(lineno, "fence-language", says("fence-language", lang=lang, target=target), info, fix=f"```{target}")
        elif lang not in STANDARD_FENCE_LANGS:
            add(lineno, "fence-language-unknown", says("fence-language-unknown", lang=lang), info)
        if FENCE_LANG_FIXES.get(lang, lang) == "shell":
            add(lineno, "reference-no-shell",
                says("reference-no-shell"), info)


def json_balanced_object(text: str, start: int) -> str | None:
    """The object beginning at the first `{` at or after `start`, counting braces outside strings."""
    open_at = text.find("{", start)
    if open_at < 0:
        return None
    depth, in_string, escaped = 0, False, False
    for index in range(open_at, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[open_at : index + 1]
    return None


def json_bodies(page: Page) -> list[tuple[int, str]]:
    """(line, source) for every JSON body a reader could copy: json fences and curl request bodies."""
    out = []
    for line, info, content in page.code:
        lang = info.split()[0].lower() if info else ""
        if lang in JSON_FENCE_LANGS:
            if content.strip() and not NOT_JSON_BODY_RE.match(content):
                out.append((line, content))
        elif "curl" in content and (flag := JSON_DATA_FLAG_RE.search(content)):
            if body := json_balanced_object(content, flag.end()):
                out.append((line, body))
    return out


def json_strip_comments(source: str) -> str:
    """Comments removed, leaving string literals alone: `"http://x"` is a URL, not an annotation."""
    return JSON_COMMENT_RE.sub(
        lambda match: match.group(0) if match.group(0).startswith('"') else "", source
    )


def json_normalized(source: str) -> str:
    """The body with the four documented conventions removed, so only real syntax errors survive."""
    text = json_strip_comments(source)
    text = JSON_PLACEHOLDER_RE.sub('"placeholder"', text)
    text = JSON_INLINE_ELISION_RE.sub('"elided"', text)
    text = JSON_ELISION_RE.sub("", text)
    return JSON_TRAILING_COMMA_RE.sub(r"\1", text)


def json_accepted_shape(text: str) -> bool:
    """Shapes that are not one object but are still readable: a field list, a property excerpt, or
    two alternative bodies shown one after the other."""
    stripped = text.strip()
    inner = stripped[1:-1] if stripped.startswith("{") and stripped.endswith("}") else ""
    if inner and ":" not in inner and JSON_NAME_LIST_RE.fullmatch(inner):
        return True
    if not stripped.startswith(("{", "[")):
        try:
            json.loads("{" + stripped.rstrip(",") + "}")
            return True
        except ValueError:
            return False
    decoder, index, values = json.JSONDecoder(), 0, 0
    while index < len(stripped):
        try:
            _, index = decoder.raw_decode(stripped, index)
        except ValueError:
            return False
        values += 1
        while index < len(stripped) and stripped[index] in " \t\r\n,":
            index += 1
    return values > 1


def check_json(page: Page, add: Add) -> None:
    for line, source in json_bodies(page):
        try:
            json.loads(source)
            continue
        except ValueError:
            pass
        text = json_normalized(source)
        try:
            json.loads(text)
            continue
        except ValueError as error:
            message = getattr(error, "msg", str(error))
            offending = int(getattr(error, "lineno", 1) or 1)
        if json_accepted_shape(text):
            continue
        lines = source.splitlines()
        evidence = lines[offending - 1].strip() if 0 < offending <= len(lines) else ""
        add(line + offending, "json-parse",
            says("json-parse", reason=message.lower()), evidence)


def check_urls(page: Page, add: Add) -> None:
    for line, _info, content in page.code:
        for offset, text in enumerate(content.splitlines()):
            for match in URL_QUERY_SEPARATOR_RE.finditer(text):
                url = match.group(0)
                if "?" in url[: url.index("&")]:
                    continue
                add(line + offset + 1, "url-query-separator",
                    says("url-query-separator"), url,
                    fix=url.replace("&", "?", 1))


def check_lists(page: Page, add: Add) -> None:
    for lineno, depth, ordered in page.list_items:
        if depth > MAX_LIST_DEPTH:
            add(lineno, "list-depth", says("list-depth", depth=depth, limit=MAX_LIST_DEPTH))
        if ordered:
            add(lineno, "no-ordered-lists",
                says("no-ordered-lists"))


def check_links(page: Page, add: Add) -> None:
    for lineno, text, href in page.links:
        check_anchor_text(add, lineno, text, href)
        if "docs.moderntreasury.com" not in href:
            continue
        if PROJECT_URL_PREFIX[page.project] in href:
            add(lineno, "link-absolute-internal",
                says("link-absolute-internal"), href)


def check_anchor_text(add: Add, lineno: int, text: str, href: str) -> None:
    if not text or not href:
        add(lineno, "link-anchor-empty", says("link-anchor-empty"), text or href)
    elif text.lower().strip(".:") in VAGUE_ANCHORS:
        add(lineno, "link-anchor-vague", says("link-anchor-vague", "vague", text=text), text)
    elif BARE_URL_RE.fullmatch(text):
        add(lineno, "link-anchor-vague", says("link-anchor-vague", "url"), text)


def check_images(page: Page, add: Add) -> None:
    for lineno, alt, src in page.images:
        if alt != DECORATIVE and not alt.strip():
            add(lineno, "image-alt", says("image-alt"), src)


def check_bare_urls(page: Page, add: Add) -> None:
    for block in page.blocks:
        for match in BARE_URL_RE.finditer(block.text):
            # A URL used as a link's anchor text is a link, not a bare URL (markdownlint MD034).
            if any(start <= match.start() < end for start, end in block.link_spans):
                continue
            add(block.line_at(match.start()), "link-bare-url", says("link-bare-url"), match.group(0))


# What each sanctioned emoji is *for*. The policy decides which emoji are sanctioned; this only
# carries the phrasing for the ones it knows, so a newly sanctioned emoji is listed without a role
# rather than described wrongly.
CALLOUT_ROLES = POLICY.mapping("callout_roles")


def sanctioned_callouts() -> str:
    """`\N{BLUE BOOK} for information, \N{CONSTRUCTION SIGN} for limitations or ...`: what to use instead."""
    listed = [f"{e} {CALLOUT_ROLES[e]}" if e in CALLOUT_ROLES else e
              for e in sorted(SANCTIONED_CALLOUTS, key=lambda e: list(CALLOUT_ROLES).index(e)
                              if e in CALLOUT_ROLES else len(CALLOUT_ROLES))]
    return " or ".join([", ".join(listed[:-1]), listed[-1]] if len(listed) > 1 else listed)


def check_callouts(page: Page, add: Add) -> None:
    sanctioned = [s.rstrip("\uFE0F") for s in SANCTIONED_CALLOUTS]
    for lineno, emoji in page.callouts:
        if emoji.rstrip("\uFE0F") in sanctioned:
            continue
        add(lineno, "callout-emoji", says("callout-emoji", emoji=emoji, sanctioned=sanctioned_callouts()), emoji)


def check_sentence(add: Add, lineno: int, sentence: str) -> None:
    check_terminology(add, lineno, sentence)
    check_filler(add, lineno, sentence)
    check_readability(add, lineno, sentence)


def check_terminology(add: Add, lineno: int, text: str) -> None:
    """Object and company naming, which holds in headings as much as in prose."""
    check_shorthand(add, lineno, text)
    check_object_capitalization(add, lineno, text)


def check_shorthand(add: Add, lineno: int, sentence: str) -> None:
    for short, full in MT_SHORTHAND.items():
        if match := re.search(rf"\b{re.escape(short)}\b", sentence):
            add(lineno, "mt-shorthand", says("mt-shorthand", full=full, short=short), sentence,
                fix=re.sub(rf"\b{re.escape(short)}\b", full, sentence), span=match.span())
    for short in SHORTHAND:
        if match := re.search(rf"\b{short}s?\b", sentence):
            add(lineno, "object-shorthand", says("object-shorthand", short=short),
                sentence, span=match.span())


def check_object_capitalization(add: Add, lineno: int, sentence: str) -> None:
    """Object names are capitalized; the first miscased mention of each object is enough."""
    for obj in OBJECTS:
        for match in re.finditer(rf"\b{re.escape(obj)}s?\b", sentence, re.IGNORECASE):
            found = match.group(0)
            if found.rstrip("s") == obj:
                continue
            add(lineno, "object-capitalization", says("object-capitalization", found=found, obj=obj), sentence,
                fix=obj + found[len(obj):], span=match.span())
            break


def check_filler(add: Add, lineno: int, sentence: str) -> None:
    """A filler word, unless its policy exception describes the use in this sentence."""
    for word, replacement in FILLER_WORDS.items():
        match = re.search(rf"\b{re.escape(word)}\b", sentence, re.IGNORECASE)
        if not match or _exempt(FILLER_EXCEPTIONS, word, sentence):
            continue
        add(lineno, "filler", says("filler", word=word), sentence,
            fix=f"replace with '{replacement}'" if replacement else "delete the word",
            span=match.span())
    for word in PLEASE_WORDS:
        match = re.search(rf"\b{re.escape(word)}\b", sentence, re.IGNORECASE)
        if not match or _exempt(PLEASE_EXCEPTIONS, word, sentence):
            continue
        add(lineno, "filler-please",
            says("filler-please", word=word), sentence,
            span=match.span())


def _exempt(exceptions: dict[str, re.Pattern], word: str, sentence: str) -> bool:
    pattern = exceptions.get(word)
    return bool(pattern and pattern.search(sentence))


def agent_span(sentence: str, passive: tuple[int, int] | None) -> tuple[int, int] | None:
    """Span of the `by`-phrase naming the actor of the passive at `passive`, or None if none does.

    A named actor is the thing the rule asks for, so it is the checker's own exemption rather than an
    editorial one: "the transfer is initiated by the bank" needs no rewrite. Agreement with spaCy's
    `agent` dependency over the corpus is measured in `dev/audit_methods/passive_agent_differential.py`;
    the disagreements it prints are the argument for the window and the two exclusion lists.
    """
    if passive is None:
        return None
    for match in AGENT_BY_RE.finditer(sentence, passive[1]):
        if match.start() - passive[1] > AGENT_WINDOW:
            return None
        words = [word.strip("`\"'.,;:()").lower() for word in match.group("phrase").split()]
        if NON_AGENT_SHAPE_RE.match(words[0]):
            continue
        if not match.group("determiner") and GERUND_RE.match(words[0]):
            continue
        if any(word in NON_AGENT_HEADS for word in words):
            continue
        return match.span()
    return None


def passive_span(sentence: str, agents: bool = True) -> tuple[int, int] | None:
    """Span of the first passive construction in `sentence` that does not name its actor, or None.

    `agents=False` answers the narrower question - is there a passive construction at all - which is
    what the differential against the parser compares, and what the corpus base rate was measured on.
    """
    for pattern in (BE_PASSIVE_RE, GET_PASSIVE_RE):
        for match in pattern.finditer(sentence):
            if pattern is BE_PASSIVE_RE and ADJECTIVAL_RE.match(sentence, match.start()):
                continue
            if pattern is GET_PASSIVE_RE and GET_IDIOM_RE.match(sentence, match.start()):
                continue
            if agents and agent_span(sentence, match.span()):
                continue
            return match.span()
    return None


def check_readability(add: Add, lineno: int, sentence: str) -> None:
    words = len(sentence.split())
    if words > MAX_SENTENCE_WORDS:
        add(lineno, "sentence-length", says("sentence-length", words=words), sentence)
    if passive := passive_span(sentence):
        add(lineno, "passive-voice", says("passive-voice"),
            sentence, span=passive)
    contraction = CONTRACTION_SUFFIX_RE.search(sentence) or CONTRACTION_S_RE.search(sentence)
    if contraction:
        add(lineno, "contractions", says("contractions"), sentence,
            span=contraction.span())


def first_amount(page: Page, pattern: re.Pattern) -> tuple[int, str] | None:
    for block in page.blocks:
        if match := pattern.search(block.text):
            return block.line_at(match.start()), match.group(0)
    return None


def check_currency(page: Page, add: Add) -> None:
    dollar = first_amount(page, DOLLAR_AMOUNT_RE)
    iso = first_amount(page, ISO_AMOUNT_RE)
    if not dollar or not iso:
        return
    add(max(dollar[0], iso[0]), "currency-mixed",
        says("currency-mixed"),
        f"{dollar[1]} (line {dollar[0]}) and {iso[1]} (line {iso[0]})")


def check_acronyms(prose: list[tuple[int, str]], add: Add) -> None:
    """An acronym must be expanded in the first sentence that uses it, not later on the page."""
    for acronym, expansion in ACRONYM_EXPANSIONS.items():
        pattern = re.compile(rf"\b{acronym}\b")
        first = next(((line, s) for line, s in prose if pattern.search(s)), None)
        if first is None or re.search(expansion, first[1], re.IGNORECASE):
            continue
        match = pattern.search(first[1])
        add(first[0], "acronym-undefined", says("acronym-undefined", acronym=acronym), first[1],
            span=match.span() if match else None)


# --------------------------------------------------------------------------------------------------
# Command line. Findings, the scorecard and the rendering are shared with every other subskill
# (`docs-review/scripts/findings.py`), so a review reads as one log however it was invoked.
# --------------------------------------------------------------------------------------------------


def scorecard(findings: list[Finding], pages: int) -> dict:
    return _scorecard(findings, pages)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path, help="markdown files or directories")
    ap.add_argument("--project", choices=PROJECTS, help="override project detection")
    ap.add_argument("--strict-only", action="store_true", help="hide flexible notes")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--rule", action="append",
                    help="only report these rule ids (the scorecard then covers the filtered set)")
    ap.add_argument("--list-rules", action="store_true", help="print every rule with its provenance")
    return ap


def print_rules() -> None:
    """Every rule, how loudly it reports, and where that came from.

    A rule the guide grades harder than the checker reports is annotated: the two severities are
    different questions (what a reviewer should apply against what a run may claim), and a rule whose
    precision is not yet measured reports below its guide grade until it is.
    """
    print(policy_stamp())
    for rule, (strict, provenance) in sorted(RULES.items()):
        guide = POLICY.rules[rule].guide_severity
        reported = "strict" if strict else "flexible"
        note = f"[guide: {guide}] " if guide != reported else ""
        print(f"{'STRICT' if strict else 'flex  '} {rule:<26} {note}{provenance}")


def input_error(files: list[Path], project: str | None) -> str:
    """The reason these files cannot be checked, or "" when they can."""
    return _input_error(files, project, PROJECTS)


def run(files: list[Path], project: str | None, rules: list[str] | None) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        findings.extend(check(parse_page(path, project)))
    if not rules:
        return findings
    wanted = set(rules)
    return [x for x in findings if x.rule in wanted]


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)

    if args.list_rules:
        print_rules()
        return 0

    if not args.paths:
        ap.error("give at least one markdown file or directory")

    unknown = sorted(r for r in (args.rule or []) if r not in RULES)
    if unknown:
        print(f"unknown rule id(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    files = collect_files(args.paths)
    if error := input_error(files, args.project):
        print(error, file=sys.stderr)
        return 2

    findings = report_order(run(files, args.project, args.rule))
    card = scorecard(findings, len(files))
    if args.format == "json":
        print(json.dumps({"scorecard": card, "findings": [vars(x) for x in findings]}, indent=2))
    else:
        print(render_text(findings, card, show_flexible=not args.strict_only))
    return 1 if card["strict_failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
