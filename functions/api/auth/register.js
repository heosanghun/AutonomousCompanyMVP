import { JSON_HEADERS, nowIso } from "../_shared.js";
import { hashPassword } from "../_crypto.js";
import { ensureSchema } from "../_db.js";

export async function onRequestPost(context) {
  try {
    const env = context.env || {};
    const body = await context.request.json();
    const email = String(body?.email || "").trim().toLowerCase();
    const password = String(body?.password || "").trim();
    
    if (!email || !password || password.length < 8) {
      return new Response(JSON.stringify({ ok: false, error: "email_and_valid_password_required" }), { status: 400, headers: JSON_HEADERS });
    }

    // --- Supabase Integration ---
    if (env.SUPABASE_URL && env.SUPABASE_ANON_KEY) {
      const res = await fetch(`${env.SUPABASE_URL}/auth/v1/signup`, {
        method: "POST",
        headers: {
          "apikey": env.SUPABASE_ANON_KEY,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (!res.ok) {
        return new Response(JSON.stringify({ 
          ok: false, 
          error: "supabase_signup_failed", 
          detail: data.msg || data.message || data.error_description || data.error || JSON.stringify(data)
        }), { status: res.status, headers: JSON_HEADERS });
      }
      return new Response(JSON.stringify({ ok: true, user: data.user }), { status: 201, headers: JSON_HEADERS });
    }
    // --- End Supabase Integration ---
    
    if (!env.DB) {
      return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
    }
    await ensureSchema(env);
    
    // Check if user already exists
    const existing = await env.DB.prepare(`SELECT id FROM users WHERE lower(email) = ?1`)
      .bind(email)
      .first();
      
    if (existing) {
      return new Response(JSON.stringify({ ok: false, error: "user_already_exists" }), { status: 409, headers: JSON_HEADERS });
    }
    
    const id = crypto.randomUUID();
    const passwordHash = await hashPassword(password, String(env.AUTH_PEPPER || ""));
    const now = nowIso();
    
    await env.DB.prepare(
      `INSERT INTO users (id, email, password_hash, role, mfa_enabled, created_at, updated_at)
       VALUES (?1, ?2, ?3, 'viewer', 0, ?4, ?4)`
    )
    .bind(id, email, passwordHash, now)
    .run();
    
    return new Response(
      JSON.stringify({
        ok: true,
        message: "user_registered",
        user_id: id
      }),
      { status: 201, headers: JSON_HEADERS }
    );
    
  } catch (e) {
    return new Response(JSON.stringify({ ok: false, error: "registration_error", detail: String(e?.message || e).slice(0, 300) }), {
      status: 400,
      headers: JSON_HEADERS,
    });
  }
}
