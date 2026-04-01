const CORS_HEADERS = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

const SYSTEM_PROMPT =
  "당신은 QJC-OS 자율 운영 시스템의 수석 AI 에이전트입니다. " +
  "사용자의 명령을 받아 분석하고, 무인회사(Autonomous Company)의 운영 원칙에 따라 최선의 판단을 내리세요. " +
  "항상 한국어로 답변하며, 구체적이고 실행 가능한 인사이트를 제공하세요.";

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

export async function onRequestPost(context) {
  try {
    const env = context.env || {};
    const apiKey = env.GEMINI_API_KEY;
    if (!apiKey) {
      return new Response(
        JSON.stringify({ ok: false, error: "GEMINI_API_KEY not configured in Cloudflare environment" }),
        { status: 500, headers: CORS_HEADERS }
      );
    }

    const body = await context.request.json();
    const mission = String(body?.mission || "").trim();
    if (!mission) {
      return new Response(
        JSON.stringify({ ok: false, error: "mission_required" }),
        { status: 400, headers: CORS_HEADERS }
      );
    }

    const model = "gemini-2.5-flash";
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;

    const geminiRes = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: SYSTEM_PROMPT }] },
        contents: [{ role: "user", parts: [{ text: mission }] }],
        generationConfig: { temperature: 0.4, maxOutputTokens: 2048 },
      }),
    });

    if (!geminiRes.ok) {
      const errText = await geminiRes.text().catch(() => "");
      return new Response(
        JSON.stringify({ ok: false, error: `Gemini API error (${geminiRes.status})`, detail: errText.slice(0, 300) }),
        { status: geminiRes.status, headers: CORS_HEADERS }
      );
    }

    const data = await geminiRes.json();
    const aiReply = data?.candidates?.[0]?.content?.parts?.[0]?.text || "(응답 없음)";

    return new Response(
      JSON.stringify({
        ok: true,
        workflow_status: "Completed ☁ Serverless",
        ai_reply: aiReply,
        model,
      }),
      { status: 200, headers: CORS_HEADERS }
    );
  } catch (e) {
    return new Response(
      JSON.stringify({ ok: false, error: "mission_error", detail: String(e?.message || e).slice(0, 300) }),
      { status: 500, headers: CORS_HEADERS }
    );
  }
}
