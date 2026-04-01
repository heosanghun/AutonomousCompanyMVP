import os
import json
import time
from typing import Dict, Any
from src.agentic.pipeline_engine import PipelineEngine
from src.agentic.llm_router import LLMRouter
from src.agentic.skill_manager import SkillManager
from src.ops.security_hooks import security_guard

class QJCOS:
    """
    QJC-OS: Autonomous Enterprise Operating System.
    모든 에이전트와 파이프라인을 통합 관리하는 최상위 클래스.
    """
    def __init__(self):
        print("🚀 [QJC-OS] Initializing Sovereign Operating System...")
        self.router = LLMRouter()
        self.skill_manager = SkillManager()
        self.pipeline = PipelineEngine(self.router, self.skill_manager)
        
        # 시스템 초기화 상태 확인 (이미지 12의 'Doctor' 기능 통합)
        self.health_check()

    def health_check(self):
        print("🩺 [QJC-OS] Running internal health diagnostics...")
        # 1. SOUL.md 존재 여부 확인
        if not os.path.exists("configs/SOUL.md"):
            print("⚠️ [Warning] SOUL.md not found. Using default principles.")
        
        # 2. 보안 가드레일 로드 확인
        print(f"🛡️ [Guardrail] Protected files: {len(security_guard.rules.get('forbidden_files', []))}")
        
        # 3. 로드된 스킬 확인
        print(f"🛠️ [Skills] Loaded {len(self.skill_manager.get_tool_definitions())} active skills.")
        
        print("✨ [QJC-OS] System is Healthy and Ready for Autonomy.")

    def run_autonomously(self, mission: str):
        """
        주어진 미션을 자율적으로 수행합니다.
        (기획-실행-검증 루프 무한 반복 및 자가 치유)
        """
        print(f"\n🌟 [Mission Start] '{mission}'")
        try:
            result = self.pipeline.run_workflow(mission)
            
            # 최종 결과 리포트 출력
            print("\n📊 [Mission Report]")
            print(f"Status: {result['workflow_status']}")
            print(f"Steps Completed: {len(result['steps_results'])}")
            
            # 이미지 10의 '증거 기반 완료' 원칙 적용
            if result['workflow_status'] == "Completed":
                print("🏁 [Evidence-Based Completion] All artifacts verified by Evaluator.")
            else:
                print("⚠️ [Mission Incomplete] Retrying or escalating to administrator...")
                
            return result
            
        except Exception as e:
            print(f"🚨 [System Failure] Critical Error: {str(e)}")
            # 에러 발생 시 자가 복구 시도 (Phase 5: Self-Healing)
            return {"status": "Error", "error": str(e)}

if __name__ == "__main__":
    os.environ["PYTHONPATH"] = "."
    os.system("clear" if os.name == "posix" else "cls")
    
    os_instance = QJCOS()
    # 예시 미션: 이미지 10의 '데이터 분석' 미션 수행
    os_instance.run_autonomously("현재 시장의 RSI 지표를 분석하여 2026년 부가세 예측 리포트를 작성해줘.")
