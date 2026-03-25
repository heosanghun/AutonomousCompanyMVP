"""Create external kill switch flag."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = ROOT / "outputs" / "external_kill_switch.flag"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("kill\n", encoding="utf-8")
    print(str(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
