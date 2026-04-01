import json
import time
from typing import Dict, Any, List, Optional
from src.agentic.planner_agent import PlannerAgent
from src.agentic.generator_agent import GeneratorAgent
from src.agentic.evaluator_agent import EvaluatorAgent # 기존 에이전트 연동
from src.agentic.llm_router import LLMRouter
from src.agentic.skill_manager import SkillManager

import uuid
from datetime import datetime

class PipelineEngine:
    def __init__(self, router: Optional[LLMRouter] = None, skill_manager: Optional[SkillManager] = None):
        self.router = router or LLMRouter()
        self.skill_manager = skill_manager or SkillManager()
        
        self.planner = PlannerAgent(self.router, self.skill_manager)
        self.generator = GeneratorAgent(self.router, self.skill_manager)
        self.evaluator = EvaluatorAgent(self.router, self.skill_manager)
        
        self.current_session_artifacts: Dict[str, Any] = {}
        self.current_session_id: Optional[str] = None

    def run_workflow(self, request_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        사용자 요청에 대한 전체 자율 워크플로우 실행 및 DB 로깅.
        """
        self.current_session_id = str(uuid.uuid4())
        start_time = datetime.now().isoformat()
        
        # [Logging] 세션 시작 기록
        print(f"[PipelineEngine] New Session: {self.current_session_id}")
        print(f"[PipelineEngine] Request: '{request_text}'")
        
        # 1. Planning (기획)
        plan = self.planner.create_plan(request_text, context)
        steps = plan.get("steps", [])
        print(f"[PipelineEngine] Plan Created: {len(steps)} steps defined.")
        
        all_results = []
        success = False if not steps else True # 기본값 설정

        # 2. Execution & Evaluation (실행 및 검증 루프)
        for step in steps:
            step_id = step.get("step_id")
            step_success = False
            for attempt in range(1, 4):
                print(f"[PipelineEngine] Attempt {attempt} for Step {step_id}")
                
                # Execution (Generator)
                result = self.generator.execute_step(step, self.current_session_artifacts)
                
                # Evaluation (Evaluator)
                evaluation = self.evaluator.evaluate_trade(
                    proposal=result, 
                    portfolio_state=self.current_session_artifacts, 
                    market_context=context or {}
                )
                
                is_approved = evaluation.get("approved") is True or evaluation.get("decision") == "Approved"
                
                if is_approved:
                    print(f"[PipelineEngine] Step {step_id} APPROVED by Evaluator.")
                    step_success = True
                    # 결과물 업데이트 (Artifacts 누적)
                    self.current_session_artifacts.update(result.get("artifacts", {}))
                    all_results.append({
                        "step_id": step_id,
                        "status": "Success",
                        "result": result,
                        "evaluation": evaluation
                    })
                    break
                else:
                    print(f"[PipelineEngine] Step {step_id} REJECTED: {evaluation.get('reason')}")
                    # 피드백을 context에 추가하여 재수행
                    step["task"] += f"\n[Feedback from Evaluator]: {evaluation.get('reason')}"
            
            if not step_success:
                print(f"[PipelineEngine] Step {step_id} FAILED after 3 attempts.")
                success = False
                all_results.append({
                    "step_id": step_id,
                    "status": "Failed",
                    "reason": "Max attempts reached"
                })
                break # 파이프라인 중단

        return {
            "workflow_status": "Completed" if success else "Failed",
            "request_analysis": plan.get("request_analysis"),
            "steps_results": all_results,
            "final_artifacts": self.current_session_artifacts
        }

if __name__ == "__main__":
    # 간단한 자가 진단 테스트
    engine = PipelineEngine()
    test_result = engine.run_workflow("비트코인의 현재 RSI를 분석하고 과매수 상태인지 판단해줘")
    print(json.dumps(test_result, indent=2, ensure_ascii=False))
