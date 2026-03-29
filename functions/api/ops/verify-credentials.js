import { getCurrentUser, unauthorizedJson } from "../_auth.js";
import { JSON_HEADERS, nowIso } from "../_shared.js";

export async function onRequestPost(context) {
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();

  const body = await context.request.json();
  const venue = String(body?.venue || "").toLowerCase();
  const key = String(body?.key || "").trim();
  const secret = String(body?.secret || "").trim();

  if (!key || !secret) {
    return new Response(JSON.stringify({ ok: false, error: "missing_credentials" }), { status: 400, headers: JSON_HEADERS });
  }

  // In a real production system, this would perform a signed GET /account fetch.
  // For the MVP demonstration, we validate basic format or perform a mock check.
  let ok = false;
  let error = "";

  if (venue === "upbit") {
    // Upbit keys are usually 40 chars
    if (key.length >= 20 && secret.length >= 20) {
      ok = true;
    } else {
      error = "invalid_format_upbit";
    }
  } else if (venue === "binance") {
    // Binance keys are usually 64 chars
    if (key.length >= 32 && secret.length >= 32) {
      ok = true;
    } else {
      error = "invalid_format_binance";
    }
  } else {
    error = "unsupported_venue";
  }

  return new Response(
    JSON.stringify({
      ok,
      error,
      venue,
      timestamp_utc: nowIso(),
      note: ok ? "Credential format validated (mock connection success)" : "Validation failed",
    }),
    { status: 200, headers: JSON_HEADERS }
  );
}
