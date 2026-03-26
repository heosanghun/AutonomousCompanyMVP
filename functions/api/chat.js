import { JSON_HEADERS, defaultStatusPayload, isOpsQuery, nowIso, stylePrompt } from "./_shared.js";
import { getCurrentUser } from "./_auth.js";
import { ensureSchema } from "./_db.js";

export async function onRequestPost(context) {
  try {
    const env = context.env || {};
    if (env.DB) await ensureSchema(env);
    const body = await context.request.json();
    const message = String(body?.message || "").trim();
    if (!message) {
      return new Response(JSON.stringify({ ok: false, error: "message_required" }), {
        status: 400,
        headers: JSON_HEADERS,
      });
    }

    const key = String(env.GEMINI_API_KEY || "").trim();
    if (!key) {
      return new Response(JSON.stringify({ ok: false, error: "missing_gemini_api_key" }), {
        status: 400,
        headers: JSON_HEADERS,
      });
    }

    const settings = typeof body?.settings === "object" && body.settings ? body.settings : {};
    const history = Array.isArray(body?.history) ? body.history : [];
    const routeMode = String(settings?.route_mode || "auto").toLowerCase();
    const route = routeMode === "ops" ? "ops" : routeMode === "general" ? "general" : isOpsQuery(message) ? "ops" : "general";
    const { toneRule, lengthRule } = stylePrompt(settings);
    const status = defaultStatusPayload();
    const model = String(env.GEMINI_MODEL || "gemini-2.5-flash").trim();
    const maxPromptChars = Math.max(1000, Number(env.LLM_MAX_PROMPT_CHARS || 12000));
    if (message.length > maxPromptChars) {
      return new Response(JSON.stringify({ ok: false, error: "prompt_too_long", max_prompt_chars: maxPromptChars }), {
        status: 400,
        headers: JSON_HEADERS,
      });
    }

    const sys = [
      "You are an ops assistant for an autonomous company dashboard.",
      "Answer in Korean.",
      `Style: ${toneRule}.`,
      `Length rule: ${lengthRule}`,
      route === "ops"
        ? "This is an operations-focused query. Use status JSON and propose practical prioritized actions."
        : "This is a general conversation query. Keep it natural and helpful.",
    ].join(" ");

    const contents = [{ role: "user", parts: [{ text: sys }] }];
    if (route === "ops") {
      contents.push({ role: "user", parts: [{ text: `Status JSON:\n${JSON.stringify(status)}` }] });
    }
    for (const item of history.slice(-16)) {
      const role = String(item?.role || "user").toLowerCase() === "assistant" ? "model" : "user";
      const text = String(item?.text || "").trim();
      if (text) contents.push({ role, parts: [{ text: text.slice(0, 2000) }] });
    }
    contents.push({ role: "user", parts: [{ text: message }] });

    const upstream = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`,
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ contents }),
      },
    );

    const raw = await upstream.text();
    if (!upstream.ok) {
      return new Response(JSON.stringify({ ok: false, error: `gemini_http_${upstream.status}`, detail: raw.slice(0, 400) }), {
        status: 400,
        headers: JSON_HEADERS,
      });
    }

    const data = JSON.parse(raw || "{}");
    const parts = data?.candidates?.[0]?.content?.parts || [];
    const reply = String(parts?.[0]?.text || "").trim();
    if (!reply) {
      return new Response(JSON.stringify({ ok: false, error: "empty_gemini_response" }), {
        status: 400,
        headers: JSON_HEADERS,
      });
    }

    if (env.DB) {
      const user = await getCurrentUser(context);
      await env.DB.prepare(
        `INSERT INTO chat_logs (id, user_id, route, model, prompt_chars, response_chars, created_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)`,
      )
        .bind(
          crypto.randomUUID(),
          user?.id || null,
          route,
          model,
          message.length + JSON.stringify(history).length,
          reply.length,
          nowIso(),
        )
        .run();
    }
    return new Response(JSON.stringify({ ok: true, reply, provider: "gemini", model, route, generated_at_utc: nowIso() }), {
      status: 200,
      headers: JSON_HEADERS,
    });
  } catch (e) {
    return new Response(
      JSON.stringify({ ok: false, error: "chat_handler_error", detail: String(e?.message || e).slice(0, 300) }),
      { status: 400, headers: JSON_HEADERS },
    );
  }
}
