import json
from typing import Dict, Any, List
from pathlib import Path
from src.agentic.llm_router import LLMRouter
from src.agentic.skill_manager import SkillManager

class PlannerAgent:
    """
    사용자의 요청을 분석하여 구체적인 실행 계획(Step-by-Step)을 수립하는 기획자 에이전트.
    """
    def __init__(self, router: LLMRouter = None, skill_manager: SkillManager = None):
        self.router = router or LLMRouter()
        self.skill_manager = skill_manager or SkillManager()
        self.soul_path = Path("configs/SOUL.md")
        self.soul_content = self._load_soul()

    def _load_soul(self) -> str:
        if self.soul_path.exists():
            return self.soul_path.read_text(encoding="utf-8")
        return "No SOUL defined."

    def create_plan(self, user_request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        skills_info = json.dumps(self.skill_manager.get_tool_definitions(), indent=2, ensure_ascii=False)
        
        system_prompt = f"""
당신은 'Autonomous Company'의 최고 전략 책임자(CSO)이자 수석 플래너입니다.
당신의 임무는 사용자의 모호한 요청을 아래의 [COMPANY SOUL] 원칙에 기반하여 '실행 가능한 단계별 계획'으로 변환하는 것입니다.

[COMPANY SOUL]
{self.soul_content}

사용 가능한 도구(SKILLS):
{skills_info}

# 계획 수립 원칙:
1. 모든 계획은 '최소 단위 작업(Sprint Contract)'으로 나누어야 합니다.
2. 각 단계는 구체적인 목표와 예상 결과물(Artifact)을 가져야 합니다.
3. 리스크가 높은 작업은 반드시 '검증(Evaluator)' 단계를 포함해야 합니다.
4. 불확실성이 큰 경우, 리서치(Research) 단계를 먼저 배치하십시오.

# 응답 형식 (JSON):
{{
  "request_analysis": "요청에 대한 심층 분석",
  "priority": "High/Medium/Low",
  "steps": [
    {{
      "step_id": 1,
      "task": "작업 내용",
      "required_skills": ["사용할 스킬명"],
      "expected_outcome": "결과물 정의"
    }}
  ],
  "potential_risks": ["예상되는 위험 요소"]
}}
"""
        user_prompt = f"사용자 요청: {user_request}\n현재 컨텍스트: {json.dumps(context or {})}"
        
        response = self.router.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_hint="opus" # 기획은 최고 성능 모델 권장
        )
        
        try:
            # Clean response for JSON parsing
            clean_res = response.strip()
            if "```json" in clean_res:
                clean_res = clean_res.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_res:
                clean_res = clean_res.split("```")[1].split("```")[0].strip()
                
            return json.loads(clean_res)
        except:
            # 폴백: JSON 추출 시도
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except: pass
            
            # 기본 계획 반환 (LLM이 형식을 못 맞췄을 경우)
            return {
                "request_analysis": "Parsing failed, using fallback plan",
                "steps": [{"step_id": 1, "task": user_request, "required_skills": [], "expected_outcome": "Outcome defined by request"}]
            }
