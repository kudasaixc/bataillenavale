from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


REGISTRY_PATH = Path.home() / ".pipeviewer" / "registry.json"


def register_pipe(pipe_name: str, url: str) -> None:
    registry: Dict[str, Any] = {"pipes": {}}
    if REGISTRY_PATH.exists():
        try:
            with REGISTRY_PATH.open("r", encoding="utf-8") as handle:
                registry = json.load(handle)
        except (json.JSONDecodeError, OSError):
            registry = {"pipes": {}}

    registry.setdefault("pipes", {})[pipe_name] = url

    try:
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with REGISTRY_PATH.open("w", encoding="utf-8") as handle:
            json.dump(registry, handle, indent=2)
    except OSError:
        pass
