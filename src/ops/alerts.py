"""Simple webhook alerts for operational incidents."""

from __future__ import annotations

import json
import os
import urllib.request


def send_alert(event: str, payload: dict) -> bool:
    """Send alert to webhook if configured; fail silently."""
    url = os.environ.get("OPS_ALERT_WEBHOOK_URL", "").strip()
    if not url:
        return False
    body = json.dumps({"event": event, "payload": payload}, ensure_ascii=True).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8):
            return True
    except Exception:
        return False
