import { forbiddenJson, getCurrentUser, hasRole, unauthorizedJson } from "../_auth.js";
import { ensureSchema } from "../_db.js";
import { JSON_HEADERS, nowIso } from "../_shared.js";

export async function onRequestGet(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  if (!hasRole(user, "auditor")) return forbiddenJson("auditor");

  const rows = await env.DB.prepare(
    `SELECT id, request_type, title, status, requested_by, reviewed_by, approved_by, executed_by, audited_by, risk_level, created_at, updated_at
     FROM workflow_requests
     ORDER BY created_at DESC
     LIMIT 200`,
  ).all();
  return new Response(JSON.stringify({ ok: true, items: rows.results || [] }), { status: 200, headers: JSON_HEADERS });
}

export async function onRequestPost(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  if (!hasRole(user, "operator")) return forbiddenJson("operator");

  const body = await context.request.json();
  const requestType = String(body?.request_type || "change_request").trim();
  const title = String(body?.title || "").trim();
  const payload = body?.payload || {};
  const riskLevel = String(body?.risk_level || "medium").toLowerCase();
  if (!title) {
    return new Response(JSON.stringify({ ok: false, error: "title_required" }), { status: 400, headers: JSON_HEADERS });
  }
  const id = crypto.randomUUID();
  const evId = crypto.randomUUID();
  const now = nowIso();
  await env.DB.prepare(
    `INSERT INTO workflow_requests (
      id, request_type, title, payload_json, status, requested_by, risk_level, created_at, updated_at
    ) VALUES (?1, ?2, ?3, ?4, 'requested', ?5, ?6, ?7, ?7)`,
  )
    .bind(id, requestType, title, JSON.stringify(payload), user.id, riskLevel, now)
    .run();
  await env.DB.prepare(
    `INSERT INTO workflow_events (id, request_id, event_type, actor_id, note, created_at)
     VALUES (?1, ?2, 'requested', ?3, ?4, ?5)`,
  )
    .bind(evId, id, user.id, "initial request", now)
    .run();
  return new Response(JSON.stringify({ ok: true, id }), { status: 201, headers: JSON_HEADERS });
}
