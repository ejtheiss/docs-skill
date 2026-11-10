"""Review scope derived from the working file and an optional Git base."""
from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
import subprocess


def add_arguments(parser) -> None:
    parser.add_argument('--mode', choices=('review', 'draft'), default='review')
    parser.add_argument('--base', help='Git ref used to identify new files and touched lines')
    parser.add_argument('--names', type=Path, help='per-run customer names, one per line; # comments')
    parser.add_argument('--spec', type=Path, help='OpenAPI JSON snapshot (otherwise DOCS_REVIEW_SPEC; optional)')


@dataclass
class Context:
    mode: str = 'review'
    new: bool = False
    touched: set[int] = field(default_factory=set)

    def includes(self, allowed: tuple[str, ...], line: int, end: int | None = None) -> bool:
        active = {'always', self.mode}
        if self.new:
            active.add('new')
        if self.touched.intersection(range(line, (end or line) + 1)):
            active.add('touched')
        return bool(active.intersection(allowed))


def file_context(path: Path, mode: str, base: str | None) -> Context:
    context = Context(mode=mode, new=mode == 'draft')
    if not base:
        return context
    def git(*args):
        return subprocess.run(['git', '-C', str(path.resolve().parent), *args],
                              capture_output=True, text=True)
    root = git('rev-parse', '--show-toplevel')
    revision = git('rev-parse', '--verify', '--end-of-options', base + '^{commit}')
    if root.returncode or revision.returncode:
        raise ValueError(f'cannot resolve --base {base!r} for {path}')
    relative = path.resolve().relative_to(Path(root.stdout.strip())).as_posix()
    old = git('show', f'{revision.stdout.strip()}:{relative}')
    if old.returncode:
        context.new = True
        return context
    current = path.read_text(encoding='utf-8', errors='replace')
    for tag, _a, _b, start, end in SequenceMatcher(
            None, old.stdout.splitlines(), current.splitlines(), autojunk=False).get_opcodes():
        if tag in ('insert', 'replace'):
            context.touched.update(range(start + 1, end + 1))
    return context
