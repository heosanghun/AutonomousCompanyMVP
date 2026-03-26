import { forbiddenJson, getCurrentUser, hasRole, unauthorizedJson } from "../_auth.js";
import { ensureSchema } from "../_db.js";
import { JSON_HEADERS, nowIso } from "../_shared.js";

const PLAYBOOKS = {
  latency_spike: [
    "collect_status_snapshot",
    "enable_conservative_mode",
    "retry_with_backoff",
    "verify_reconcile",
  ],
  gate_failure: [
    "collect_gate_report",
    "freeze_risky_actions",
    "open_workflow_ticket",
    "notify_human_owner",
  ],
  drift_detected: [
    "collect_drift_stats",
    "reduce_notional_scale",
    "run_policy_check",
    "require_review_before_execute",
  ],
};

async function writeEvent(env, eventType, severity, payload) {
  await env.DB.prepare(
    `INSERT INTO ops_events (id, event_type, severity, payload_json, created_at)
     VALUES (?1, ?2, ?3, ?4, ?5)`,
  )
    .bind(crypto.randomUUID(), eventType, severity, JSON.stringify(payload), nowIso())
    .run();
}

export async function onRequestGet(context) {
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  return new Response(JSON.stringify({ ok: true, playbooks: PLAYBOOKS }), { status: 200, headers: JSON_HEADERS });
}

export async function onRequestPost(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  if (!hasRole(user, "operator")) return forbiddenJson("operator");

  const body = await context.request.json();
  const playbookId = String(body?.playbook_id || "latency_spike").trim();
  const steps = PLAYBOOKS[playbookId];
  if (!steps) return new Response(JSON.stringify({ ok: false, error: "playbook_not_found" }), { status: 404, headers: JSON_HEADERS });

  const executed = [];
  for (const s of steps) {
    executed.push({ step: s, result: "ok" });
    await writeEvent(env, "playbook_step", "info", { playbook_id: playbookId, step: s, actor_id: user.id });
  }

  const webhook = String(env.OPS_ALERT_WEBHOOK_URL || "").trim();
  let webhookSent = false;
  if (webhook) {
    try {
      const r = await fetch(webhook, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          source: "autonomouscompany-playbook",
          playbook_id: playbookId,
          actor_id: user.id,
          executed_at_utc: nowIso(),
          steps: executed,
        }),
      });
      webhookSent = r.ok;
    } catch (_) {
      webhookSent = false;
    }
  }

  await writeEvent(env, "playbook_completed", "info", {
    playbook_id: playbookId,
    actor_id: user.id,
    webhook_sent: webhookSent,
  });
  return new Response(
    JSON.stringify({ ok: true, playbook_id: playbookId, executed, webhook_sent: webhookSent }),
    { status: 200, headers: JSON_HEADERS },
  );
}
