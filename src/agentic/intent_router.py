"""Natural language intent routing for specialized AI agents."""

from __future__ import annotations

import json
from typing import Any, Dict
from src.agentic.llm_router import LLMRouter


class IntentRouter:
    """
    Routes user queries to the appropriate specialized agent.
    Similar to the 'Auto-Routing' feature described in the Anthropics harness.
    """

    def __init__(self, router: LLMRouter = None):
        self.router = router or LLMRouter()
        self.available_agents = {
            "market_analyst": "Analyzes price drops, market trends, volatility, and news.",
            "risk_officer": "Modifies risk parameters, evaluates PnL drops, handles kill-switches.",
            "compliance_officer": "Checks operational limits, regulatory gates, and waivers.",
            "devops_healer": "Investigates system crashes, latency issues, and restarts pipelines."
        }

    def route_query(self, user_query: str) -> Dict[str, Any]:
        """
        Determines which agent should handle the query.
        """
        agents_desc = "\n".join([f"- {k}: {v}" for k, v in self.available_agents.items()])
        
        prompt = f"""
You are the AutonomousCompanyMVP AI Dispatcher.
Your job is to route the user's natural language query to the correct specialized agent.

[AVAILABLE AGENTS]
{agents_desc}

[USER QUERY]
"{user_query}"

Output ONLY a JSON object matching this schema:
{{
    "selected_agent": "one of the keys from AVAILABLE AGENTS, or 'unknown'",
    "reason": "Why this agent was chosen",
    "extracted_keywords": ["list", "of", "important", "entities", "or", "metrics"]
}}
"""
        try:
            # Prefer a fast, cheap model for routing
            text = self.router.generate_content(prompt, temperature=0.1, preferred_provider="openai")
            
            if not text:
                return {"selected_agent": "unknown", "reason": "LLM failed to respond."}

            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            return {"selected_agent": "unknown", "reason": f"Error during routing: {e}"}

