"""AI Cross-Verify Policy Implementation.

Reduces single-model hallucination/bias by evaluating high-risk decisions
across multiple simulated personas to find consensus, conflicts, and confidence.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Any

from src.bootstrap_env import load_dotenv_files


def cross_verify_decision(
    proposal: dict[str, Any],
    review_scope: str = "high_risk_policy_change",
    mask_sensitive: bool = True,
) -> dict[str, Any]:
    """Runs a cross-verification over a proposed decision using different personas."""
    load_dotenv_files()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    # Masking sensitive info
    safe_proposal = dict(proposal)
    if mask_sensitive:
        for k in ["api_key", "secret", "credentials", "password"]:
            if k in safe_proposal:
                safe_proposal[k] = "***MASKED***"

    prompt = f"""
You are the AutonomousCompanyMVP Cross-Verification Engine.
You must evaluate the following proposed change using three distinct internal personas:
1. CRO-Agent (Chief Risk Officer): Focuses entirely on downside protection, limits, and compliance.
2. COO-Agent (Chief Operating Officer): Focuses on stability, latency, system reliability, and rollout safety.
3. Revenue-Agent (Quant/Trader): Focuses on expected yield, alpha capture, and execution efficiency.

Proposed Change/Decision:
{json.dumps(safe_proposal, indent=2, ensure_ascii=False)}

Scope: {review_scope}

Analyze the proposal from each perspective, then synthesize the results into a final JSON output.
Your output MUST be ONLY valid JSON matching this schema:
{{
  "consensus": "string describing what all 3 personas agree on",
  "conflicts": ["list of strings detailing disagreements between personas"],
  "unique_insights": ["list of unique points raised by specific personas"],
  "final_decision": "approved|rejected|needs_revision",
  "confidence_score": 0.0 to 1.0 (float),
  "review_scope": "{review_scope}",
  "review_time_utc": "ISO timestamp (e.g. 2026-03-27T12:00:00Z)"
}}
"""
    if not key:
        return _fallback_cross_verify(review_scope)

    payload = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
    ).encode("utf-8")

    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
    
    for m in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
        req = urllib.request.Request(
            url, data=payload, method="POST", headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                data = json.loads(r.read().decode("utf-8"))
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = (parts[0].get("text", "") if parts else "").strip()
            
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text.strip())
        except urllib.error.HTTPError:
            continue
        except Exception as e:
            print(f"Cross-verify LLM call failed for {m}: {e}")
            continue

    return _fallback_cross_verify(review_scope)


def _fallback_cross_verify(review_scope: str) -> dict[str, Any]:
    from src.execution.models import utc_now_iso
    return {
        "consensus": "Fallback: unable to run full cross-verification due to LLM failure or missing key.",
        "conflicts": ["LLM API unavailable"],
        "unique_insights": [],
        "final_decision": "needs_revision",
        "confidence_score": 0.0,
        "review_scope": review_scope,
        "review_time_utc": utc_now_iso()
    }
