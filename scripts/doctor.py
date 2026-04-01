import os
import sys
import json
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from src.agentic.skill_manager import SkillManager
from src.agentic.llm_router import LLMRouter

def check_status():
    print("🦞 [Autonomous Company Doctor] 자가 진단을 시작합니다...\n")
    issues = []
    
    # 1. 환경 설정 점검
    print("[1/4] 환경 변수 및 설정 점검 중...")
    required_envs = ["GEMINI_API_KEY", "OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN"]
    for env in required_envs:
        if not os.getenv(env):
            issues.append(f"❌ 환경 변수 누락: {env}")
        else:
            print(f"  ✅ {env} 로드됨")
            
    if not os.path.exists(".env"):
        issues.append("⚠️ .env 파일이 없습니다. 환경 변수가 시스템에 이미 설정되어 있어야 합니다.")

    # 2. 기업 헌법 및 보안 가드레일 점검
    print("\n[2/4] 보안 및 가드레일 점검 중...")
    soul_path = Path("configs/SOUL.md")
    if not soul_path.exists():
        issues.append("❌ configs/SOUL.md 파일이 없습니다. 에이전트의 판단 기준이 상실되었습니다.")
    else:
        print(f"  ✅ SOUL.md 탐지됨 (크기: {soul_path.stat().st_size} bytes)")

    # 3. 모듈형 스킬 로딩 점검
    print("\n[3/4] 스킬 매니저 및 도구 로딩 점검 중...")
    try:
        sm = SkillManager()
        tools = sm.get_tool_definitions()
        if not tools:
            issues.append("⚠️ 로드된 스킬이 없습니다. skills/ 폴더를 확인하세요.")
        else:
            print(f"  ✅ {len(tools)}개의 스킬이 정상적으로 로드되었습니다.")
            for t in tools:
                print(f"    - {t['name']}")
    except Exception as e:
        issues.append(f"❌ 스킬 매니저 초기화 실패: {str(e)}")

    # 4. AI 라우팅 및 모델 연결성 점검
    print("\n[4/4] AI 라우팅 및 모델 연결성 점검 중...")
    try:
        router = LLMRouter()
        # 실제 호출은 비용이 발생하므로 모델 구성 정보만 출력
        print("  ✅ LLMRouter 초기화 완료 (Gemini, OpenAI 지원)")
    except Exception as e:
        issues.append(f"❌ LLM 라우터 설정 오류: {str(e)}")

    # 최종 결과 보고
    print("\n" + "="*60)
    if not issues:
        print("🎉 [건강함] 모든 시스템 진단 항목이 통과되었습니다!")
    else:
        print(f"⚠️ 총 {len(issues)}개의 잠재적 이슈가 발견되었습니다:")
        for issue in issues:
            print(f"  {issue}")
    print("="*60 + "\n")

if __name__ == "__main__":
    check_status()
