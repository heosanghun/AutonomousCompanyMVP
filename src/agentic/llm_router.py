"""Multi-LLM Routing and Fallback System."""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from typing import Any, Dict, Optional
from src.execution.models import utc_now_iso

class LLMRouter:
    """Routes LLM requests to different providers with fallback logic."""

    def __init__(self):
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    def generate_content(self, prompt: str, temperature: float = 0.2, preferred_provider: str = "gemini") -> Optional[str]:
        """Tries preferred provider first, falls back to others if it fails."""
        providers = [preferred_provider]
        for p in ["gemini", "openai", "anthropic"]:
            if p not in providers:
                providers.append(p)

        for provider in providers:
            try:
                if provider == "gemini" and self.gemini_key:
                    res = self._call_gemini(prompt, temperature)
                    if res: return res
                elif provider == "openai" and self.openai_key:
                    res = self._call_openai(prompt, temperature)
                    if res: return res
                elif provider == "anthropic" and self.anthropic_key:
                    res = self._call_anthropic(prompt, temperature)
                    if res: return res
            except Exception as e:
                print(f"[{provider.upper()}] Call failed: {e}")
                continue
        
        return None

    def _call_gemini(self, prompt: str, temperature: float) -> Optional[str]:
        payload = json.dumps(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature}
            }
        ).encode("utf-8")

        models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
        for m in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.gemini_key}"
            req = urllib.request.Request(
                url, data=payload, method="POST", headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=45) as r:
                    data = json.loads(r.read().decode("utf-8"))
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                return (parts[0].get("text", "") if parts else "").strip()
            except urllib.error.HTTPError:
                continue
        return None

    def _call_openai(self, prompt: str, temperature: float) -> Optional[str]:
        payload = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }).encode("utf-8")
        
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_key}"
            }
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

    def _call_anthropic(self, prompt: str, temperature: float) -> Optional[str]:
        payload = json.dumps({
            "model": "claude-3-haiku-20240307",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }).encode("utf-8")
        
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.anthropic_key,
                "anthropic-version": "2023-06-01"
            }
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data.get("content", [{}])[0].get("text", "").strip()
