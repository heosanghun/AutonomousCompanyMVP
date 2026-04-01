import json
import time
from typing import Dict, Any, List
from pathlib import Path
from src.agentic.llm_router import LLMRouter
from src.agentic.skill_manager import SkillManager

class GeneratorAgent:
    """
    수립된 계획에 따라 작업을 수행하고 결과물(Artifact)을 생성하는 실행 에이전트.
    """
    def __init__(self, router: LLMRouter = None, skill_manager: SkillManager = None):
        self.router = router or LLMRouter()
        self.skill_manager = skill_manager or SkillManager()

    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        주어진 단계(Task)를 수행합니다. 스킬이 정의되어 있다면 실제 호출을 시도합니다.
        """
        step_id = step.get("step_id", "Unknown")
        task = step.get("task", "")
        required_skills = step.get("required_skills", [])
        
        print(f"[Generator] Executing Step {step_id}: {task}")
        
        # 1. 필요 시 스킬 호출 로직 (예: RSI 계산, 파일 읽기 등)
        skill_results = []
        for skill_name in required_skills:
            try:
                # SkillManager를 통해 실제 스킬 실행
                result = self.skill_manager.execute_skill(skill_name, context or {})
                skill_results.append({skill_name: result})
                print(f"✅ Skill {skill_name} executed successfully.")
            except Exception as e:
                skill_results.append({skill_name: f"Error: {str(e)}"})
                print(f"❌ Skill {skill_name} failed: {e}")

        # 2. 작업 완료를 위한 LLM 분석 (생성 결과물 정제)
        system_prompt = f"""
당신은 'Autonomous Company'의 최고 기술 책임자(CTO)이자 빌더(Generator)입니다.
주어진 작업을 수행하고 그 결과물(Artifact)을 생성하십시오.

작업: {task}
스킬 실행 결과: {json.dumps(skill_results, indent=2, ensure_ascii=False)}

# 지침:
1. '증거 없는 완료'는 허용되지 않습니다. 데이터나 구체적인 수치를 제시하십시오.
2. 작업 결과를 요약하고, 다음 단계를 위해 필요한 데이터를 명확히 하십시오.
3. 작업 수행 중 발견된 예외 상황을 기록하십시오.

# 응답 형식 (JSON):
{{
  "step_id": {step_id},
  "status": "Completed/Failed/In-Progress",
  "result_summary": "수행 결과 요약",
  "artifacts": {{ "key": "value" }},
  "technical_notes": "특이 사항"
}}
"""
        response = self.router.generate(
            system_prompt=system_prompt,
            user_prompt=f"컨텍스트: {json.dumps(context or {})}",
            model_hint="sonnet" # 실행은 효율적인 모델 권장
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
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except: pass
            return {
                "step_id": step_id,
                "status": "Completed (Unstructured)",
                "result_summary": response[:200],
                "artifacts": {"raw_response": response}
            }
