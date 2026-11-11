from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[3]
# Scenario-specific terms in the KYB, already-shipped, policy and bespoke evals.
# General API vocabulary (identifications, legal entities, addresses) is intentional.
EVAL_TERMS = ['registered agent', 'fbo', 'for benefit of', 'for the benefit of',
              'end user', 'external account', 'ach debit', 'reserve sizing',
              'fremont', 'wyoming', 'fractional', 'juniper example holdings llc', 'kyb example 0042']


def test_config_vocabulary_is_not_scenario_specific():
    tables = [yaml.safe_load((ROOT / 'skill/docs-review/config/locate.yaml').read_text())['synonyms']]
    path = ROOT / 'skill/docs-autopilot/config/autopilot.yaml'
    if path.exists():
        config = yaml.safe_load(path.read_text())
        tables += [config['customer_phrases'], config['topic_weights']]
    for table in tables:
        text = re.sub(r'[-_]+', ' ', yaml.safe_dump(table).lower())
        for token in EVAL_TERMS:
            assert not re.search(r'(?<!\w)' + re.escape(token) + r'(?!\w)', text), token


def test_web_checks_use_markdown_export(monkeypatch):
    import sys
    sys.path.insert(0, str(ROOT / 'skill/docs-review/scripts'))
    import locate
    urls = []
    def fetch(url):
        urls.append(url)
        return dict(url=url, status='live', text='Early Access Feature')
    monkeypatch.setattr(locate, 'fetch', fetch)
    candidate = dict(url='https://docs.moderntreasury.com/platform/reference/reconciliation-rule-object', quote='Early Access Feature')
    locate.web_check([candidate])
    assert candidate['web']['status'] == 'ok'
    assert candidate['url'] + '.md' in urls and candidate['url'] not in urls
