"""Load exchange API credentials into os.environ (never log secret values)."""

from __future__ import annotations

import json
import os
from pathlib import Path


def load_exchange_credentials_from_file(root: Path, overwrite: bool = False) -> bool:
    """Load secrets/exchange_credentials.json into environment.

    If overwrite is False, only sets keys that are missing or empty in os.environ.
    """
    sec_path = root / "secrets" / "exchange_credentials.json"
    if not sec_path.is_file():
        return False
    try:
        data = json.loads(sec_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    key = str(data.get("EXCHANGE_API_KEY", "")).strip()
    secret = str(data.get("EXCHANGE_API_SECRET", "")).strip()
    if not key or not secret:
        return False
    if overwrite:
        os.environ["EXCHANGE_API_KEY"] = key
        os.environ["EXCHANGE_API_SECRET"] = secret
        return True
    if not os.environ.get("EXCHANGE_API_KEY", "").strip():
        os.environ["EXCHANGE_API_KEY"] = key
    if not os.environ.get("EXCHANGE_API_SECRET", "").strip():
        os.environ["EXCHANGE_API_SECRET"] = secret
    return True
