"""Artifact Handoff and Context Compression for Long-Running Agents.

As outlined in Anthropic's harness design, long-running processes suffer from
"Context Anxiety" and token limits. This module solves that by frequently
summarizing recent state and resetting the LLM session using a clean,
structured artifact.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from src.agentic.llm_router import LLMRouter


class ContextHandoffManager:
    """
    Manages the transition of knowledge between isolated trading sessions.
    Writes and reads a JSON artifact to prevent infinite context accumulation.
    """
    
    ARTIFACT_PATH = Path("outputs/worker/session_artifact.json")

    def __init__(self, router: LLMRouter = None):
        self.router = router or LLMRouter()
        self.ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)

    def load_previous_artifact(self) -> Dict[str, Any]:
        """Loads the compressed context from the previous session."""
        if not self.ARTIFACT_PATH.exists():
            return {
                "session_id": "initial",
                "summary": "No previous history. Starting fresh.",
                "lessons_learned": [],
                "warnings": []
            }
        try:
            return json.loads(self.ARTIFACT_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {"error": "Failed to load artifact."}

    def generate_and_save_handoff(
        self,
        session_id: str,
        raw_logs: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Takes massive raw logs and compresses them into a clean JSON artifact
        using the LLM.
        """
        prompt = f"""
You are the Handoff Architect for a long-running autonomous trading system.
A 12-hour session just completed. To avoid context limit issues, you must
summarize the raw events into a clean, structured artifact for the NEXT agent
that wakes up.

[SESSION METRICS]
{json.dumps(metrics, indent=2)}

[RAW LOG SNIPPETS]
{raw_logs[-3000:]}  # Taking last 3000 chars

Focus heavily on "lessons learned" and "warnings" for the next agent.
Output ONLY a JSON object matching this schema:
{{
    "session_id": "{session_id}",
    "summary": "Brief 2-3 sentence overview of the market conditions and system performance.",
    "lessons_learned": ["list of what worked or didn't work"],
    "warnings": ["list of critical issues the next agent must watch out for"]
}}
"""
        try:
            text = self.router.generate_content(prompt, temperature=0.1, preferred_provider="gemini")
            if text:
                if text.startswith("```json"): text = text[7:]
                if text.endswith("```"): text = text[:-3]
                
                artifact = json.loads(text.strip())
                
                # Save physical artifact
                self.ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
                
                return artifact
        except Exception as e:
            print(f"Failed to generate handoff artifact: {e}")
            
        # Fallback
        fallback = {
            "session_id": session_id,
            "summary": "Fallback summary due to LLM error. Check raw logs.",
            "lessons_learned": ["Always check logs"],
            "warnings": ["Handoff compression failed"]
        }
        self.ARTIFACT_PATH.write_text(json.dumps(fallback, indent=2), encoding="utf-8")
        return fallback
