import importlib.util
import subprocess
from pathlib import Path

import pytest

GATE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gate', GATE / 'gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def review(tmp_path, text, rule, mode='review', base=None):
    path = tmp_path / 'page.md'
    path.write_text('---\ntitle: Example\n---\n' + text)
    args = ['--mode', mode]
    if base:
        args += ['--base', base]
    return [f for f in gate.check([path], args, project='payments')['findings'] if f['rule'] == rule]


def test_curl_request_and_non_request_tags(tmp_path):
    assert [f['line'] for f in review(tmp_path, '```shell cURL\ncurl https://example.com\n```\n', 'fence-language')] == [4]
    assert not review(tmp_path, '```curl cURL\ncurl https://example.com\n```\n```shell\nnpm install\n```\n', 'fence-language')


def test_callout_pairs_and_variation_selectors(tmp_path):
    assert len(review(tmp_path, '<Callout theme=\'warn\' icon="📘️">\nText\n</Callout>\n', 'callout-emoji')) == 1
    assert not review(tmp_path, '<Callout theme="info" icon="📘️">\nText\n</Callout>\n', 'callout-emoji')


def test_own_project_and_relative_links(tmp_path):
    findings = review(tmp_path, '[Accounts](https://docs.moderntreasury.com/payments/docs/accounts)\n\n[Account](../x.md)\n\n[Ledger](https://docs.moderntreasury.com/ledgers/docs/x)\n\n[Account](doc:x)\n', 'link-absolute-internal')
    assert [(f['line'], f['fix']) for f in findings] == [(4, 'doc:accounts'), (6, 'doc:x')]


def test_filler_leverage_and_phrases(tmp_path):
    assert len(review(tmp_path, 'Leverage robust tools seamlessly with our SE team.\n', 'marketing-words')) == 4
    assert not review(tmp_path, 'The leverage ratio measures financial leverage.\n', 'marketing-words')
    assert not review(tmp_path, 'Leverage robust tools seamlessly with our SE team.\n', 'filler')


@pytest.mark.parametrize('rule,text', [('em-dash', 'Text — text.'), ('marketing-words', 'Use robust tools.')])
def test_authored_bans_are_strict_only_in_draft(tmp_path, rule, text):
    assert [f['strict'] for f in review(tmp_path, text, rule, 'review')] == [False]
    assert [f['strict'] for f in review(tmp_path, text, rule, 'draft')] == [True]


def test_em_dash_prose_not_code_or_tables(tmp_path):
    text = 'Text — text.\n\n`code — code`\n\n```text\ncode — code\n```\n\n| A |\n|---|\n| X — Y |\n'
    assert [f['line'] for f in review(tmp_path, text, 'em-dash')] == [4]


def test_em_dash_component_prose_and_html_exclusions(tmp_path):
    text = '<Callout icon="📘" theme="info">\nText — text with `code — code`.\n</Callout>\n\n<table><tr><td>Table — table</td></tr></table>\n\n<pre>Code — code</pre>\n'
    assert [f['line'] for f in review(tmp_path, text, 'em-dash')] == [5]


def test_body_h1_review_and_draft(tmp_path):
    assert not review(tmp_path, '## Start\n', 'body-h1')
    assert [f['line'] for f in review(tmp_path, '## Start\n', 'body-h1', mode='draft')] == [4]
    assert not review(tmp_path, '# Start\n\n## Next\n', 'body-h1', mode='draft')


def test_image_alt_review_and_draft(tmp_path):
    assert not review(tmp_path, '<Image src="x.png" />\n', 'image-alt')
    assert len(review(tmp_path, '<Image src="x.png" alt="" />\n', 'image-alt', mode='draft')) == 1
    assert not review(tmp_path, '<Image src="x.png" alt="A chart" />\n', 'image-alt', mode='draft')


def test_base_new_and_touched_images(tmp_path):
    def git(*args):
        return subprocess.run(['git', '-C', str(tmp_path), *args], check=True, capture_output=True, text=True)
    git('init', '-q')
    path = tmp_path / 'page.md'
    path.write_text('---\ntitle: Example\n---\n<Image\n  src="old.png"\n/>\n\n![](untouched.png)\n')
    git('add', 'page.md')
    git('-c', 'user.name=Gate fixture', '-c', 'user.email=gate@example.invalid', 'commit', '-qm', 'Fixture base')
    fs = review(tmp_path, '<Image\n  src="changed.png"\n/>\n\n![](untouched.png)\n', 'image-alt', base='HEAD')
    assert [f['line'] for f in fs] == [4]
    assert not review(tmp_path, '## Existing\n', 'body-h1', base='HEAD')
    new = tmp_path / 'new.md'
    new.write_text('---\ntitle: New\n---\n## Start\n')
    assert [f['line'] for f in gate.check([new], ['--base', 'HEAD'], project='payments')['findings'] if f['rule'] == 'body-h1'] == [4]


def test_invalid_base_fails_closed(tmp_path):
    with pytest.raises(RuntimeError, match='checker exit 2'):
        review(tmp_path, '## Start\n', 'body-h1', base='does-not-exist')


def test_touched_multiline_markdown_image(tmp_path):
    subprocess.run(['git', '-C', str(tmp_path), 'init', '-q'], check=True)
    path = tmp_path / 'page.md'
    path.write_text('---\ntitle: Example\n---\n![](\nold.png\n)\n\n![](untouched.png)\n')
    subprocess.run(['git', '-C', str(tmp_path), 'add', 'page.md'], check=True)
    subprocess.run(['git', '-C', str(tmp_path), '-c', 'user.name=Gate fixture',
                    '-c', 'user.email=gate@example.invalid', 'commit', '-qm', 'Fixture base'], check=True)
    findings = review(tmp_path, '![](\nchanged.png\n)\n\n![](untouched.png)\n', 'image-alt', base='HEAD')
    assert [f['line'] for f in findings] == [4]
