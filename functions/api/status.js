import { JSON_HEADERS, defaultStatusPayload, nowIso } from "./_shared.js";

export async function onRequestGet() {
  const payload = defaultStatusPayload();
  payload.generated_at_utc = nowIso();
  return new Response(JSON.stringify(payload), { status: 200, headers: JSON_HEADERS });
}
