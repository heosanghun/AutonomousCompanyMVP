export async function onRequestGet() {
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
  ].join("\n");
  return new Response(body, {
    status: 200,
    headers: { "content-type": "text/plain; charset=utf-8" },
  });
}
