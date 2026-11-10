"""Attach original witnesses and the explicitly requested hosted-block no-fire witness."""
import json
from pathlib import Path
import sys

import gate


def supplement(path):
    root = gate.corpus_root()
    original = json.loads((gate.HERE / 'evidence/phase-c.json').read_text())['supplementary']['undefined_block_witnesses']
    witnesses = []
    for finding in original:
        parts = Path(finding['path']).parts
        start = next(i for i, part in enumerate(parts) if part.startswith('docs-readme-'))
        witnesses.append(dict(path=Path(*parts[start:]).as_posix(), component=finding['evidence']))
    no_fire = next(w['path'] for w in witnesses if w['component'] == 'EarlyAccess')
    results = json.loads(path.with_suffix('.json').read_text())
    for mode in ('review', 'draft'):
        report = gate.check([root / no_fire], ['--mode', mode, '--rule', 'reuse-undefined-block'])
        assert not report['findings'], report
        results['reuse-undefined-block']['measurements'][mode]['non_firing'] = str(root / no_fire)
    results['original_page_paths'] = witnesses
    results['hosted_block_confirmation'] = 'Eric supplied the 2026-11-10 browser DOM and .md export observation; not independently repeated in this run.'
    path.with_suffix('.json').write_text(json.dumps(results, indent=2) + '\n')
    text = path.read_text()
    text = text.replace(str(root / 'docs-readme-ledgers/custom_pages/support.md'), str(root / no_fire))
    text += '\n## Original nine page paths\n\n' + '\n'.join(f'- `{w["path"]}`: {w["component"]}' for w in witnesses)
    text += '\n\nHosted-block confirmation: ' + results['hosted_block_confirmation'] + '\n'
    path.write_text(text)
    print(text)


if __name__ == '__main__':
    supplement(Path(sys.argv[1]))
