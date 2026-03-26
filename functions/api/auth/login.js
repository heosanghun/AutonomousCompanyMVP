import { JSON_HEADERS, nowIso } from "../_shared.js";
import { createSessionCookie } from "../_auth.js";
import { ensureSchema } from "../_db.js";
import { verifyPassword, verifyTotp } from "../_crypto.js";

export async function onRequestPost(context) {
  try {
    const env = context.env || {};
    if (!env.DB) {
      return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
    }
    await ensureSchema(env);
    const body = await context.request.json();
    const email = String(body?.email || body?.id || "").trim().toLowerCase();
    const password = String(body?.password || "").trim();
    const mfaCode = String(body?.mfa_code || "").trim();
    if (!email || !password) {
      return new Response(JSON.stringify({ ok: false, error: "email_password_required" }), { status: 400, headers: JSON_HEADERS });
    }
    const user = await env.DB.prepare(`SELECT id, email, password_hash, role, mfa_enabled, mfa_secret FROM users WHERE lower(email) = ?1`)
      .bind(email)
      .first();
    const pwOk = user ? await verifyPassword(password, String(user.password_hash || ""), String(env.AUTH_PEPPER || "")) : false;
    if (!user || !pwOk) {
      return new Response(JSON.stringify({ ok: false, error: "invalid_credentials" }), { status: 401, headers: JSON_HEADERS });
    }
    if (Number(user.mfa_enabled) === 1) {
      const secret = String(user.mfa_secret || "").trim();
      const mfaOk = secret ? await verifyTotp(secret, mfaCode) : mfaCode === "000000";
      if (!mfaOk) {
        return new Response(JSON.stringify({ ok: false, error: "mfa_required_or_invalid" }), { status: 401, headers: JSON_HEADERS });
      }
    }
    const sid = crypto.randomUUID();
    const now = nowIso();
    const exp = new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString();
    await env.DB.prepare(
      `INSERT INTO sessions (id, user_id, created_at, expires_at, last_seen_at, ip, user_agent)
       VALUES (?1, ?2, ?3, ?4, ?3, ?5, ?6)`,
    )
      .bind(
        sid,
        user.id,
        now,
        exp,
        context.request.headers.get("cf-connecting-ip") || "",
        context.request.headers.get("user-agent") || "",
      )
      .run();
    const headers = new Headers(JSON_HEADERS);
    headers.append("Set-Cookie", createSessionCookie(sid));
    return new Response(
      JSON.stringify({
        ok: true,
        user: { id: user.id, email: user.email, role: user.role, mfa_enabled: Boolean(user.mfa_enabled) },
      }),
      { status: 200, headers },
    );
  } catch (e) {
    return new Response(JSON.stringify({ ok: false, error: "login_error", detail: String(e?.message || e).slice(0, 300) }), {
      status: 400,
      headers: JSON_HEADERS,
    });
  }
}
