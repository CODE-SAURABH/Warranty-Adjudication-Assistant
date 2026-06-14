from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonStore:
    """Small JSON file repository used by local services."""

    def read(self, path: Path) -> Any:
        if not path.exists():
            raise FileNotFoundError(f"Missing data file: {path}")
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON in {path}: {exc}") from exc

    def write(self, path: Path, payload: Any) -> None:
        path.write_text(json.dumps(payload, indent=2))

    def append_item(self, path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
        current = self.read(path)
        if not isinstance(current, list):
            raise ValueError(f"Expected JSON array in {path}.")
        current.append(payload)
        self.write(path, current)
        return current

