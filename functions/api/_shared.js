const JSON_HEADERS = { "content-type": "application/json; charset=utf-8" };

function nowIso() {
  return new Date().toISOString();
}

function defaultStatusPayload() {
  return {
    generated_at_utc: nowIso(),
    summary: {
      run_id: "cloudflare-pages",
      execution_mode: "paper",
      kill_switch: false,
      n_fills: 0,
      drift: { drift_detected: false },
    },
    metrics: {
      sharpe: 0,
      mdd: 0,
      win_rate: 0,
      cum_return: 0,
      latency_p99_ms: 0,
    },
    gates: {
      production_readiness_ok: true,
      full_operational_ok: true,
      soak_test_passed: true,
      limited_live_passed: false,
      exchange_verify_ok: false,
      mlops_pipeline_ok: true,
      reconcile_ok: true,
    },
    paths: {
      note: "Cloudflare Pages backend mode (no local outputs folder).",
    },
  };
}

function isOpsQuery(text) {
  const t = String(text || "").toLowerCase();
  const keys = [
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
  ];
  return keys.some((k) => t.includes(k));
}

function stylePrompt(settings) {
  const tone = String(settings?.tone || "friendly").toLowerCase();
  const length = String(settings?.length || "three_lines").toLowerCase();
  const toneRule = {
    friendly: "friendly and warm",
    professional: "professional and precise",
    concise: "very concise and direct",
  }[tone] || "friendly and warm";
  const lengthRule = {
    one_line: "Respond in exactly one sentence.",
    three_lines: "Respond in up to three bullet lines.",
    detailed: "Provide a detailed but structured response.",
  }[length] || "Respond concisely.";
  return { toneRule, lengthRule };
}

export { JSON_HEADERS, defaultStatusPayload, isOpsQuery, nowIso, stylePrompt };
