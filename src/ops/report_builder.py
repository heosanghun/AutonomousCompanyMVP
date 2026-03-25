"""Build daily and weekly markdown reports from runtime artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_daily_report(summary_path: str | Path, report_path: str | Path, notes: List[str] | None = None) -> None:
    summary = _load_json(Path(summary_path))
    metrics = summary.get("metrics", {})
    n_updates = summary.get("n_updates", 0)
    n_interrupts = summary.get("n_interrupts", 0)
    kill_switch = summary.get("kill_switch", False)

    lines = [
        "# Daily Autonomous Ops Report",
        "",
        f"- generated_at_utc: `{_iso_now()}`",
        f"- kill_switch: `{kill_switch}`",
        f"- n_updates: `{n_updates}`",
        f"- n_interrupts: `{n_interrupts}`",
        "",
        "## Performance",
        f"- cagr: `{metrics.get('cagr')}`",
        f"- sharpe: `{metrics.get('sharpe')}`",
        f"- sortino: `{metrics.get('sortino')}`",
        f"- mdd: `{metrics.get('mdd')}`",
        f"- win_rate: `{metrics.get('win_rate')}`",
        "",
        "## Runtime",
        f"- latency_mean_ms: `{metrics.get('latency_mean_ms')}`",
        f"- latency_p95_ms: `{metrics.get('latency_p95_ms')}`",
        f"- latency_p99_ms: `{metrics.get('latency_p99_ms')}`",
        "",
        "## Notes"
    ]
    if notes:
        lines.extend([f"- {n}" for n in notes])
    else:
        lines.append("- No additional notes.")

    p = Path(report_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_weekly_report(daily_reports_dir: str | Path, report_path: str | Path) -> None:
    d = Path(daily_reports_dir)
    reports = sorted(d.glob("daily_*.md"))
    lines = [
        "# Weekly Autonomous Ops Report",
        "",
        f"- generated_at_utc: `{_iso_now()}`",
        f"- daily_report_count: `{len(reports)}`",
        "",
        "## Included Reports"
    ]
    if not reports:
        lines.append("- No daily reports found.")
    else:
        for r in reports:
            lines.append(f"- `{r.name}`")

    p = Path(report_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
