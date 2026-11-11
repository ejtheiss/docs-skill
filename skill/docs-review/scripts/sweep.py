#!/usr/bin/env python3
"""Scaffold: rank strict findings from read-only corpus snapshots; traffic is unknown."""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import subprocess
import tempfile

from mode_support import review, snapshot, read_snapshot


def rank(findings: list[dict], top: int) -> list[dict]:
    by_rule = defaultdict(list)
    for finding in findings:
        if finding['strict']:
            by_rule[finding['rule']].append(finding)
    rows = [dict(rule=rule, severity='strict', pages=len({f['path'] for f in group}),
                 findings=len(group), traffic=None) for rule, group in by_rule.items()]
    return sorted(rows, key=lambda r: (-r['pages'], r['rule']))[:top]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repos', nargs='+', type=Path)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--ref', default='origin/v2.0')
    parser.add_argument('--top', type=int, default=10)
    args = parser.parse_args(argv)
    if args.top < 1:
        parser.error('--top must be positive')
    if bool(args.snapshot) == bool(args.repos):
        parser.error('provide --snapshot DIR (runtime) or --repos DIR... (development), not both')
    try:
        with tempfile.TemporaryDirectory(prefix='docs-sweep-') as folder:
            root = Path(folder)
            if args.snapshot:
                entries = read_snapshot(args.snapshot)
                searched = [{k: v for k, v in e.items() if k != 'filename'} for e in entries]
                for entry in entries:
                    if Path(entry['path']).suffix.lower() not in ('.md', '.mdx'):
                        continue
                    target = root / entry['repo'] / entry['path']
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(Path(entry['filename']).read_text(encoding='utf-8'), encoding='utf-8')
            else:
                searched = snapshot(args.repos, args.ref, root)
            report = review(root, mode='review')
        print('SWEEP SCAFFOLD: strict severity first, then pages affected; traffic unknown (no ranking weight).')
        print('| Rule | Severity | Pages | Findings | Traffic |')
        print('|---|---|---:|---:|---|')
        for row in rank(report['findings'], args.top):
            print(f'| {row["rule"]} | {row["severity"]} | {row["pages"]} | {row["findings"]} | unknown |')
        print('searched: ' + str(searched))
        print(report['scorecard']['policy'])
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    raise SystemExit(main())
