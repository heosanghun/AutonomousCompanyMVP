import { forbiddenJson, getCurrentUser, hasRole, unauthorizedJson } from "../_auth.js";
import { JSON_HEADERS } from "../_shared.js";

export async function onRequestGet(context) {
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  const required = new URL(context.request.url).searchParams.get("required") || "viewer";
  if (!hasRole(user, required)) return forbiddenJson(required);
  return new Response(JSON.stringify({ ok: true, user, required_role: required }), {
    status: 200,
    headers: JSON_HEADERS,
  });
}
