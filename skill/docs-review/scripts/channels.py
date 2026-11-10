"""Source-preserving Markdown channels for cross-page and API checks."""
import re

from markdown_it import MarkdownIt


def body(text):
    if text.startswith('---\n') and (end := text.find('\n---', 4)) >= 0:
        stop = text.find('\n', end + 1)
        stop = len(text) if stop < 0 else stop
        return ''.join('\n' if c == '\n' else ' ' for c in text[:stop]) + text[stop:]
    return text


def fences(text):
    return [t for t in MarkdownIt().parse(body(text)) if t.type == 'fence']


def markup(text):
    chars = list(body(text))
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    for token in fences(text):
        for index in range(offsets[token.map[0]], offsets[token.map[1]]):
            if chars[index] != '\n':
                chars[index] = ' '
    result = ''.join(chars)
    return re.sub(r'<!--.*?-->|(`+).*?\1', lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), result, flags=re.S)


def repo_root(path):
    return next((p for p in path.resolve().parents if p.name.startswith('docs-readme-')), path.resolve().parent)
