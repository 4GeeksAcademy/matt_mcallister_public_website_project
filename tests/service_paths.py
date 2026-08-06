"""Ensure service-specific imports resolve to the intended FastAPI app package."""

from __future__ import annotations

import sys
from pathlib import Path


def prefer_service_path(service_name: str) -> Path:
    root = Path(__file__).resolve().parents[1] / "services" / service_name
    root_str = str(root)
    sys.path = [entry for entry in sys.path if not entry.endswith(f"services/{service_name}")]
    sys.path.insert(0, root_str)
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]
    return root
