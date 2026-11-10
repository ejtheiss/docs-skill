#!/usr/bin/env python3
"""Find quoted evidence in snapshots or Git refs; relevance is reviewer judgment."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen

import yaml

from mode_support import CONFIG, PROJECTS, default_repos, git, revision, source, read_snapshot

SETTINGS = yaml.safe_load((CONFIG / 'locate.yaml').read_text())
NOTICE = 'reviewer judgment: the model judges whether a quote actually answers the question; the script only locates evidence.'


def normalized(text: str) -> str:
    return re.sub(r'[-_]+', ' ', text.lower()).replace('’', "'")


def terms(question: str) -> list[list[str]]:
    groups = []
    folded = normalized(question)
    for key, aliases in SETTINGS['synonyms'].items():
        values = list(dict.fromkeys([key, *aliases]))
        if any(re.search(r'(?<!\w)' + re.escape(normalized(v)) + r'(?!\w)', folded) for v in values):
            groups.append(values)
    pattern = r'`([^`]+)`|"([^"]+)"|(?<!\w)\x27([^\x27]+)\x27(?!\w)|\b[\w]+(?:[-\x27][\w]+)*\b'
    for match in re.finditer(pattern, question.replace('’', "'")):
        phrase = next((g for g in match.groups() if g is not None), match.group()).lower()
        phrase = re.sub(r"'s$", '', phrase)
        if phrase in SETTINGS['stopwords'] or len(phrase) < 2:
            continue
        if any(normalized(phrase) in {normalized(v) for v in group} or
               any(normalized(phrase) in normalized(v).split() for v in group) for group in groups):
            continue
        groups.append([phrase])
    return sorted(groups, key=lambda g: g[0])


def matched(text: str, groups: list[list[str]]) -> list[str]:
    folded = normalized(text)
    return [g[0] for g in groups if any(re.search(r'(?<!\w)' + re.escape(normalized(v)) + r'(?!\w)', folded) for v in g)]


def headings(lines: list[str]) -> list[str]:
    result, heading, fence = [], '(body)', ''
    for line in lines:
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            if not fence:
                fence = marker[1][0]
            elif marker[1][0] == fence:
                fence = ''
        if not fence and (found := re.match(r'^#{1,6}\s+(.+?)\s*#*$', line)):
            heading = found[1]
        result.append(heading)
    return result


def public_url(repo: Path, path: str, text: str) -> str:
    project = 'reference' if path.startswith('reference/') else next(
        (name for name, row in PROJECTS.items() if row['repo'].split('/')[0] == repo.name), 'platform')
    frontmatter = {}
    if text.startswith('---\n'):
        try:
            frontmatter = yaml.safe_load(text.split('---', 2)[1]) or {}
        except yaml.YAMLError:
            pass
    stem = Path(path).stem
    if stem.lower() == 'index':
        stem = Path(path).parent.name
    slug = frontmatter.get('slug') if isinstance(frontmatter, dict) else None
    slug = slug or re.sub(r'[^a-z0-9_-]+', '-', stem.lower()).strip('-')
    section = 'reference' if project == 'reference' else 'docs'
    return 'https://docs.moderntreasury.com' + PROJECTS[project]['url_prefix'] + section + '/' + quote(str(slug), safe='-_')


def candidates(repos: list[Path], ref: str, groups: list[list[str]], top: int) -> tuple[list[dict], list[dict]]:
    found, searched = [], []
    aliases = sorted({v for group in groups for v in group})
    # Normalized phrase variants must also be discoverable by fixed-string Git grep.
    aliases = sorted(set(aliases) | {normalized(v) for v in aliases})
    for repo in repos:
        try:
            sha = revision(repo, ref)
            record = dict(repo=str(repo), ref=ref, sha=sha)
            searched.append(record)
            if not aliases:
                continue
            flags = [flag for value in aliases for flag in ('-e', value)]
            output = git(repo, 'grep', '-n', '--null', '-i', '-F', *flags, sha, '--', '*.md', '*.mdx', allowed=(0, 1))
            hits = {}
            for path_ref, line, _text in re.findall(r'([^\0]+)\0(\d+)\0([^\n]*)\n?', output):
                hits.setdefault(path_ref.removeprefix(sha + ':'), set()).add(int(line))
            for path, numbers in sorted(hits.items()):
                text = source(repo, sha, path)
                lines = text.splitlines()
                titles = headings(lines)
                spans = set()
                for number in sorted(numbers):
                    start = max(0, number - 3)
                    end = min(len(lines), start + SETTINGS['passage_lines'])
                    if (start, end) in spans:
                        continue
                    spans.add((start, end))
                    passage = '\n'.join(lines[start:end])
                    matches = matched(passage, groups)
                    if not matches:
                        continue
                    coverage = len(matches) / len(groups)
                    title = text.split('title:', 1)[-1].splitlines()[0] if 'title:' in text else path
                    score = coverage + .2 * len(matched(title, groups)) / len(groups) + .1 * len(matched(titles[number - 1], groups)) / len(groups)
                    found.append(dict(repo=str(repo), sha=sha, path=path, heading=titles[number - 1],
                                      line_start=start + 1, line_end=end, quote=passage,
                                      url=public_url(repo, path, text), matched_terms=matches,
                                      coverage=round(coverage, 4), score=round(score, 4), strength='full term coverage' if coverage == 1 else 'weak hit'))
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            if not searched or searched[-1].get('repo') != str(repo):
                searched.append(dict(repo=str(repo), ref=ref, sha=None))
            searched[-1]['error'] = str(exc)
    found.sort(key=lambda c: (-c['score'], c['repo'], c['path'], c['line_start']))
    # Avoid filling the result with overlapping snippets from a single section.
    selected, seen = [], set()
    for candidate in found:
        key = (candidate['repo'], candidate['path'])
        if key not in seen:
            selected.append(candidate)
            seen.add(key)
        if len(selected) == top:
            break
    return selected, searched


def fetch(url: str) -> dict:
    try:
        with urlopen(url, timeout=SETTINGS['timeout_seconds']) as response:
            text = response.read(4 * 1024 * 1024 + 1).decode('utf-8', errors='replace')
        if len(text.encode('utf-8')) > 4 * 1024 * 1024:
            return dict(url=url, status='unreachable', error='response exceeds 4 MiB limit')
        return dict(url=url, status='live', text=text)
    except (OSError, URLError, ValueError) as exc:
        return dict(url=url, status='unreachable', error=str(exc))


def snapshot_candidates(root, groups, top):
    entries = read_snapshot(root)
    found = []
    for entry in entries:
        if Path(entry['path']).suffix.lower() not in ('.md', '.mdx') or not groups:
            continue
        text = Path(entry['filename']).read_text(encoding='utf-8')
        lines = text.splitlines()
        titles = headings(lines)
        passages = []
        for index, line in enumerate(lines):
            if not matched(line, groups):
                continue
            start = max(0, index - 2)
            end = min(len(lines), start + SETTINGS['passage_lines'])
            passage = '\n'.join(lines[start:end])
            matches = matched(passage, groups)
            coverage = len(matches) / len(groups)
            title = text.split('title:', 1)[-1].splitlines()[0] if 'title:' in text else entry['path']
            score = coverage + .2 * len(matched(title, groups)) / len(groups) + .1 * len(matched(titles[index], groups)) / len(groups)
            passages.append(dict(repo=entry['repo'], path=entry['path'], sha=entry['sha'], source_url=entry['url'],
                                 heading=titles[index], line_start=start + 1, line_end=end, quote=passage,
                                 url=public_url(Path(entry['repo']), entry['path'], text), matched_terms=matches,
                                 coverage=round(coverage, 4), score=round(score, 4),
                                 strength='full term coverage' if coverage == 1 else 'weak hit'))
        if passages:
            found.append(sorted(passages, key=lambda p: (-p['score'], p['line_start']))[0])
    found.sort(key=lambda p: (-p['score'], p['repo'], p['path'], p['line_start']))
    return found[:top], [{k: v for k, v in e.items() if k != 'filename'} for e in entries]


def web_check(found: list[dict]) -> list[dict]:
    indexes = ['https://docs.moderntreasury.com' + p['url_prefix'] + 'llms.txt'
               for name, p in PROJECTS.items() if name != 'reference']
    urls = sorted({c['url'] + '.md' for c in found} | set(indexes))
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = dict(zip(urls, pool.map(fetch, urls)))
    for candidate in found:
        response = responses[candidate['url'] + '.md']
        candidate['web'] = {k: v for k, v in response.items() if k != 'text'}
        if response['status'] == 'live':
            candidate['web'].update(live=True, status='ok' if candidate['quote'] in response['text'].replace('\r\n', '\n') else 'mismatch')
    for url in indexes:
        response = responses[url]
        if response['status'] == 'live':
            body = response['text']
            missing = [c['url'] for c in found if c['url'].startswith(url.removesuffix('llms.txt')) and c['url'] not in body]
            response['status'] = 'empty' if not body.strip() else 'incomplete' if missing or 'https://' not in body else 'live'
            response['missing_candidates'] = missing
        response.pop('text', None)
    return [{k: v for k, v in responses[url].items() if k != 'text'} for url in urls]


def gh_api(endpoint: str, query: str | None = None) -> dict | list:
    command = ['gh', 'api', '--method', 'GET', endpoint]
    if query is not None:
        command += ['-f', 'q=' + query, '-f', 'per_page=' + str(SETTINGS['pr_limit'])]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError(result.stderr.strip())
    return json.loads(result.stdout)


def pr_search(repos: list[Path], groups: list[list[str]], days: int) -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    queries = [f'repo:{SETTINGS["github_owner"]}/{repo.name} is:pr {state}' for repo in repos
               for state in ('is:open', f'is:merged merged:>={cutoff}')]
    result = dict(queries=queries, terms=groups, matches=[], notes=[])
    if not shutil.which('gh'):
        result['notes'].append('PR search not run: gh missing; no --prs input supplied')
        return result
    items = {}
    successful = 0
    for query in queries:
        try:
            response = gh_api('search/issues', query)
            successful += 1
            if response.get('incomplete_results') or response['total_count'] > len(response['items']):
                result['notes'].append(f'incomplete PR search: {query}')
            for item in response['items']:
                items[item['url']] = item
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            result['notes'].append(f'{query}: {exc}')
    if not successful:
        result['notes'].append('PR search not run: no successful gh queries and no --prs input supplied')
    def inspect(item):
        endpoint = item['repository_url'].split('api.github.com/')[-1] + '/pulls/' + str(item['number'])
        try:
            detail = gh_api(endpoint)
            texts = [('title', detail['title']), ('body', detail.get('body') or '')]
            page, unavailable, file_count = 1, [], 0
            while True:
                files = gh_api(endpoint + f'/files?per_page=100&page={page}')
                file_count += len(files)
                unavailable.extend(f['filename'] for f in files if 'patch' not in f)
                texts.extend((f['filename'], f.get('patch') or '') for f in files)
                if len(files) < 100:
                    break
                page += 1
            matching = [f'{name}: {line}' for name, text in texts for line in text.splitlines() if matched(line, groups)]
            warnings = []
            if unavailable or detail.get('changed_files', file_count) > file_count:
                warnings.append(f'{endpoint}: incomplete patches; unavailable={unavailable}, files={file_count}')
            if not matching:
                return dict(warnings=warnings) if warnings else None
            coverage = len(matched('\n'.join(text for _, text in texts), groups)) / len(groups) if groups else 0
            title_coverage = len(matched(detail['title'], groups))
            return dict(number=detail['number'], state=detail['state'], merged_at=detail.get('merged_at'),
                        url=detail['html_url'], title=detail['title'], matched_lines=matching[:8],
                        matched_line_count=len(matching), coverage=coverage, title_matches=title_coverage,
                        warnings=warnings, repository=item['repository_url'].split('/repos/')[-1])
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            return dict(error=f'{endpoint}: {exc}')
    with ThreadPoolExecutor(max_workers=4) as pool:
        for match in pool.map(inspect, [items[key] for key in sorted(items)]):
            if match and 'error' in match:
                result['notes'].append(match['error'])
            elif match:
                result['notes'].extend(match.pop('warnings', []))
                if 'number' in match:
                    result['matches'].append(match)
    result['matches'].sort(key=lambda p: (-p['coverage'], -p['title_matches'], p['repository'], p['number']))
    return result


def connector_prs(path, groups, days):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'cannot read --prs JSON: {exc}') from exc
    items = data.get('items') if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError('--prs must be an array or an object with an items array')
    result = dict(queries=['connector input: ' + str(path)], terms=groups, matches=[],
                  notes=['Connector input coverage is caller-supplied; patches may be incomplete.'])
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    for item in items:
        if not isinstance(item, dict) or type(item.get('number')) is not int or item['number'] < 1:
            raise ValueError('PR item requires a positive integer number')
        if not isinstance(item.get('title'), str) or item.get('state') not in ('open', 'closed', 'merged'):
            raise ValueError('PR item requires title and state open/closed/merged')
        url = item.get('html_url')
        repo = item.get('repo')
        if repo is None:
            repository_url = item.get('repository_url', '')
            repo = repository_url.split('/repos/')[-1] if isinstance(repository_url, str) else None
        if not isinstance(repo, str):
            raise ValueError('PR item requires a string repo or repository_url')
        if repo in {p.name for p in default_repos()}:
            repo = SETTINGS['github_owner'] + '/' + repo
        if repo not in {SETTINGS['github_owner'] + '/' + p.name for p in default_repos()} or not isinstance(url, str) or not url.startswith('https://'):
            raise ValueError('PR item requires a known repo and https html_url')
        pull_request = item.get('pull_request') or {}
        if not isinstance(pull_request, dict):
            raise ValueError('PR pull_request must be an object')
        merged = item.get('merged_at') or pull_request.get('merged_at')
        try:
            merged_date = datetime.fromisoformat(merged.replace('Z', '+00:00')) if merged else None
            if merged_date is not None and merged_date.tzinfo is None:
                raise ValueError('timezone required')
        except (ValueError, AttributeError) as exc:
            raise ValueError('PR merged_at must be a timezone-aware ISO timestamp or null') from exc
        texts = [item['title'], *('' if item.get(k) is None else item[k] for k in ('body', 'patch'))]
        if not all(isinstance(t, str) for t in texts):
            raise ValueError('PR body and optional patch must be strings or null')
        if item['state'] == 'merged' and not merged_date:
            raise ValueError('merged PR state requires merged_at')
        if item['state'] != 'open' and not (merged_date and merged_date >= cutoff):
            continue
        matching = [line for text in texts for line in text.splitlines() if matched(line, groups)]
        if matching:
            result['matches'].append(dict(number=item['number'], title=item['title'], state='merged' if merged else item['state'],
                merged_at=merged, url=url, repository=repo, matched_lines=matching[:8], matched_line_count=len(matching),
                coverage=len(matched('\n'.join(texts), groups)) / len(groups), title_matches=len(matched(item['title'], groups))))
    result['matches'].sort(key=lambda p: (-p['coverage'], -p['title_matches'], p['repository'], p['number']))
    return result


def locate(question, repos, ref='origin/v2.0', top=None, web=True, prs=True, days=90, snapshot_dir=None, prs_file=None):
    groups = terms(question)
    found, searched = (snapshot_candidates(snapshot_dir, groups, top or SETTINGS['top']) if snapshot_dir
                       else candidates(repos, ref, groups, top or SETTINGS['top']))
    return dict(question=question, judgment=NOTICE, status='candidate locations' if found else 'not found',
                candidates=found, searched=dict(repositories=searched, terms=groups,
                urls=web_check(found) if web else [], web='enabled' if web else 'disabled',
                prs=(connector_prs(prs_file, groups, days) if prs_file else pr_search(repos, groups, days)) if prs
                else dict(queries=[], matches=[], notes=['PR search not run: disabled'])))


def render(report):
    rows = [report['status'], report['judgment']]
    for candidate in report['candidates']:
        rows += [f"{candidate['repo']}/{candidate['path']}:{candidate['line_start']}-{candidate['line_end']} [{candidate['heading']}] {candidate['strength']} coverage={candidate['coverage']}",
                 candidate['url'], candidate['quote']]
        if 'web' in candidate:
            rows.append('web: ' + json.dumps(candidate['web']))
    rows += ['searched:', json.dumps(report['searched'], indent=2, ensure_ascii=False)]
    return '\n'.join(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('question')
    parser.add_argument('--repos', nargs='+', type=Path)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--prs', type=Path)
    parser.add_argument('--ref', default='origin/v2.0')
    parser.add_argument('--no-web', action='store_true')
    parser.add_argument('--no-prs', action='store_true')
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--top', type=int, default=SETTINGS['top'])
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    if args.days < 0 or args.top < 1:
        parser.error('--days must be nonnegative and --top must be positive')
    if bool(args.snapshot) == bool(args.repos):
        parser.error('provide --snapshot DIR (runtime) or --repos DIR... (development), not both')
    if args.prs and args.no_prs:
        parser.error('--prs and --no-prs cannot be combined')
    try:
        report = locate(args.question, args.repos or default_repos(), args.ref, args.top,
                        not args.no_web, not args.no_prs, args.days, args.snapshot, args.prs)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else render(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
