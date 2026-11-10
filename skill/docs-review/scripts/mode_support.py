"""Read-only Git snapshots and the shared reviewer subprocess for authoring modes."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import yaml

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / 'config'
PROJECTS = yaml.safe_load((CONFIG / 'policy.yaml').read_text())['projects']


def default_repos() -> list[Path]:
    return [Path.home() / 'work' / name for name in sorted({p['repo'].split('/')[0] for p in PROJECTS.values()})]


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
