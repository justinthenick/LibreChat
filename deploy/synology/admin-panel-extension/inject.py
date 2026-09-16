#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path('/src')


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one injection anchor, found {count}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


sidebar = ROOT / 'src/components/Sidebar.tsx'
replace_once(
    sidebar,
    """  {\n    labelKey: 'com_nav_configuration',\n    path: '/configuration',\n    icon: 'settings',\n    capability: SystemCapabilities.READ_CONFIGS,\n  },\n""",
    """  {\n    labelKey: 'com_nav_configuration',\n    path: '/configuration',\n    icon: 'settings',\n    capability: SystemCapabilities.READ_CONFIGS,\n  },\n  {\n    labelKey: 'com_nav_deployment',\n    path: '/deployment',\n    icon: 'settings',\n  },\n""",
)

app = ROOT / 'src/routes/_app.tsx'
replace_once(
    app,
    "  '/configuration': 'com_config_title',\n",
    "  '/configuration': 'com_config_title',\n  '/deployment': 'com_nav_deployment',\n",
)

translations = ROOT / 'src/locales/en/translation.json'
data = json.loads(translations.read_text(encoding='utf-8'))
if 'com_nav_deployment' in data:
    raise SystemExit('translation already contains com_nav_deployment; upstream layout changed')
data['com_nav_deployment'] = 'Deployment'
translations.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
