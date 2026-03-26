import { ensureSchema } from "./api/_db.js";

export async function onRequestGet(context) {
  const env = context.env || {};
  let workflowPending = 0;
  let policyDenied = 0;
  let highSeverity = 0;
  let activeSessions = 0;
  if (env.DB) {
    await ensureSchema(env);
    const [a, b, c, d] = await Promise.all([
      env.DB.prepare(`SELECT COUNT(*) as c FROM workflow_requests WHERE status IN ('requested','in_review','approved')`).first(),
      env.DB.prepare(`SELECT COUNT(*) as c FROM policy_decisions WHERE allowed = 0`).first(),
      env.DB.prepare(`SELECT COUNT(*) as c FROM ops_events WHERE severity IN ('high','critical')`).first(),
      env.DB.prepare(`SELECT COUNT(*) as c FROM sessions`).first(),
    ]);
    workflowPending = Number(a?.c || 0);
    policyDenied = Number(b?.c || 0);
    highSeverity = Number(c?.c || 0);
    activeSessions = Number(d?.c || 0);
  }
  const body = [
    "# HELP acmvp_sharpe Sharpe ratio from cloud backend fallback.",
    "# TYPE acmvp_sharpe gauge",
    "acmvp_sharpe 0",
    "# HELP acmvp_mdd Maximum drawdown.",
    "# TYPE acmvp_mdd gauge",
    "acmvp_mdd 0",
    "# HELP acmvp_win_rate Win rate.",
    "# TYPE acmvp_win_rate gauge",
    "acmvp_win_rate 0",
    "# HELP acmvp_cum_return Cumulative return.",
    "# TYPE acmvp_cum_return gauge",
    "acmvp_cum_return 0",
    "# HELP acmvp_workflow_pending Pending workflow requests.",
    "# TYPE acmvp_workflow_pending gauge",
    `acmvp_workflow_pending ${workflowPending}`,
    "# HELP acmvp_policy_denied_total Total denied policy checks.",
    "# TYPE acmvp_policy_denied_total counter",
    `acmvp_policy_denied_total ${policyDenied}`,
    "# HELP acmvp_high_severity_events High severity ops events.",
    "# TYPE acmvp_high_severity_events gauge",
    `acmvp_high_severity_events ${highSeverity}`,
    "# HELP acmvp_active_sessions Active authenticated sessions.",
    "# TYPE acmvp_active_sessions gauge",
    `acmvp_active_sessions ${activeSessions}`,
  ].join("\n");
  return new Response(body, {
    status: 200,
    headers: { "content-type": "text/plain; charset=utf-8" },
  });
}
