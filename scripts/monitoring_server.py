"""Local monitoring web server for AutonomousCompanyMVP."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bootstrap_env import load_dotenv_files
from src.agentic.observe_agent import summarize_status
from src.agentic.propose_agent import propose_next_actions

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
    mlops = _read_json(OUTPUTS_DIR / "mlops" / "pipeline_result.json")

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
            "mlops_pipeline_ok": bool(mlops.get("ok", False)),
            "reconcile_ok": bool(summary.get("reconcile", {}).get("ok", False)) if isinstance(summary, dict) else False,
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


def build_observe_payload() -> dict:
    status = build_status_payload()
    return {
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "observe": summarize_status(status),
    }


def build_propose_payload() -> dict:
    status = build_status_payload()
    prod = _read_json(OUTPUTS_DIR / "production_readiness_report.json")
    errors = prod.get("errors", []) if isinstance(prod, dict) else []
    gates = status.get("gates", {}) if isinstance(status, dict) else {}
    return {
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "proposal": propose_next_actions({"errors": errors, "gates": gates}),
    }


def _is_ops_query(text: str) -> bool:
    t = (text or "").lower()
    keywords = (
        "운영",
        "상태",
        "게이트",
        "리스크",
        "위험",
        "조치",
        "지표",
        "샤프",
        "킬스위치",
        "드리프트",
        "latency",
        "p99",
        "reconcile",
        "pipeline",
        "run_id",
        "gate",
        "risk",
        "ops",
    )
    return any(k in t for k in keywords)


def _gemini_chat_reply(
    user_text: str,
    status: dict,
    history: list[dict] | None = None,
    settings: dict | None = None,
) -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("missing_gemini_api_key")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    settings = settings or {}
    tone = str(settings.get("tone", "friendly")).strip().lower()
    length = str(settings.get("length", "normal")).strip().lower()
    route_mode = str(settings.get("route_mode", "auto")).strip().lower()
    route = "ops" if route_mode == "ops" else ("general" if route_mode == "general" else ("ops" if _is_ops_query(user_text) else "general"))
    tone_rule = {
        "friendly": "friendly and warm",
        "professional": "professional and precise",
        "concise": "very concise and direct",
    }.get(tone, "friendly and warm")
    length_rule = {
        "one_line": "Respond in exactly one sentence.",
        "three_lines": "Respond in up to three bullet lines.",
        "detailed": "Provide a detailed but structured response.",
        "normal": "Keep response concise.",
    }.get(length, "Keep response concise.")
    safe_status = {
        "metrics": status.get("metrics", {}),
        "gates": status.get("gates", {}),
        "execution_mode": (status.get("summary", {}) or {}).get("execution_mode"),
        "kill_switch": (status.get("summary", {}) or {}).get("kill_switch"),
    }
    system_prompt_base = (
        "You are an ops assistant for an autonomous company dashboard. "
        "Answer in Korean. "
        f"Style: {tone_rule}. "
        f"Length rule: {length_rule} "
    )
    route_prompt = (
        "This is an operations-focused query. "
        "Use given runtime status as ground truth, and provide practical prioritized actions."
        if route == "ops"
        else "This is a general conversation query. Keep it natural and helpful; only mention ops status if user asks."
    )
    contents: list[dict] = [
        {"role": "user", "parts": [{"text": f"{system_prompt_base}\n{route_prompt}"}]}
    ]
    if route == "ops":
        contents.append({"role": "user", "parts": [{"text": f"Status JSON:\n{json.dumps(safe_status, ensure_ascii=True)}"}]})
    for item in (history or []):
        role_raw = str(item.get("role", "user")).lower()
        role = "model" if role_raw == "assistant" else "user"
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        contents.append({"role": role, "parts": [{"text": text[:2000]}]})
    payload = {
        "contents": contents + [{"role": "user", "parts": [{"text": user_text}]}]
    }
    raw = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    req = urllib.request.Request(url, data=raw, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode("utf-8") or "{}")
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = (parts[0].get("text", "") if parts else "").strip()
    if not text:
        raise RuntimeError("empty_gemini_response")
    return text


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
        if parsed.path == "/api/observe":
            payload = build_observe_payload()
            raw = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/api/propose":
            payload = build_propose_payload()
            raw = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/metrics":
            st = build_status_payload()
            m = st.get("metrics", {}) if isinstance(st, dict) else {}
            gates = st.get("gates", {}) if isinstance(st, dict) else {}
            summ = st.get("summary", {}) if isinstance(st, dict) else {}
            drift = summ.get("drift", {}) if isinstance(summ, dict) else {}
            reconcile = summ.get("reconcile", {}) if isinstance(summ, dict) else {}
            n_fills = float(summ.get("n_fills") or 0) if isinstance(summ, dict) else 0.0
            kill_sw = 1.0 if (isinstance(summ, dict) and summ.get("kill_switch")) else 0.0
            drift_det = 1.0 if (isinstance(drift, dict) and drift.get("drift_detected")) else 0.0
            recon_ok = 1.0 if reconcile.get("ok") else 0.0
            lines = [
                "# HELP acmvp_sharpe Sharpe ratio from latest summary.",
                "# TYPE acmvp_sharpe gauge",
                f"acmvp_sharpe {m.get('sharpe') or 0}",
                "# HELP acmvp_mdd Maximum drawdown.",
                "# TYPE acmvp_mdd gauge",
                f"acmvp_mdd {m.get('mdd') or 0}",
                "# HELP acmvp_win_rate Win rate.",
                "# TYPE acmvp_win_rate gauge",
                f"acmvp_win_rate {m.get('win_rate') or 0}",
                "# HELP acmvp_cum_return Cumulative return.",
                "# TYPE acmvp_cum_return gauge",
                f"acmvp_cum_return {m.get('cum_return') or 0}",
                "# HELP acmvp_latency_p99_ms Latency p99 ms.",
                "# TYPE acmvp_latency_p99_ms gauge",
                f"acmvp_latency_p99_ms {m.get('latency_p99_ms') or 0}",
                "# HELP acmvp_n_fills Fill count from summary.",
                "# TYPE acmvp_n_fills gauge",
                f"acmvp_n_fills {n_fills}",
                "# HELP acmvp_kill_switch Kill switch active (1=yes).",
                "# TYPE acmvp_kill_switch gauge",
                f"acmvp_kill_switch {kill_sw}",
                "# HELP acmvp_drift_detected Drift guard triggered (1=yes).",
                "# TYPE acmvp_drift_detected gauge",
                f"acmvp_drift_detected {drift_det}",
                "# HELP acmvp_reconcile_ok Reconcile ok (1=yes).",
                "# TYPE acmvp_reconcile_ok gauge",
                f"acmvp_reconcile_ok {recon_ok}",
                "# HELP acmvp_gate_ok Operational gate (1=ok).",
                "# TYPE acmvp_gate_ok gauge",
                f"acmvp_gate_ok {1 if gates.get('full_operational_ok') else 0}",
            ]
            raw = "\n".join(lines).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/chat":
            self.send_response(404)
            self.end_headers()
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(max(length, 0)) if length > 0 else b"{}"
            req = json.loads(body.decode("utf-8") or "{}")
            user_text = str(req.get("message", "")).strip()
            if not user_text:
                raise ValueError("message_required")
            history = req.get("history", [])
            if not isinstance(history, list):
                history = []
            settings = req.get("settings", {})
            if not isinstance(settings, dict):
                settings = {}
            status = build_status_payload()
            reply = _gemini_chat_reply(user_text, status, history=history, settings=settings)
            payload = {
                "ok": True,
                "reply": reply,
                "provider": "gemini",
                "model": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
                "route": settings.get("route_mode", "auto"),
                "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
            }
            raw = json.dumps(payload, ensure_ascii=True).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        except urllib.error.HTTPError as e:
            try:
                err = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                err = ""
            payload = {"ok": False, "error": f"gemini_http_{e.code}", "detail": err}
        except Exception as e:
            payload = {"ok": False, "error": type(e).__name__, "detail": str(e)[:300]}
        raw = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(400)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--check", action="store_true", help="Print status payload and exit")
    args = parser.parse_args()
    load_dotenv_files(ROOT)

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
