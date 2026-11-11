"""Read-only Git snapshots and the shared reviewer subprocess for authoring modes."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

import yaml

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / 'config'
PROJECTS = yaml.safe_load((CONFIG / 'policy.yaml').read_text())['projects']


def default_repos() -> list[Path]:
    return [Path(name) for name in sorted({p['repo'].split('/')[0] for p in PROJECTS.values()})]


def read_snapshot(root: Path) -> list[dict]:
    root = root.resolve()
    try:
        manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'cannot read snapshot manifest.json: {exc}') from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get('entries'), list):
        raise ValueError('snapshot manifest must be an object with an entries array')
    entries, seen = [], set()
    known = {p.name for p in default_repos()}
    for item in manifest['entries']:
        if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k] for k in ('repo', 'path', 'sha', 'url')):
            raise ValueError('snapshot entry requires string repo, path, sha and url')
        relative = Path(item['path'])
        if item['repo'] not in known or relative.is_absolute() or '..' in relative.parts or '\\' in item['path']:
            raise ValueError('snapshot entry must use a known repo and a safe repository-relative path')
        if relative.suffix.lower() not in ('.md', '.mdx') and item['path'] != 'reference/modern-treasury-api.json':
            raise ValueError('snapshot entries must be Markdown pages or the OpenAPI spec')
        if item['sha'] != 'live' and not re.fullmatch(r'(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})', item['sha']):
            raise ValueError('snapshot sha must be a Git SHA or "live"')
        if not re.match(r'https://[^/\s]+/', item['url']):
            raise ValueError('snapshot url must be an absolute https source URL')
        key = (item['repo'], relative.as_posix())
        if key in seen:
            raise ValueError('duplicate snapshot repo/path entry')
        seen.add(key)
        filename = (root / item['repo'] / relative).resolve()
        if not filename.is_relative_to(root) or not filename.is_file():
            raise ValueError(f'snapshot file missing or outside snapshot: {item["repo"]}/{item["path"]}')
        entries.append(dict(item, path=relative.as_posix(), filename=str(filename)))
    return sorted(entries, key=lambda e: (e['repo'], e['path']))


def snapshot_source(root: Path, repo: str, path: str) -> tuple[str, dict]:
    entry = next((e for e in read_snapshot(root) if e['repo'] == repo and e['path'] == path), None)
    if entry is None:
        raise ValueError(f'target not listed in snapshot manifest: {repo}/{path}')
    return Path(entry['filename']).read_text(encoding='utf-8'), {k: v for k, v in entry.items() if k != 'filename'}


def git(repo: Path, *args: str, allowed=(0,)) -> str:
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=30)
    if result.returncode not in allowed:
        raise ValueError(f'{repo}: git {args[0]} failed: {result.stderr.strip()}')
    return result.stdout


def revision(repo: Path, ref: str) -> str:
    return git(repo, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}').strip()


def source(repo: Path, sha: str, path: str) -> str:
    relative = Path(path)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('target path must be repository-relative without ..')
    return git(repo, 'show', f'{sha}:{relative.as_posix()}')


def review(path: Path, project: str | None = None, mode: str = 'draft') -> dict:
    command = [sys.executable, str(HERE / 'review.py'), str(path), '--mode', mode, '--format', 'json']
    if project:
        command += ['--project', project]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode not in (0, 1):
        raise ValueError(f'review failed: {result.stderr.strip()}')
    return json.loads(result.stdout)


def snapshot(repos: list[Path], ref: str, root: Path) -> list[dict]:
    searched = []
    for repo in repos:
        sha = revision(repo, ref)
        searched.append(dict(repo=str(repo), ref=ref, sha=sha))
        for path in git(repo, 'ls-tree', '-r', '--name-only', sha).splitlines():
            if Path(path).suffix.lower() not in ('.md', '.mdx'):
                continue
            content = source(repo, sha, path)
            target = root / repo.name / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
    return searched
