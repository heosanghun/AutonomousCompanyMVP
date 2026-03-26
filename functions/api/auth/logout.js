import { clearSessionCookie, getCurrentUser, parseCookies } from "../_auth.js";
import { JSON_HEADERS } from "../_shared.js";

export async function onRequestPost(context) {
  const env = context.env || {};
  const cookies = parseCookies(context.request);
  const sid = String(cookies.acmvp_session || "").trim();
  if (sid && env.DB) {
    await env.DB.prepare(`DELETE FROM sessions WHERE id = ?1`).bind(sid).run();
  }
  await getCurrentUser(context); // touch schema init path safely
  const headers = new Headers(JSON_HEADERS);
  headers.append("Set-Cookie", clearSessionCookie());
  return new Response(JSON.stringify({ ok: true }), { status: 200, headers });
}
