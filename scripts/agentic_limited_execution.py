"""Limited-permission execution agent for guarded live/paper operation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bootstrap_env import load_dotenv_files
from src.main import run


def _approved() -> bool:
    p = ROOT / "outputs" / "human_live_approval.json"
    if not p.exists():
        return False
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(obj.get("approved", False)) and bool(str(obj.get("approved_by", "")).strip())


def main() -> int:
    load_dotenv_files()
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="paper", choices=["paper", "live"])
    parser.add_argument("--out", default="outputs/agentic_execution")
    parser.add_argument("--max-notional-scale", type=float, default=0.1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Hard safety constraints for this agent.
    if args.mode == "live" and not _approved():
        print(json.dumps({"ok": False, "reason": "missing_human_approval_for_live"}, ensure_ascii=True, indent=2))
        return 1
    if args.max_notional_scale <= 0 or args.max_notional_scale > 1.0:
        print(json.dumps({"ok": False, "reason": "invalid_max_notional_scale"}, ensure_ascii=True, indent=2))
        return 1

    os.environ["EXECUTION_MODE"] = args.mode
    os.environ["AGENTIC_EXECUTION_MODE"] = "limited"
    os.environ["MAX_NOTIONAL_SCALE"] = str(args.max_notional_scale)

    if args.dry_run:
        payload = {
            "ok": True,
            "mode": "dry_run",
            "execution_mode": args.mode,
            "max_notional_scale": args.max_notional_scale,
            "note": "No orders executed in dry run.",
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    summary = run(output_dir=args.out)
    out_path = ROOT / args.out / "agentic_execution_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "ok": True,
        "mode": "limited_execution",
        "execution_mode": args.mode,
        "max_notional_scale": args.max_notional_scale,
        "summary": summary,
    }
    out_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

