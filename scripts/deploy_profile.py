"""Print deployment profile (shadow / canary / production) hints for operators."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="shadow", help="shadow|canary|production")
    args = parser.parse_args()
    p = Path("configs/deployment_profile.json")
    if not p.exists():
        print(json.dumps({"error": "missing_configs/deployment_profile.json"}, ensure_ascii=True))
        return 1
    cfg = json.loads(p.read_text(encoding="utf-8"))
    prof = str(args.profile).lower()
    block = cfg.get(prof, {})
    payload = {
        "selected": prof,
        "config": block,
        "rollback": cfg.get("rollback", {}),
        "env_hints": {
            "EXECUTION_MODE": block.get("execution_mode", "paper"),
            "MARKET_DATA_SOURCE": "mock or binance_rest",
        },
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
