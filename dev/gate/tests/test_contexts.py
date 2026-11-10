import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SKILL = Path(os.environ.get('DOCS_GATE_SKILL', ROOT / 'skill'))
spec = importlib.util.spec_from_file_location('gate_contexts', SKILL / 'docs-review/scripts/contexts.py')
contexts = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = contexts
spec.loader.exec_module(contexts)


def git(folder, *args):
    return subprocess.run(['git', '-C', str(folder), *args], check=True, capture_output=True)


def commit(folder):
    git(folder, 'add', 'page.md')
    git(folder, '-c', 'user.name=Gate fixture', '-c', 'user.email=gate@example.invalid',
        'commit', '-qm', 'Fixture base')


def test_context_membership_and_span_boundaries():
    review = contexts.Context()
    assert review.includes(('always',), 1)
    assert review.includes(('review',), 1)
    assert not review.includes(('draft', 'new', 'touched'), 1)
    assert not review.includes((), 1)
    draft = contexts.Context(mode='draft', new=True)
    assert draft.includes(('draft',), 1)
    assert draft.includes(('new',), 1)
    assert not draft.includes(('review', 'touched'), 1)
    touched = contexts.Context(touched={5, 7})
    assert touched.includes(('touched',), 5)
    assert touched.includes(('touched',), 3, 5)
    assert touched.includes(('touched',), 7, 9)
    assert not touched.includes(('touched',), 3, 4)
    assert not touched.includes(('touched',), 6)
    assert not touched.includes(('touched',), 8, 9)


def test_no_base_does_not_require_git(tmp_path):
    path = tmp_path / 'page.md'
    path.write_text('Text\n')
    assert contexts.file_context(path, 'review', None) == contexts.Context()
    assert contexts.file_context(path, 'draft', None) == contexts.Context(mode='draft', new=True)


def test_git_insert_replace_delete_and_draft(tmp_path):
    git(tmp_path, 'init', '-q')
    path = tmp_path / 'page.md'
    path.write_text('one\ntwo\nthree\nfour\nfive\nsix\n')
    commit(tmp_path)
    assert contexts.file_context(path, 'review', 'HEAD') == contexts.Context()
    assert contexts.file_context(path, 'draft', 'HEAD') == contexts.Context(mode='draft', new=True)
    path.write_text('inserted\none\nreplacement\nthree\nfive\nsix\nlast\n')
    assert contexts.file_context(path, 'review', 'HEAD') == contexts.Context(touched={1, 3, 7})
    assert contexts.file_context(path, 'draft', 'HEAD') == contexts.Context(mode='draft', new=True, touched={1, 3, 7})
    new = tmp_path / 'new.md'
    new.write_text('New\n')
    assert contexts.file_context(new, 'review', 'HEAD') == contexts.Context(new=True)


def test_git_changed_non_utf8_line(tmp_path):
    git(tmp_path, 'init', '-q')
    path = tmp_path / 'page.md'
    path.write_text('one\ntwo\n')
    commit(tmp_path)
    path.write_bytes(b'one\n\xff\n')
    assert contexts.file_context(path, 'review', 'HEAD') == contexts.Context(touched={2})


@pytest.mark.parametrize('repository', [False, True])
def test_invalid_base_is_an_error(tmp_path, repository):
    path = tmp_path / 'page.md'
    path.write_text('Text\n')
    if repository:
        git(tmp_path, 'init', '-q')
        commit(tmp_path)
    with pytest.raises(ValueError) as error:
        contexts.file_context(path, 'review', 'missing')
    assert str(error.value) == f'cannot resolve --base {"missing"!r} for {path}'
