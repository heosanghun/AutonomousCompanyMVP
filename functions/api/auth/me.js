import { JSON_HEADERS } from "../_shared.js";
import { getCurrentUser } from "../_auth.js";

export async function onRequestGet(context) {
  const user = await getCurrentUser(context);
  if (!user) {
    return new Response(JSON.stringify({ ok: true, authenticated: false, user: null }), {
      status: 200,
      headers: JSON_HEADERS,
    });
  }
  return new Response(JSON.stringify({ ok: true, authenticated: true, user }), {
    status: 200,
    headers: JSON_HEADERS,
  });
}
