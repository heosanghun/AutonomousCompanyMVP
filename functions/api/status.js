import { JSON_HEADERS, defaultStatusPayload, nowIso } from "./_shared.js";
import { ensureSchema } from "./_db.js";

export async function onRequestGet(context) {
  const payload = defaultStatusPayload();
  payload.generated_at_utc = nowIso();
  const env = context.env || {};
  if (env.DB) {
    await ensureSchema(env);
    const [wf, wfPending, sessions, policyDenied, opsHigh, chatCount] = await Promise.all([
      env.DB.prepare(`SELECT COUNT(*) as c FROM workflow_requests`).first(),
      env.DB.prepare(`SELECT COUNT(*) as c FROM workflow_requests WHERE status IN ('requested','in_review','approved')`).first(),
      env.DB.prepare(`SELECT COUNT(*) as c FROM sessions`).first(),
      env.DB.prepare(`SELECT COUNT(*) as c FROM policy_decisions WHERE allowed = 0`).first(),
      env.DB.prepare(`SELECT COUNT(*) as c FROM ops_events WHERE severity IN ('high','critical')`).first(),
      env.DB.prepare(`SELECT COUNT(*) as c FROM chat_logs`).first(),
    ]);
    payload.summary.workflow_total = Number(wf?.c || 0);
    payload.summary.workflow_pending = Number(wfPending?.c || 0);
    payload.summary.active_sessions = Number(sessions?.c || 0);
    payload.summary.policy_denied = Number(policyDenied?.c || 0);
    payload.summary.high_severity_events = Number(opsHigh?.c || 0);
    payload.summary.chat_total = Number(chatCount?.c || 0);
    payload.metrics.slo_uptime_target = 99.9;
    payload.metrics.error_budget_remaining_pct = Math.max(0, 100 - Number(opsHigh?.c || 0) * 2);
  }
  return new Response(JSON.stringify(payload), { status: 200, headers: JSON_HEADERS });
}
