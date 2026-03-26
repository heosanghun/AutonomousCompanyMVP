import { forbiddenJson, getCurrentUser, hasRole, unauthorizedJson } from "../_auth.js";
import { ensureSchema } from "../_db.js";
import { JSON_HEADERS } from "../_shared.js";

export async function onRequestGet(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  if (!hasRole(user, "auditor")) return forbiddenJson("auditor");
  const limit = Math.max(10, Math.min(500, Number(new URL(context.request.url).searchParams.get("limit") || 100)));
  const rows = await env.DB.prepare(
    `SELECT id, event_type, severity, payload_json, created_at
     FROM ops_events
     ORDER BY created_at DESC
     LIMIT ?1`,
  )
    .bind(limit)
    .all();
  return new Response(JSON.stringify({ ok: true, items: rows.results || [] }), { status: 200, headers: JSON_HEADERS });
}
