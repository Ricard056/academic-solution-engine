"""Asserts the runtime config copy stays identical to the bible source.

config/display_defaults/default.json is the runtime copy of
bible/50_config_defaults_global_v3_2.json (see CLAUDE.md). If they drift,
this guard fails and names both files.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "display_defaults" / "default.json"
BIBLE_PATH = PROJECT_ROOT / "bible" / "50_config_defaults_global_v3_2.json"

DRIFT_MESSAGE = (
    "config/display_defaults/default.json no longer matches "
    "bible/50_config_defaults_global_v3_2.json — the runtime copy must stay "
    "identical to the bible source (CLAUDE.md / bible 50)"
)


def test_config_default_matches_bible_50_bytes():
    config_text = CONFIG_PATH.read_text(encoding="utf-8")
    bible_text = BIBLE_PATH.read_text(encoding="utf-8")
    assert config_text == bible_text, DRIFT_MESSAGE


def test_config_default_matches_bible_50_as_json():
    # Belt and braces: even if whitespace ever legitimately differs, the
    # parsed content must be equal (this currently passes trivially given
    # byte equality, but localizes WHAT drifted if the byte test fails).
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    bible = json.loads(BIBLE_PATH.read_text(encoding="utf-8"))
    assert config == bible, DRIFT_MESSAGE
