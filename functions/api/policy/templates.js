import { forbiddenJson, getCurrentUser, hasRole, unauthorizedJson } from "../_auth.js";
import { JSON_HEADERS } from "../_shared.js";

const TEMPLATES = [
  {
    id: "trade-high-risk",
    title: "High-Risk Trade Approval",
    required_checks: [
      "workflow_approved",
      "policy_enforced",
      "risk_limit_ok",
      "human_signoff",
    ],
    required_role: "admin",
  },
  {
    id: "ops-change-medium",
    title: "Medium-Risk Ops Change",
    required_checks: [
      "workflow_in_review_or_approved",
      "policy_enforced",
      "rollback_plan_present",
    ],
    required_role: "auditor",
  },
  {
    id: "data-pipeline-deploy",
    title: "Data Pipeline Deployment",
    required_checks: [
      "schema_compatible",
      "reconcile_ok",
      "drift_guard_ok",
      "mlops_pipeline_ok",
    ],
    required_role: "operator",
  },
];

function evalTemplate(template, checks) {
  const missing = template.required_checks.filter((k) => !checks.includes(k));
  return {
    ok: missing.length === 0,
    missing,
    passed: template.required_checks.filter((k) => checks.includes(k)),
  };
}

export async function onRequestGet(context) {
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  if (!hasRole(user, "viewer")) return forbiddenJson("viewer");
  return new Response(JSON.stringify({ ok: true, templates: TEMPLATES }), { status: 200, headers: JSON_HEADERS });
}

export async function onRequestPost(context) {
  const user = await getCurrentUser(context);
  if (!user) return unauthorizedJson();
  const body = await context.request.json();
  const id = String(body?.template_id || "").trim();
  const checks = Array.isArray(body?.checks) ? body.checks.map((x) => String(x)) : [];
  const template = TEMPLATES.find((t) => t.id === id);
  if (!template) return new Response(JSON.stringify({ ok: false, error: "template_not_found" }), { status: 404, headers: JSON_HEADERS });
  if (!hasRole(user, template.required_role)) return forbiddenJson(template.required_role);
  const result = evalTemplate(template, checks);
  return new Response(
    JSON.stringify({
      ok: true,
      template_id: id,
      required_role: template.required_role,
      user_role: user.role,
      evaluation: result,
    }),
    { status: 200, headers: JSON_HEADERS },
  );
}
