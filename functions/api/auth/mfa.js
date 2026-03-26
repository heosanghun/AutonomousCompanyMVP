import { getCurrentUser, unauthorizedJson } from "../_auth.js";
import { ensureSchema } from "../_db.js";
import { generateBase32Secret, verifyTotp } from "../_crypto.js";
import { JSON_HEADERS } from "../_shared.js";

export async function onRequestPost(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();

  const body = await context.request.json();
  const action = String(body?.action || "begin").toLowerCase();
  if (action === "begin") {
    const secret = generateBase32Secret(32);
    await env.DB.prepare(`UPDATE users SET mfa_secret = ?2, mfa_enabled = 0 WHERE id = ?1`).bind(user.id, secret).run();
    const issuer = encodeURIComponent("AutonomousCompanyMVP");
    const account = encodeURIComponent(user.email || user.id);
    const uri = `otpauth://totp/${issuer}:${account}?secret=${secret}&issuer=${issuer}&algorithm=SHA1&digits=6&period=30`;
    return new Response(JSON.stringify({ ok: true, secret, otpauth_uri: uri }), { status: 200, headers: JSON_HEADERS });
  }
  if (action === "enable") {
    const code = String(body?.code || "").trim();
    const rec = await env.DB.prepare(`SELECT mfa_secret FROM users WHERE id = ?1`).bind(user.id).first();
    const secret = String(rec?.mfa_secret || "");
    if (!secret) return new Response(JSON.stringify({ ok: false, error: "mfa_secret_not_initialized" }), { status: 400, headers: JSON_HEADERS });
    const ok = await verifyTotp(secret, code);
    if (!ok) return new Response(JSON.stringify({ ok: false, error: "invalid_totp_code" }), { status: 400, headers: JSON_HEADERS });
    await env.DB.prepare(`UPDATE users SET mfa_enabled = 1 WHERE id = ?1`).bind(user.id).run();
    return new Response(JSON.stringify({ ok: true, mfa_enabled: true }), { status: 200, headers: JSON_HEADERS });
  }
  if (action === "disable") {
    await env.DB.prepare(`UPDATE users SET mfa_enabled = 0, mfa_secret = NULL WHERE id = ?1`).bind(user.id).run();
    return new Response(JSON.stringify({ ok: true, mfa_enabled: false }), { status: 200, headers: JSON_HEADERS });
  }
  return new Response(JSON.stringify({ ok: false, error: "invalid_action" }), { status: 400, headers: JSON_HEADERS });
}
