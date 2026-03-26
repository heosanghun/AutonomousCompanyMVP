import { forbiddenJson, getCurrentUser, hasRole, unauthorizedJson } from "../_auth.js";
import { ensureSchema } from "../_db.js";
import { JSON_HEADERS, nowIso } from "../_shared.js";

async function record(env, eventType, severity, payload) {
  await env.DB.prepare(
    `INSERT INTO ops_events (id, event_type, severity, payload_json, created_at)
     VALUES (?1, ?2, ?3, ?4, ?5)`,
  )
    .bind(crypto.randomUUID(), eventType, severity, JSON.stringify(payload || {}), nowIso())
    .run();
}

export async function onRequestPost(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  if (!hasRole(user, "operator")) return forbiddenJson("operator");

  const body = await context.request.json();
  const incidentType = String(body?.incident_type || "unknown_incident");
  const maxRetries = Math.max(1, Math.min(5, Number(body?.max_retries || 3)));
  const baseDelayMs = Math.max(200, Math.min(5000, Number(body?.base_delay_ms || 500)));
  const simulateFailures = Math.max(0, Math.min(maxRetries, Number(body?.simulate_failures || 1)));

  const attempts = [];
  let success = false;
  for (let i = 1; i <= maxRetries; i += 1) {
    const willFail = i <= simulateFailures;
    attempts.push({
      attempt: i,
      wait_ms_before_next: willFail ? baseDelayMs * (2 ** (i - 1)) : 0,
      result: willFail ? "failed" : "success",
    });
    await record(env, "recovery_attempt", willFail ? "warn" : "info", {
      incident_type: incidentType,
      attempt: i,
      actor_id: user.id,
      result: willFail ? "failed" : "success",
    });
    if (!willFail) {
      success = true;
      break;
    }
  }

  if (!success) {
    await record(env, "recovery_escalation", "high", {
      incident_type: incidentType,
      reason: "max_retries_exceeded",
      actor_id: user.id,
    });
  }

  return new Response(
    JSON.stringify({
      ok: success,
      incident_type: incidentType,
      actor_id: user.id,
      strategy: "exponential_backoff",
      attempts,
      escalated: !success,
      next_action: success ? "monitor" : "rollback_and_human_notify",
    }),
    { status: success ? 200 : 409, headers: JSON_HEADERS },
  );
}
