from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from football_live_agent.models import Event


class JsonState:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._data = self._load()

    def mark_seen(self, event: Event) -> bool:
        seen = set(self._data.setdefault("seen_event_ids", []))
        if event.event_id in seen:
            return False
        seen.add(event.event_id)
        self._data["seen_event_ids"] = sorted(seen)
        self._save()
        return True

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"seen_event_ids": []}
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2, sort_keys=True)
            handle.write("\n")
