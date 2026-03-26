import { forbiddenJson, getCurrentUser, hasRole, unauthorizedJson } from "../_auth.js";
import { ensureSchema } from "../_db.js";
import { JSON_HEADERS, nowIso } from "../_shared.js";

export async function onRequestGet(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  if (!hasRole(user, "admin")) return forbiddenJson("admin");
  const rows = await env.DB.prepare(`SELECT id, email, role, mfa_enabled, created_at, updated_at FROM users ORDER BY created_at DESC`).all();
  return new Response(JSON.stringify({ ok: true, items: rows.results || [] }), { status: 200, headers: JSON_HEADERS });
}

export async function onRequestPatch(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  if (!hasRole(user, "admin")) return forbiddenJson("admin");
  const body = await context.request.json();
  const id = String(body?.id || "").trim();
  const role = String(body?.role || "").trim().toLowerCase();
  const mfaEnabled = body?.mfa_enabled === true || body?.mfa_enabled === 1 ? 1 : 0;
  if (!id || !["viewer", "auditor", "operator", "admin"].includes(role)) {
    return new Response(JSON.stringify({ ok: false, error: "id_and_valid_role_required" }), { status: 400, headers: JSON_HEADERS });
  }
  await env.DB.prepare(`UPDATE users SET role = ?2, mfa_enabled = ?3, updated_at = ?4 WHERE id = ?1`)
    .bind(id, role, mfaEnabled, nowIso())
    .run();
  return new Response(JSON.stringify({ ok: true, id, role, mfa_enabled: Boolean(mfaEnabled) }), {
    status: 200,
    headers: JSON_HEADERS,
  });
}
