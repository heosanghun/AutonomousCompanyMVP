import { forbiddenJson, getCurrentUser, hasRole, unauthorizedJson } from "../_auth.js";
import { ensureSchema } from "../_db.js";
import { JSON_HEADERS, nowIso } from "../_shared.js";

const RULES = {
  review: { from: "requested", to: "in_review", role: "auditor", field: "reviewed_by" },
  approve: { from: "in_review", to: "approved", role: "admin", field: "approved_by" },
  reject: { from: "in_review", to: "rejected", role: "auditor", field: "reviewed_by" },
  execute: { from: "approved", to: "executed", role: "operator", field: "executed_by" },
  audit: { from: "executed", to: "audited", role: "auditor", field: "audited_by" },
};

async function getRequest(env, id) {
  return env.DB.prepare(`SELECT * FROM workflow_requests WHERE id = ?1`).bind(id).first();
}

export async function onRequestGet(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  if (!hasRole(user, "auditor")) return forbiddenJson("auditor");
  const id = String(context.params?.id || "");
  const req = await getRequest(env, id);
  if (!req) return new Response(JSON.stringify({ ok: false, error: "not_found" }), { status: 404, headers: JSON_HEADERS });
  const events = await env.DB.prepare(`SELECT * FROM workflow_events WHERE request_id = ?1 ORDER BY created_at ASC`).bind(id).all();
  return new Response(JSON.stringify({ ok: true, item: req, events: events.results || [] }), { status: 200, headers: JSON_HEADERS });
}

export async function onRequestPatch(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();

  const id = String(context.params?.id || "");
  const req = await getRequest(env, id);
  if (!req) return new Response(JSON.stringify({ ok: false, error: "not_found" }), { status: 404, headers: JSON_HEADERS });
  const body = await context.request.json();
  const action = String(body?.action || "").toLowerCase();
  const note = String(body?.note || "").trim();
  const rule = RULES[action];
  if (!rule) return new Response(JSON.stringify({ ok: false, error: "invalid_action" }), { status: 400, headers: JSON_HEADERS });
  if (!hasRole(user, rule.role)) return forbiddenJson(rule.role);
  if (String(req.status) !== rule.from) {
    return new Response(
      JSON.stringify({ ok: false, error: "invalid_transition", expected_from: rule.from, current: req.status }),
      { status: 400, headers: JSON_HEADERS },
    );
  }

  const now = nowIso();
  const sql = `UPDATE workflow_requests SET status = ?2, ${rule.field} = ?3, updated_at = ?4 WHERE id = ?1`;
  await env.DB.prepare(sql).bind(id, rule.to, user.id, now).run();
  await env.DB.prepare(
    `INSERT INTO workflow_events (id, request_id, event_type, actor_id, note, created_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6)`,
  )
    .bind(crypto.randomUUID(), id, action, user.id, note || action, now)
    .run();
  return new Response(JSON.stringify({ ok: true, id, status: rule.to }), { status: 200, headers: JSON_HEADERS });
}
