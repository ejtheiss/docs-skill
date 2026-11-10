#!/usr/bin/env python3
"""Offline corpus/fixture/mutation evidence; never a dependency of the shipped skill."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECTS = ('payments', 'ledgers', 'platform', 'reference')


def corpus_root():
    root = os.environ.get('DOCS_CORPUS_ROOT') or os.environ.get('DOCS_GATE_CORPUS')
    if not root:
        raise ValueError('corpus evidence is opt-in: set DOCS_CORPUS_ROOT to a materialized corpus directory')
    path = Path(root).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f'corpus directory does not exist: {path}')
    return path


def rule_config(rules):
    config = yaml.safe_load((HERE / 'rules.yaml').read_text())
    missing = set(rules) - config.keys()
    if missing:
        raise ValueError(f'unmapped rules: {sorted(missing)}')
    return {r: config[r] for r in sorted(set(rules))}


def check(paths, checker_args=(), project=None, skill=None):
    if not paths or any(not Path(path).exists() for path in paths):
        raise RuntimeError('missing checker input')
    skill = Path(skill or os.environ.get('DOCS_GATE_SKILL', ROOT / 'skill'))
    command = [sys.executable, str(skill / 'docs-review/scripts/review.py'),
               *map(str, paths), '--format', 'json']
    if project:
        command += ['--project', project]
    command += list(checker_args)
    process = subprocess.run(command, capture_output=True, text=True,
                             env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=120)
    if process.returncode not in (0, 1):
        raise RuntimeError(f'checker exit {process.returncode}: {process.stderr}')
    try:
        report = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'checker did not return JSON: {process.stderr}') from exc
    if not isinstance(report.get('findings'), list) or 'scorecard' not in report:
        raise ValueError('checker did not return a review report')
    return report


def project_of(path):
    parts = [p.lower() for p in path.parts]
    if 'reference' in parts:
        return 'reference'
    for project in PROJECTS[:-1]:
        if any(project in part for part in parts):
            return project
    raise ValueError(f'cannot infer project: {path}')


def measure(rule, files, findings):
    selected = [f for f in findings if f['rule'] == rule]
    fired = {f['path'] for f in selected}
    paths = sorted(map(str, files))
    projects = {}
    for project in PROJECTS:
        members = {str(p) for p in files if project_of(p) == project}
        pages_fired = len(members & fired)
        projects[project] = dict(pages=len(members), fired=pages_fired,
                                 findings=sum(f['path'] in members for f in selected),
                                 over_half=pages_fired > len(members) / 2)
    return dict(projects=projects,
                total=dict(pages=len(paths), fired=len(fired), findings=len(selected)),
                firing=next((p for p in paths if p in fired), None),
                non_firing=next((p for p in paths if p not in fired), None))


def mutants(source, functions):
    """One AST edit per mutant, stable traversal order and content-addressed ids."""
    tree = ast.parse(source)
    nodes = list(ast.walk(tree))
    indexes = {id(node): i for i, node in enumerate(nodes)}
    result = []
    flips = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE,
             ast.LtE: ast.Gt, ast.Gt: ast.LtE, ast.GtE: ast.Lt,
             ast.In: ast.NotIn, ast.NotIn: ast.In, ast.Is: ast.IsNot, ast.IsNot: ast.Is}

    def emit(node, replacement, operator):
        mutated = copy.deepcopy(tree)
        target = list(ast.walk(mutated))[indexes[id(node)]]
        for parent in ast.walk(mutated):
            for field, value in ast.iter_fields(parent):
                if value is target:
                    setattr(parent, field, copy.deepcopy(replacement))
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if item is target:
                            value[i] = copy.deepcopy(replacement)
        ast.fix_missing_locations(mutated)
        code = ast.unparse(mutated) + '\n'
        try:
            compile(code, '<mutant>', 'exec')
        except (SyntaxError, ValueError):
            return
        digest = hashlib.sha256(code.encode()).hexdigest()[:12]
        if any(m['id'].endswith(digest) for m in result):
            return
        result.append(dict(id=f'{operator}-L{node.lineno}-{digest}', operator=operator,
                           line=node.lineno, source=code))

    for function in (n for n in nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and n.name in functions):
        emit(function, ast.FunctionDef(name=function.name, args=copy.deepcopy(function.args),
             body=[ast.Return(value=None), *copy.deepcopy(function.body)],
             decorator_list=copy.deepcopy(function.decorator_list), returns=copy.deepcopy(function.returns),
             type_comment=function.type_comment, type_params=[]), 'early-return')
        docstring = function.body[0] if function.body and isinstance(function.body[0], ast.Expr) and isinstance(function.body[0].value, ast.Constant) and isinstance(function.body[0].value.value, str) else None
        excluded = {id(n) for n in ast.walk(docstring)} if docstring else set()
        for node in ast.walk(function):
            if id(node) in excluded:
                continue
            if isinstance(node, ast.Compare):
                for i, op in enumerate(node.ops):
                    if type(op) in flips:
                        changed = copy.deepcopy(node)
                        changed.ops[i] = flips[type(op)]()
                        emit(node, changed, 'comparison')
            if isinstance(node, ast.BoolOp):
                changed = copy.deepcopy(node)
                changed.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
                emit(node, changed, 'boolean')
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                emit(node, node.operand, 'not-remove')
            if isinstance(node, (ast.If, ast.While, ast.IfExp)):
                changed = copy.deepcopy(node)
                changed.test = ast.UnaryOp(op=ast.Not(), operand=changed.test)
                emit(node, changed, 'not-insert')
            if isinstance(node, ast.Constant):
                if isinstance(node.value, bool):
                    emit(node, ast.Constant(not node.value), 'boolean-constant')
                elif isinstance(node.value, (int, float)):
                    for delta in (-1, 1):
                        emit(node, ast.Constant(node.value + delta), 'number')
                elif isinstance(node.value, str):
                    emit(node, ast.Constant(node.value + '__mutant__'), 'string')
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                called = node.value.func
                if (isinstance(called, ast.Name) and called.id in ('add', 'emit')) or (isinstance(called, ast.Attribute) and called.attr in ('add', 'emit', 'append')):
                    emit(node, ast.Pass(), 'emit-delete')
    return result


def fixture_inventory(rule, config):
    cases = json.loads((HERE / 'fixtures' / rule / 'expectations.json').read_text())
    counts = {kind: sum(c['kind'] == kind for c in cases) for kind in ('positive', 'negative', 'boundary')}
    if not all(counts.values()):
        raise ValueError(f'{rule}: missing positive, negative or boundary fixtures')
    edges = {edge for c in cases for edge in c.get('edges', [])}
    if set(config['boundaries']) - edges:
        raise ValueError(f'{rule}: missing boundary coverage {set(config["boundaries"]) - edges}')
    return counts


def fixture_run(rule, checker_args, skill, log):
    process = subprocess.run([sys.executable, '-m', 'pytest', str(HERE / 'tests/test_fixtures.py'),
                              str(HERE / 'tests/test_contexts.py'),
                              '-q', '-p', 'no:cacheprovider'], capture_output=True, text=True,
                             env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                                  'DOCS_GATE_RULE': rule, 'DOCS_GATE_SKILL': str(skill),
                                  'DOCS_GATE_ARGS': json.dumps(checker_args)}, timeout=120)
    log.write_text(process.stdout + process.stderr)
    if process.returncode not in (0, 1):
        raise RuntimeError(f'fixture infrastructure failed: {log}')
    return process.returncode == 0


def signatures(report, rule):
    return sorted(json.dumps(f, sort_keys=True) for f in report['findings'] if f['rule'] == rule)


def corpus_modes(checker_args, requested):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--mode', choices=('review', 'draft'), default='review')
    inherited, _unknown = parser.parse_known_args(checker_args)
    return list(dict.fromkeys(requested or [inherited.mode]))


def mutation_run(rule, config, checker_args, corpus, baselines, work, jobs=4):
    targets = config.get('targets', [config])
    variants = []
    for target in targets:
        original = ROOT / 'skill' / target['source']
        for mutant in mutants(original.read_text(), target['functions']):
            mutant['file'] = target['source']
            variants.append(mutant)
    if not variants:
        raise ValueError(f'{rule}: no mutants generated; check function mapping')
    skill = work / 'skill'
    shutil.copytree(ROOT / 'skill', skill, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    if not fixture_run(rule, checker_args, skill, work / 'baseline-pytest.txt'):
        raise RuntimeError(f'{rule}: unmutated fixtures fail; see {work}')
    def exercise(mutant):
        folder = work / mutant['id']
        folder.mkdir()
        copy = folder / 'skill'
        shutil.copytree(skill, copy)
        (copy / mutant['file']).write_text(mutant['source'])
        return [fixture_run(rule, checker_args, copy, folder / f'{repeat}-pytest.txt')
                for repeat in (1, 2)]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        outcomes = list(pool.map(exercise, variants))
    sets = [[m['id'] for m, outcome in zip(variants, outcomes) if outcome[i]] for i in (0, 1)]
    if sets[0] != sets[1]:
        raise RuntimeError(f'{rule}: non-deterministic survivor sets: {sets}')
    details = []
    for mutant in variants:
        if mutant['id'] not in sets[0]:
            continue
        copy = work / mutant['id'] / 'skill'
        try:
            silence = {mode: signatures(check([corpus], [*checker_args, '--mode', mode], skill=copy), rule)
                       == signatures(baseline, rule) for mode, baseline in baselines.items()}
            silent = all(silence.values())
            error = None
        except (RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            silent, error, silence = False, str(exc), {}
        details.append(dict(id=mutant['id'], corpus_silent=silent, by_mode=silence, error=error,
                            source=mutant['file'], line=mutant['line'], operator=mutant['operator']))
    return dict(generated=len(variants), killed=len(variants) - len(details),
                kill_rate=(len(variants) - len(details)) / len(variants),
                survivors=details, repeat_survivors=sets)


def render(rule, measurements, counts, mutation):
    rows = [f'## {rule}', '']
    for mode, measurement in measurements.items():
        rows += [f'### {mode}', '', '| Project | Pages fired / pages | Findings | Gate 1 |',
                 '|---|---:|---:|---|']
        for project, data in measurement['projects'].items():
            rows.append(f'| {project} | {data["fired"]} / {data["pages"]} | {data["findings"]} | ' +
                        ('REJECT/DEMOTE (>50%)' if data['over_half'] else 'within base-rate limit') + ' |')
        total = measurement['total']
        rows += [f'| total | {total["fired"]} / {total["pages"]} | {total["findings"]} | — |', '',
                 f'Firing witness: `{measurement["firing"] or "none (inactive or corpus-silent)"}`',
                 f'Non-firing witness: `{measurement["non_firing"] or "none"}`', '']
    rows += [
             f'Fixtures: {counts["positive"]} positive, {counts["negative"]} negative, {counts["boundary"]} boundary; real-checker pytest passed.',
             f'Mutation: {mutation["killed"]}/{mutation["generated"]} killed = {mutation["kill_rate"]:.3f}; bar ≥0.950: ' + ('PASS' if mutation['kill_rate'] >= .95 else 'FAIL'),
             'Two bytecode-disabled runs: identical survivor sets.', '', 'Survivors:']
    rows += [f'- `{m["id"]}`: corpus-silent **{m["corpus_silent"]}** ({m["by_mode"]})' + (f'; error: {m["error"]}' if m['error'] else '') for m in mutation['survivors']] or ['- None.']
    rows += ['', 'Gate 5 (independent oracle): NOT ESTABLISHED by this harness.',
             'Gate 6 (blind adjudication): NOT ESTABLISHED by this harness. No admission claim.', '']
    return '\n'.join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rule', action='append', required=True)
    parser.add_argument('--checker-arg', action='append', default=[], help='one checker token per occurrence; use --checker-arg=--flag')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--corpus-mode', action='append', choices=('review', 'draft'))
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    config = rule_config(args.rule)
    try:
        corpus = corpus_root()
    except ValueError as exc:
        parser.error(str(exc))
    files = sorted(corpus.rglob('*.md'))
    if not files:
        parser.error(f'no corpus markdown: {corpus}')
    if any(token.split('=')[0] in ('--rule', '--format', '--strict-only', '--list-rules') for token in args.checker_arg):
        parser.error('checker arguments must not filter findings or replace JSON output')
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    baselines = {mode: check([corpus], [*args.checker_arg, '--mode', mode])
                 for mode in corpus_modes(args.checker_arg, args.corpus_mode)}
    baseline = next(iter(baselines.values()))
    if 'openapi-field-exists' in config and any(
            'openapi-field-exists not run: no spec snapshot' in b['scorecard'].get('notes', [])
            for b in baselines.values()):
        parser.error('OpenAPI evidence requires --checker-arg=--spec --checker-arg=PATH or DOCS_REVIEW_SPEC')
    if any(b['scorecard']['pages'] != len(files) for b in baselines.values()):
        raise ValueError('checker and harness disagree on corpus page count')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='run-', dir=args.out.parent))
    rows = ['# Admission-gate evidence', '', f'Corpus: `{corpus}`; {baseline["scorecard"]["policy"]}.',
            f'Checker arguments: `{json.dumps(args.checker_arg)}`.',
            'Mutations include neighboring decisions within mapped functions; all fixture findings are asserted.', '']
    results = {}
    for rule, entry in config.items():
        rule_work = work / rule
        rule_work.mkdir()
        counts = fixture_inventory(rule, entry)
        measured = {mode: measure(rule, files, b['findings']) for mode, b in baselines.items()}
        mutation = mutation_run(rule, entry, args.checker_arg, corpus, baselines, rule_work, args.jobs)
        results[rule] = dict(measurements=measured, fixtures=counts, mutation=mutation)
        rows.append(render(rule, measured, counts, mutation))
    manifest = corpus / 'MANIFEST.txt'
    if manifest.exists():
        rows += ['## Corpus manifest', '', '```text', manifest.read_text().strip(), '```']
    args.out.write_text('\n'.join(rows) + '\n')
    args.out.with_suffix('.json').write_text(json.dumps(results, indent=2) + '\n')
    print(args.out.read_text())
    print(f'Mutation fixture logs: {work}')
    return int(any(v['mutation']['kill_rate'] < .95 or
                   any(p['over_half'] for m in v['measurements'].values() for p in m['projects'].values()) or
                   not any(m['firing'] for m in v['measurements'].values()) or
                   not any(m['non_firing'] for m in v['measurements'].values())
                   for v in results.values()))


if __name__ == '__main__':
    sys.exit(main())
