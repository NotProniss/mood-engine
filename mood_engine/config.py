"""Central plugin configuration loader for user-tunable Mood Engine settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PLUGIN_ROOT = Path(__file__).parents[1]
CONFIG_PATH = PLUGIN_ROOT / "config.yml"
EXAMPLE_CONFIG_PATH = PLUGIN_ROOT / "config.example.yml"

with (CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_CONFIG_PATH).open(encoding="utf-8") as file:
    PLUGIN_CONFIG: dict[str, Any] = yaml.safe_load(file) or {}


def config_path(relative_path: str) -> Path:
    """Resolve a path from the plugin-root config relative to the plugin root."""
    return PLUGIN_ROOT / relative_path
