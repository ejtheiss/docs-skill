#!/usr/bin/env python3
"""Validate and append one reviewer-judgment label, not a checker finding."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys

RUBRIC_IDS = frozenset({
    'guarantee-scoped-to-evidence', 'step-actor-marked', 'ledger-entries-balance',
    'psp-byob-scoped', 'no-invented-fields', 'webhook-per-async-transition',
    'idempotency-where-retry-moves-money', 'money-losing-mistake',
})
FIELDS = frozenset({'case_hash', 'page_hash', 'rubric_id', 'decision', 'rationale',
                    'reviewer', 'timestamp', 'policy_id'})


def validate_label(label: object) -> dict:
    if not isinstance(label, dict) or set(label) != FIELDS:
        raise ValueError('label must be an object with exactly: ' + ', '.join(sorted(FIELDS)))
    if any(not isinstance(value, str) or not value.strip() for value in label.values()):
        raise ValueError('all label values must be nonempty strings')
    for field, size in (('case_hash', 64), ('page_hash', 64), ('policy_id', 12)):
        if not re.fullmatch(rf'[0-9a-f]{{{size}}}', label[field]):
            raise ValueError(f'{field} must contain {size} lowercase hexadecimal characters')
    if label['rubric_id'] not in RUBRIC_IDS:
        raise ValueError('unknown reviewer-judgment rubric_id')
    if label['decision'] not in ('accept', 'reject'):
        raise ValueError('decision must be accept or reject')
    try:
        timestamp = datetime.fromisoformat(label['timestamp'].removesuffix('Z') + ('+00:00' if label['timestamp'].endswith('Z') else ''))
    except ValueError as exc:
        raise ValueError('timestamp must be an ISO 8601 datetime with a timezone') from exc
    if timestamp.tzinfo is None:
        raise ValueError('timestamp must include a timezone')
    return label


def append_label(path: Path, label: object) -> None:
    validated = validate_label(label)
    if path.exists() and path.stat().st_size:
        with path.open('rb') as stream:
            stream.seek(-1, 2)
            if stream.read(1) != b'\n':
                raise ValueError('existing JSONL log does not end with a newline')
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(validated, ensure_ascii=False, sort_keys=True) + '\n')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label', help='JSON label file, or - for standard input')
    parser.add_argument('--out', required=True, type=Path, help='JSONL append destination')
    args = parser.parse_args(argv)
    try:
        if args.label == '-':
            label = json.load(sys.stdin)
        else:
            label = json.loads(Path(args.label).read_text(encoding='utf-8'))
        append_label(args.out, label)
    except (OSError, ValueError) as exc:
        print(f'label rejected: {exc}', file=sys.stderr)
        return 2
    print(f'Appended reviewer judgment: {label["rubric_id"]} {label["decision"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
