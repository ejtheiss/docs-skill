"""Import barrier only. Claude performs reviewed live writes through MCP."""
import os

if os.environ.get('DOCS_AUTOPILOT_DRY_RUN') == '1':
    raise RuntimeError('live writer imports are forbidden during dry-run')
