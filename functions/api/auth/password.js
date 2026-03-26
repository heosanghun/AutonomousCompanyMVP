import { getCurrentUser, unauthorizedJson } from "../_auth.js";
import { ensureSchema } from "../_db.js";
import { hashPassword, verifyPassword } from "../_crypto.js";
import { JSON_HEADERS, nowIso } from "../_shared.js";

export async function onRequestPost(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();

  const body = await context.request.json();
  const current = String(body?.current_password || "").trim();
  const next = String(body?.new_password || "").trim();
  if (!current || !next || next.length < 8) {
    return new Response(JSON.stringify({ ok: false, error: "password_policy_failed" }), { status: 400, headers: JSON_HEADERS });
  }
  const rec = await env.DB.prepare(`SELECT password_hash FROM users WHERE id = ?1`).bind(user.id).first();
  const ok = await verifyPassword(current, String(rec?.password_hash || ""), String(env.AUTH_PEPPER || ""));
  if (!ok) {
    return new Response(JSON.stringify({ ok: false, error: "invalid_current_password" }), { status: 401, headers: JSON_HEADERS });
  }
  const hashed = await hashPassword(next, String(env.AUTH_PEPPER || ""));
  await env.DB.prepare(`UPDATE users SET password_hash = ?2, updated_at = ?3 WHERE id = ?1`).bind(user.id, hashed, nowIso()).run();
  return new Response(JSON.stringify({ ok: true }), { status: 200, headers: JSON_HEADERS });
}
