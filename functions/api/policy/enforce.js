import { getCurrentUser, unauthorizedJson } from "../_auth.js";
import { ensureSchema } from "../_db.js";
import { JSON_HEADERS, nowIso } from "../_shared.js";

function decide(user, action, resource, riskLevel) {
  const role = String(user?.role || "viewer");
  const risk = String(riskLevel || "medium").toLowerCase();
  if (role === "admin") return { allowed: true, reason: "admin_override" };
  if (action === "workflow.execute" && role !== "operator") return { allowed: false, reason: "operator_required" };
  if (risk === "high" && role !== "admin") return { allowed: false, reason: "high_risk_admin_required" };
  if (action.startsWith("policy.") && role !== "admin") return { allowed: false, reason: "policy_admin_required" };
  if (resource.startsWith("secrets/") && role !== "admin") return { allowed: false, reason: "secret_admin_required" };
  return { allowed: role !== "viewer", reason: role === "viewer" ? "viewer_read_only" : "policy_ok" };
}

export async function onRequestPost(context) {
  const env = context.env || {};
  if (!env.DB) return new Response(JSON.stringify({ ok: false, error: "d1_not_bound" }), { status: 500, headers: JSON_HEADERS });
  await ensureSchema(env);
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();

  const body = await context.request.json();
  const action = String(body?.action || "").trim();
  const resource = String(body?.resource || "").trim();
  const riskLevel = String(body?.risk_level || "medium").trim();
  if (!action || !resource) {
    return new Response(JSON.stringify({ ok: false, error: "action_resource_required" }), { status: 400, headers: JSON_HEADERS });
  }
  const d = decide(user, action, resource, riskLevel);
  const now = nowIso();
  await env.DB.prepare(
    `INSERT INTO policy_decisions (id, actor_id, action, resource, allowed, reason, created_at)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)`,
  )
    .bind(crypto.randomUUID(), user.id, action, resource, d.allowed ? 1 : 0, d.reason, now)
    .run();
  return new Response(
    JSON.stringify({
      ok: true,
      decision: {
        allowed: d.allowed,
        reason: d.reason,
        actor_id: user.id,
        action,
        resource,
        risk_level: riskLevel,
        created_at_utc: now,
      },
    }),
    { status: 200, headers: JSON_HEADERS },
  );
}
