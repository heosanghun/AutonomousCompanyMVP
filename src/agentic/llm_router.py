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

    def generate(self, system_prompt: str, user_prompt: str, model_hint: str = "sonnet", temperature: float = 0.2) -> str:
        """
        에이전트가 사용하는 표준 생성 메서드.
        system_prompt와 user_prompt를 결합하여 최적의 모델로 전달합니다.
        """
        full_prompt = f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}"
        
        # model_hint에 따른 선호 제공자 설정
        preferred = "gemini"
        if "opus" in model_hint.lower() or "sonnet" in model_hint.lower():
            preferred = "anthropic"
        elif "gpt" in model_hint.lower():
            preferred = "openai"
            
        return self.generate_content(full_prompt, temperature, preferred_provider=preferred) or "Error: No response from LLM."

    def generate_content(self, prompt: str, temperature: float = 0.2, preferred_provider: str = "gemini", system_instruction: str = None) -> Optional[str]:
        """Tries preferred provider first, falls back to others if it fails."""
        if system_instruction:
            prompt = f"[SYSTEM]\n{system_instruction}\n\n[USER]\n{prompt}"
            
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
