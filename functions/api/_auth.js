import { nowIso } from "./_shared.js";
import { ensureSchema } from "./_db.js";

const ROLE_WEIGHT = {
  viewer: 10,
  auditor: 20,
  operator: 30,
  admin: 40,
};

function parseCookies(request) {
  const raw = request.headers.get("cookie") || "";
  const out = {};
  for (const part of raw.split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (!k) continue;
    out[k] = decodeURIComponent(rest.join("=") || "");
  }
  return out;
}

function createSessionCookie(id, ttlSeconds = 60 * 60 * 8) {
  return `acmvp_session=${encodeURIComponent(id)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${ttlSeconds}`;
}

function clearSessionCookie() {
  return "acmvp_session=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0";
}

async function getCurrentUser(context) {
  const env = context.env || {};
  
  // --- Supabase Integration ---
  if (env.SUPABASE_URL && env.SUPABASE_ANON_KEY) {
    const cookies = parseCookies(context.request);
    const sid = String(cookies.acmvp_session || "").trim();
    // In a real app, we might use the access_token from localStorage or a different cookie.
    // For now, let's assume we want to check if the session exists in Supabase.
    // However, without the JWT in the cookie, we can't easily verify with Supabase.
    // If the user is logged in via Supabase, we should ideally have stored the JWT.
  }
  // --- End Supabase Integration ---

  if (!env.DB) return null;
  await ensureSchema(env);
  const cookies = parseCookies(context.request);
  const sid = String(cookies.acmvp_session || "").trim();
  if (!sid) return null;
  const rec = await env.DB.prepare(
    `SELECT s.id as session_id, s.expires_at, u.id, u.email, u.role, u.mfa_enabled
     FROM sessions s
     JOIN users u ON s.user_id = u.id
     WHERE s.id = ?1`,
  )
    .bind(sid)
    .first();
  if (!rec) return null;
  if (new Date(rec.expires_at).getTime() < Date.now()) {
    await env.DB.prepare(`DELETE FROM sessions WHERE id = ?1`).bind(sid).run();
    return null;
  }
  await env.DB.prepare(`UPDATE sessions SET last_seen_at = ?2 WHERE id = ?1`).bind(sid, nowIso()).run();
  return {
    id: rec.id,
    email: rec.email,
    role: rec.role,
    mfa_enabled: Boolean(rec.mfa_enabled),
    session_id: rec.session_id,
  };
}

function hasRole(user, requiredRole) {
  const a = ROLE_WEIGHT[String(user?.role || "viewer")] || 0;
  const b = ROLE_WEIGHT[String(requiredRole || "viewer")] || 0;
  return a >= b;
}

function unauthorizedJson() {
  return new Response(JSON.stringify({ ok: false, error: "unauthorized" }), {
    status: 401,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function forbiddenJson(requiredRole = "operator") {
  return new Response(JSON.stringify({ ok: false, error: "forbidden", required_role: requiredRole }), {
    status: 403,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export {
  clearSessionCookie,
  createSessionCookie,
  forbiddenJson,
  getCurrentUser,
  hasRole,
  parseCookies,
  unauthorizedJson,
};
