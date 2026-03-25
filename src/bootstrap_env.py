"""Load local .env / .ENV into os.environ (no extra dependencies)."""

from __future__ import annotations

import os
from pathlib import Path


def _parse_env_file(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if text.startswith("\ufeff"):
        text = text[1:]
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip().lstrip("\ufeff")
        val = val.strip().strip('"').strip("'")
        if key and val:
            out[key] = val
    return out


def load_dotenv_files(root: Path | None = None) -> None:
    """Merge `.env` then `.ENV` (later overrides). Apply only if unset or empty in os.environ."""
    base = root or Path(__file__).resolve().parents[1]
    merged: dict[str, str] = {}
    for name in (".env", ".ENV"):
        path = base / name
        if not path.is_file():
            continue
        merged.update(_parse_env_file(path))
    for key, val in merged.items():
        cur = os.environ.get(key, "")
        if key not in os.environ or not str(cur).strip():
            os.environ[key] = val
