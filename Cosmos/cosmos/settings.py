"""Settings persistence for UI customization."""

from __future__ import annotations

import json
from copy import deepcopy

from cosmos.config import SETTINGS_FILE, ensure_dirs

DEFAULT_SETTINGS: dict = {
    "theme": {
        "accent": "#6366f1",
        "accentSoft": "rgba(99, 102, 241, 0.18)",
        "background": "#0a0a0f",
        "surface": "rgba(255, 255, 255, 0.04)",
        "surfaceHover": "rgba(255, 255, 255, 0.08)",
        "text": "#f4f4f5",
        "textMuted": "#a1a1aa",
        "border": "rgba(255, 255, 255, 0.08)",
    },
    "layout": {
        "radiusSm": "8px",
        "radiusMd": "14px",
        "radiusLg": "20px",
        "radiusXl": "28px",
        "spacing": "16px",
        "gridGap": "18px",
    },
    "controls": {
        "buttonOpacity": "0.72",
        "buttonBlur": "16px",
        "cardOpacity": "0.55",
        "animationSpeed": "0.35s",
        "cornerStyle": "rounded",
    },
}


class SettingsStore:
    """Load and save user UI preferences."""

    def __init__(self) -> None:
        ensure_dirs()
        self._data = deepcopy(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> None:
        if SETTINGS_FILE.exists():
            try:
                stored = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                self._merge(stored)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self, settings: dict) -> None:
        self._merge(settings)
        ensure_dirs()
        SETTINGS_FILE.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def get(self) -> dict:
        return deepcopy(self._data)

    def reset(self) -> dict:
        self._data = deepcopy(DEFAULT_SETTINGS)
        self.save(self._data)
        return self.get()

    def _merge(self, incoming: dict) -> None:
        for section, values in incoming.items():
            if section not in self._data:
                self._data[section] = values
            elif isinstance(values, dict):
                self._data[section].update(values)
            else:
                self._data[section] = values
