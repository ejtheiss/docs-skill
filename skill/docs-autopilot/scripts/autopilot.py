#!/usr/bin/env python3
"""Offline decisions from recorded inputs. Models research and author; this script never does."""
from __future__ import annotations

import argparse
from contextlib import AbstractContextManager
from datetime import date
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

import yaml

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / 'config/autopilot.yaml'


def read(path):
    return json.loads(Path(path).read_text())


class WritesGuard(AbstractContextManager):
    """Offline process plus an import barrier inherited by checker subprocesses."""
    def __enter__(self):
        if 'autopilot_live_writers' in sys.modules:
            raise RuntimeError('live writers were imported before dry-run')
        self.previous = os.environ.get('DOCS_AUTOPILOT_DRY_RUN')
        os.environ['DOCS_AUTOPILOT_DRY_RUN'] = '1'
        self.connect, self.create = socket.socket.connect, socket.create_connection
        def denied(*args, **kwargs):
            raise PermissionError('network disabled in dry-run')
        socket.socket.connect = denied
        socket.create_connection = denied
        return self

    def __exit__(self, *error):
        socket.socket.connect, socket.create_connection = self.connect, self.create
        if self.previous is None:
            os.environ.pop('DOCS_AUTOPILOT_DRY_RUN', None)
        else:
            os.environ['DOCS_AUTOPILOT_DRY_RUN'] = self.previous
        if 'autopilot_live_writers' in sys.modules:
            raise RuntimeError('live writers imported during dry-run')


def admit(candidate, config):
    checks = candidate.get('checks', {})
    signal = checks.get('signal', {})
    count = len(set(signal.get('accounts', [])))
    signal_ok = count >= config['min_distinct_accounts'] and not signal.get('bespoke', False)
    locate, flight, answer = (checks.get(k, {}) for k in ('locate', 'in_flight', 'answer'))
    locate_ok = locate.get('searched') is True and locate.get('judgment') in ('not_answered', 'hard_to_find')
    flight_checked = (set(flight.get('repos', [])) == set(config['repositories']) and flight.get('notion_checked') is True
                      and all(isinstance(flight.get(k), list) for k in ('open_prs', 'recent_merged_prs', 'notion_past_harvested')))
    flight_ok = flight_checked and not any(flight.get(k) for k in ('open_prs', 'recent_merged_prs', 'notion_past_harvested'))
    complexity = answer.get('complexity')
    known = complexity in ('A1 Known', 'A2 Synthesis') and any(e.get('label') == 'VERIFIED' and e.get('claim') and e.get('source') for e in answer.get('evidence', []))
    admission = (f'Signal: {"PASS" if signal_ok else "FAIL"} ({count} distinct accounts); '
                 f'Docs: {"PASS" if locate_ok else "FAIL/UNCHECKED"} ({locate.get("judgment", "unchecked")}); '
                 f'In flight: {"PASS" if flight_ok else "FAIL/UNCHECKED"}; '
                 f'Answerable: {"PASS" if known else "FAIL/UNCLEAR"} ({complexity or "unchecked"}).')
    status = 'Discarded'
    if signal_ok and locate_ok and flight_ok:
        status = 'Admitted' if known else 'Needs Human Answer' if complexity == 'A3 Open' else 'Needs Research'
    return dict(id=candidate['id'], status=status, admission=admission, signal_count=count,
                gap='Small discoverability gap' if locate.get('judgment') == 'hard_to_find' else 'Missing documentation')


def rank(candidates, decisions, config):
    admitted = {d['id']: d for d in decisions if d['status'] == 'Admitted'}
    def order(c):
        signal = c['checks']['signal']
        weight = sum(config['topic_weights'].get(t, 1) for t in set(c.get('topics', [])))
        return (-int(signal.get('staff_conceded', False)), -c.get('operational_cost', 0),
                -admitted[c['id']]['signal_count'], c.get('cost_to_fix', 0), -weight, c['id'])
    ordered = sorted((c for c in candidates if c['id'] in admitted), key=order)
    return [dict(id=c['id'], disposition='Draft' if i < config['draft_cap'] else 'Watching' if i < config['draft_cap'] + config['watching_cap'] else 'Discarded') for i, c in enumerate(ordered)]


def carry(candidates, rows):
    merged = {c['id']: c for c in candidates}
    for row in normalize_rows(rows):
        if row['properties'].get('Stage') == 'Watching':
            if not row.get('id'):
                raise ValueError('Watching export requires a stable row id')
            candidate = row.get('candidate') or dict(id=row['id'], question=row['properties']['Task name'], checks={})
            matching = next((key for key, c in merged.items() if key == candidate['id'] or c['question'].casefold() == candidate['question'].casefold()), None)
            if matching is None:
                candidate = dict(candidate)
                candidate['checks'] = {}  # Every admission check must be refreshed this window.
                candidate['prior_row_id'] = row['id']
                merged[candidate['id']] = candidate
            else:
                merged[matching] = dict(merged[matching], prior_row_id=row['id'])
    return list(merged.values())


def normalize_rows(rows):
    if isinstance(rows, dict):
        rows = rows.get('results', [])
    result = []
    for row in rows:
        properties = row.get('properties', {k: v for k, v in row.items() if k not in ('id', 'candidate')})
        normalized = {}
        for key, value in properties.items():
            if isinstance(value, dict) and 'type' in value:
                kind = value['type']
                value = value.get(kind)
                if kind in ('rich_text', 'title'):
                    value = ''.join(t.get('plain_text', t.get('text', {}).get('content', '')) for t in value or [])
                elif kind in ('select', 'status'):
                    value = value.get('name') if value else None
            normalized[key] = value
        result.append(dict(row, properties=normalized))
    return result


def close_shipped(rows, prs, coverage):
    decisions = []
    for row in normalize_rows(rows):
        proof = next((p for p in coverage if p.get('row_id') == row['id'] and p.get('reviewed') is True and p.get('answers_question') is True), None)
        links = [p['url'] for p in prs if proof and p.get('number') in proof.get('pr_numbers', []) and p.get('merged_at') and p.get('url')]
        if links and row.get('properties', {}).get('Stage') != 'Shipped elsewhere':
            existing = row['properties']
            decisions.append(dict(id=row['id'], properties={'Stage': 'Shipped elsewhere', 'Has Draft': False,
                                  'Sources': '\n'.join(filter(None, [existing.get('Sources'), *links])),
                                  'Open Questions': '\n'.join(filter(None, [existing.get('Open Questions'), 'Covered by merged PR: ' + ', '.join(links)]))}, operation='update'))
    return decisions


def gate(draft, names, project='platform'):
    checker = HERE.parents[1] / 'docs-review/scripts/review.py'
    if not checker.is_file():
        raise ValueError('docs-review is not installed beside docs-autopilot; install both skills')
    result = subprocess.run([sys.executable, str(checker), str(draft), '--project', project, '--mode', 'draft', '--only', 'lint',
                             '--rule', 'leak-names', '--rule', 'leak-internal', '--names', str(names), '--format', 'json'], capture_output=True, text=True, timeout=120)
    if result.returncode not in (0, 1):
        raise ValueError('docs-review gate could not run; verify names file and checker installation')
    findings = json.loads(result.stdout)['findings']
    return dict(passed=not findings, violations=[dict(rule=f['rule'], line=f['line']) for f in findings])


def generalization(candidate, base, draft=''):
    material = '\n'.join([candidate['question'], candidate.get('target_path', ''),
                          candidate.get('evidence_summary', ''), *candidate.get('open_questions', []), draft])
    with tempfile.TemporaryDirectory(prefix='docs-autopilot-gate-') as directory:
        path = Path(directory) / 'candidate.md'
        path.write_text(material)
        return gate(path, base / 'customer-names.md', candidate.get('project', 'platform'))


def row(candidate, decision, stage, run_date, draft=None):
    properties = {'Task name': candidate['question'], 'Description': decision['gap'], 'Admission': decision['admission'],
                  'Stage': stage, 'Answer Complexity': candidate['checks']['answer']['complexity'], 'Run Date': run_date,
                  'Signal Count': decision['signal_count'], 'Has Draft': draft is not None and stage == 'Ready to Push', 'Review Passes': 0,
                  'Sources': '\n'.join(candidate.get('sources', [])), 'Target Path': candidate.get('target_path', ''),
                  'Open Questions': '\n'.join(candidate.get('open_questions', [])), 'Destination': 'Docs'}
    result = dict(id=candidate.get('prior_row_id', candidate['id']), operation='update' if candidate.get('prior_row_id') else 'create', properties=properties)
    if draft is not None:
        result['body'] = {'Draft': draft, 'Evidence': candidate.get('evidence_summary', '')}
    return result


def dry_run(bundle, base, out, config):
    if out.exists() and any(out.iterdir()):
        raise ValueError('output directory must be empty; existing runs are never overwritten')
    with WritesGuard():
        rows = close_shipped(bundle.get('prior_rows', []), bundle.get('merged_prs', []), bundle.get('coverage', []))
        closed = {r['id'] for r in rows}
        candidates = [c for c in carry(bundle.get('candidates', []), bundle.get('prior_rows', [])) if c.get('prior_row_id') not in closed]
        decisions = [admit(c, config) for c in candidates]
        choices = rank(candidates, decisions, config)
        lookup = {c['id']: c for c in candidates}
        by_id = {d['id']: d for d in decisions}
        failures = []
        run_date = bundle.get('run_date', date.today().isoformat())
        for decision in decisions:
            c = lookup[decision['id']]
            if c.get('prior_row_id') in closed:
                continue
            if decision['status'] == 'Needs Human Answer':
                checked = generalization(c, base)
                if checked['passed']:
                    rows.append(row(c, decision, 'Needs Human Answer', run_date))
                else:
                    failures.append(dict(id=c['id'], reason='generalization failed', violations=checked['violations']))
        for choice in choices:
            c, d = lookup[choice['id']], by_id[choice['id']]
            if c.get('prior_row_id') in closed or choice['disposition'] == 'Discarded':
                continue
            if choice['disposition'] == 'Watching':
                checked = generalization(c, base)
                if checked['passed']:
                    rows.append(row(c, d, 'Watching', run_date))
                else:
                    failures.append(dict(id=c['id'], reason='generalization failed', violations=checked['violations']))
                continue
            if not c.get('draft_file'):
                failures.append(dict(id=c['id'], reason='no model-authored draft supplied'))
                continue
            draft_path = (base / c['draft_file']).resolve()
            if not draft_path.is_relative_to(base.resolve()):
                raise ValueError('draft path must stay in fixture/input directory')
            checked = generalization(c, base, draft_path.read_text())
            if not checked['passed'] or c.get('model_generalization_passed') is not True:
                failures.append(dict(id=c['id'], reason='generalization failed', violations=checked['violations']))
                continue
            review = c.get('review', {})
            clean = (c.get('validation', {}).get('strict_failures') == 0 and review.get('strict_failures') == 0
                     and review.get('rubric_passed') is True and review.get('money_losing_mistake') is False
                     and review.get('fresh_reviewer') is True and 1 <= review.get('passes', 0) <= config['revision_limit'] + 1)
            stage = 'Ready to Push' if clean and not c.get('fixture_evidence_only') else 'Needs SME Review'
            record = row(c, d, stage, run_date, draft_path.read_text())
            record['properties']['Review Passes'] = review.get('passes', 0)
            rows.append(record)
        dm = 'nothing qualified\n' if not rows else (f'Docs autopilot: {sum(bool(r.get("body", {}).get("Draft")) for r in rows)} drafts; '
              f'{sum(r["properties"]["Stage"] == "Watching" for r in rows)} Watching; '
              f'{sum(r["properties"]["Stage"] == "Needs Human Answer" for r in rows)} need human answers; '
              f'{len(closed)} shipped elsewhere. Review in Notion.\n')
        out.mkdir(parents=True, exist_ok=True)
        (out / 'notion-rows.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        (out / 'dm.txt').write_text(dm)
        summary = dict(mode='DRY-RUN', network_writes=0, live_writers_imported=False, decisions=decisions, ranking=choices,
                       failures=failures, rows=len(rows), schema_changes_applied=False)
        (out / 'run.json').write_text(json.dumps(summary, indent=2) + '\n')
        return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--live', action='store_true', help='reserved live interface; not implemented')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('admit', 'rank', 'carry', 'close-shipped', 'dry-run'):
        p = sub.add_parser(command)
        p.add_argument('input', type=Path)
        if command == 'dry-run':
            p.add_argument('--out', type=Path, required=True)
    p = sub.add_parser('gate')
    p.add_argument('draft', type=Path)
    p.add_argument('--names', type=Path, required=True)
    p.add_argument('--project', choices=('payments', 'ledgers', 'platform', 'reference'), default='platform')
    args = parser.parse_args(argv)
    try:
        config = yaml.safe_load(args.config.read_text())
        if args.live:
            if config.get('slack_dm_recipient', 'REQUIRED-unset') == 'REQUIRED-unset' or not config.get('notion', {}).get('data_source_id'):
                raise ValueError('live requires complete configuration, including Eric Slack user id; no DM attempted')
            spec = importlib.util.spec_from_file_location('autopilot_live_writers', HERE / 'writers.py')
            writers = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(writers)
            writers.publish(live=True, config=config)
        if args.command == 'gate':
            result = gate(args.draft, args.names, args.project)
        else:
            bundle = read(args.input)
            candidates = bundle.get('candidates', [])
            decisions = [admit(c, config) for c in candidates]
            if args.command == 'admit': result = decisions
            elif args.command == 'rank': result = rank(candidates, decisions, config)
            elif args.command == 'carry': result = carry(candidates, bundle.get('prior_rows', []))
            elif args.command == 'close-shipped': result = close_shipped(bundle.get('prior_rows', []), bundle.get('merged_prs', []), bundle.get('coverage', []))
            else: result = dry_run(bundle, args.input.parent, args.out, config)
        print(json.dumps(result, indent=2))
        return 1 if args.command == 'gate' and not result['passed'] else 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
