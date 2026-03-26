import { getCurrentUser, unauthorizedJson } from "../_auth.js";
import { ensureSchema } from "../_db.js";
import { JSON_HEADERS, nowIso } from "../_shared.js";

export async function onRequestGet(context) {
  const env = context.env || {};
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();

  const checks = [];
  const scoreOf = (ok, weight) => (ok ? weight : 0);

  const hasD1 = Boolean(env.DB);
  checks.push({ id: "d1_binding", ok: hasD1, weight: 20, note: hasD1 ? "DB bound" : "DB binding missing" });

  const hasGemini = Boolean(String(env.GEMINI_API_KEY || "").trim());
  checks.push({ id: "gemini_secret", ok: hasGemini, weight: 10, note: hasGemini ? "GEMINI_API_KEY set" : "missing GEMINI_API_KEY" });

  const hasPepper = Boolean(String(env.AUTH_PEPPER || "").trim());
  checks.push({ id: "auth_pepper", ok: hasPepper, weight: 10, note: hasPepper ? "AUTH_PEPPER set" : "missing AUTH_PEPPER" });

  let wfPending = 0;
  let policyDenied = 0;
  let highEvents = 0;
  let users = 0;
  if (hasD1) {
    await ensureSchema(env);
    const [a, b, c, d] = await Promise.all([
      env.DB.prepare(`SELECT COUNT(*) as c FROM workflow_requests WHERE status IN ('requested','in_review','approved')`).first(),
      env.DB.prepare(`SELECT COUNT(*) as c FROM policy_decisions WHERE allowed = 0`).first(),
      env.DB.prepare(`SELECT COUNT(*) as c FROM ops_events WHERE severity IN ('high','critical')`).first(),
      env.DB.prepare(`SELECT COUNT(*) as c FROM users`).first(),
    ]);
    wfPending = Number(a?.c || 0);
    policyDenied = Number(b?.c || 0);
    highEvents = Number(c?.c || 0);
    users = Number(d?.c || 0);
  }

  checks.push({ id: "user_seeded", ok: users >= 2, weight: 10, note: `users=${users}` });
  checks.push({ id: "workflow_backlog", ok: wfPending <= 10, weight: 15, note: `pending=${wfPending}` });
  checks.push({ id: "policy_denied", ok: policyDenied <= 20, weight: 15, note: `denied=${policyDenied}` });
  checks.push({ id: "high_severity_events", ok: highEvents <= 5, weight: 20, note: `high=${highEvents}` });

  const max = checks.reduce((s, x) => s + x.weight, 0);
  const got = checks.reduce((s, x) => s + scoreOf(x.ok, x.weight), 0);
  const pct = max > 0 ? Math.round((got / max) * 100) : 0;
  const ok = pct >= 85;

  return new Response(
    JSON.stringify({
      ok: true,
      readiness_ok: ok,
      readiness_percent: pct,
      generated_at_utc: nowIso(),
      checks,
    }),
    { status: 200, headers: JSON_HEADERS },
  );
}
