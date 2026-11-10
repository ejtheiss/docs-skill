"""Reserved interface only. No Notion, GitHub or Slack client is implemented."""
import os

if os.environ.get('DOCS_AUTOPILOT_DRY_RUN') == '1':
    raise RuntimeError('live writer imports are forbidden during dry-run')


def publish(*, live=False, config=None):
    if os.environ.get('DOCS_AUTOPILOT_DRY_RUN') == '1':
        raise RuntimeError('live writer calls are forbidden during dry-run')
    if (not live or not config or not config.get('slack_dm_recipient')
            or config['slack_dm_recipient'] == 'REQUIRED-unset' or not config.get('notion', {}).get('data_source_id')):
        raise RuntimeError('live writes require explicit --live and complete configuration')
    raise NotImplementedError('live Notion writer and single Eric DM are not implemented')
