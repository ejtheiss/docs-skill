"""Measurement only: raw adjacent single-backtick spans, not a shipped rule."""
import re

from markdown_it import MarkdownIt


def scan(text):
    lines = text.splitlines(keepends=True)
    if text.startswith('---\n'):
        for index in range(1, len(lines)):
            if lines[index].strip() == '---':
                lines[:index + 1] = ['\n' for _ in lines[:index + 1]]
                break
    parsed = ''.join(lines)
    for token in MarkdownIt().parse(parsed):
        if token.type == 'fence':
            lines[token.map[0]:token.map[1]] = ['\n' for _ in lines[token.map[0]:token.map[1]]]
    text = ''.join(lines)
    text = re.sub(r'<!--.*?-->', lambda m: '\n' * m[0].count('\n'), text, flags=re.S)
    result = []
    for match in re.finditer(r'(?<!`)`([^`\n]+)`([ \t\r\n]*)`([^`\n]+)`(?!`)', text):
        if not re.search(r'\n\s*\n', match[2]):
            result.append(dict(line=text.count('\n', 0, match.start()) + 1, evidence=match[0]))
    return result


def measure(path):
    return [dict(path=str(path), rule='code-span-adjacent', **finding) for finding in scan(path.read_text())]
