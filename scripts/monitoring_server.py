"""Local monitoring web server for AutonomousCompanyMVP."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web" / "monitoring"
OUTPUTS_DIR = ROOT / "outputs"


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_status_payload() -> dict:
    summary = _read_json(OUTPUTS_DIR / "summary.json")
    prod = _read_json(OUTPUTS_DIR / "production_readiness_report.json")
    full_gate = _read_json(OUTPUTS_DIR / "full_operational_gate_report.json")
    soak = _read_json(OUTPUTS_DIR / "soak_test_report.json")
    live = _read_json(OUTPUTS_DIR / "limited_live_validation_report.json")
    exchange = _read_json(OUTPUTS_DIR / "exchange_verify_report.json")

    metrics = summary.get("metrics", {}) if isinstance(summary, dict) else {}
    return {
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "summary": summary,
        "metrics": {
            "sharpe": metrics.get("sharpe"),
            "mdd": metrics.get("mdd"),
            "win_rate": metrics.get("win_rate"),
            "cum_return": metrics.get("cum_return"),
            "latency_p99_ms": metrics.get("latency_p99_ms"),
        },
        "gates": {
            "production_readiness_ok": bool(prod.get("ok", False)),
            "full_operational_ok": bool(full_gate.get("ok", False)),
            "soak_test_passed": bool(soak.get("passed", False)),
            "limited_live_passed": bool(live.get("passed", False)),
            "exchange_verify_ok": bool(exchange.get("ok", False)),
        },
        "paths": {
            "summary_json": str(OUTPUTS_DIR / "summary.json"),
            "production_readiness_report_json": str(OUTPUTS_DIR / "production_readiness_report.json"),
            "full_operational_gate_report_json": str(OUTPUTS_DIR / "full_operational_gate_report.json"),
            "soak_test_report_json": str(OUTPUTS_DIR / "soak_test_report.json"),
            "limited_live_validation_report_json": str(OUTPUTS_DIR / "limited_live_validation_report.json"),
            "exchange_verify_report_json": str(OUTPUTS_DIR / "exchange_verify_report.json"),
        },
    }


class MonitoringHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            payload = build_status_payload()
            raw = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--check", action="store_true", help="Print status payload and exit")
    args = parser.parse_args()

    WEB_DIR.mkdir(parents=True, exist_ok=True)
    if args.check:
        print(json.dumps(build_status_payload(), ensure_ascii=True, indent=2))
        return 0

    server = ThreadingHTTPServer((args.host, args.port), MonitoringHandler)
    print(f"monitoring_server_started http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
