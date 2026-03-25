"""Smoke-test Gemini API key from env (never prints the key)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bootstrap_env import load_dotenv_files


def main() -> int:
    os.chdir(ROOT)
    load_dotenv_files(ROOT)
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        print("RESULT=no_key: set GEMINI_API_KEY in .env or .ENV and save the file")
        return 1
    # Names must match v1beta ListModels (1.5-* names often retired for new keys).
    models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-flash-latest",
    ]
    payload = json.dumps(
        {"contents": [{"parts": [{"text": "Reply with exactly OK"}]}]}
    ).encode("utf-8")
    last: object = None
    for m in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
        req = urllib.request.Request(
            url, data=payload, method="POST", headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                data = json.loads(r.read().decode("utf-8"))
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = (parts[0].get("text", "") if parts else "").strip()
            print("RESULT=ok")
            print(f"MODEL={m}")
            print(f"RESPONSE_PREFIX={text[:80]!r}")
            return 0
        except urllib.error.HTTPError as e:
            last = (m, e.code, e.read()[:400].decode("utf-8", errors="replace"))
        except Exception as e:
            last = (m, type(e).__name__, str(e)[:200])
    print("RESULT=fail")
    print(f"LAST={last!r}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
