import os
import importlib.util
import inspect
import json
from typing import List, Dict, Any, Callable
from pathlib import Path

class SkillManager:
    """
    OpenClaw 스타일의 모듈형 스킬 관리자.
    skills/ 디렉토리 내의 .py 파일들을 로드하여 AI 에이전트의 도구(Tools)로 제공합니다.
    """
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Callable] = {}
        self.tool_definitions: List[Dict[str, Any]] = []
        
        # 디렉토리가 없으면 생성
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True)
            
        self._load_skills()

    def _load_skills(self):
        """디렉토리를 스캔하여 스킬 모듈을 동적으로 로드합니다."""
        for root, _, files in os.walk(self.skills_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    path = Path(root) / file
                    # 스킬 이름 결정 (예: trading/rsi.py -> trading_rsi)
                    rel_path = path.relative_to(self.skills_dir)
                    skill_id = str(rel_path.with_suffix("")).replace(os.sep, "_")
                    self._register_skill(path, skill_id)

    def _register_skill(self, path: Path, skill_id: str):
        """단일 스킬 파일을 로드하고 툴 정의를 생성합니다."""
        try:
            spec = importlib.util.spec_from_file_location(skill_id, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 모듈 내 'run' 함수가 정의되어 있는지 확인
            if hasattr(module, "run") and callable(module.run):
                doc = inspect.getdoc(module.run) or f"Skill: {skill_id}"
                params = inspect.signature(module.run).parameters
                
                # AI용 Tool Definition 생성 (OpenAI/Gemini 호환)
                tool_def = {
                    "name": skill_id,
                    "description": doc,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }

                for p_name, p_obj in params.items():
                    p_type = "string" # 기본값
                    if p_obj.annotation == int: p_type = "integer"
                    elif p_obj.annotation == float: p_type = "number"
                    elif p_obj.annotation == bool: p_type = "boolean"
                    
                    tool_def["parameters"]["properties"][p_name] = {
                        "type": p_type,
                        "description": f"Parameter: {p_name}"
                    }
                    if p_obj.default == inspect.Parameter.empty:
                        tool_def["parameters"]["required"].append(p_name)

                self.skills[skill_id] = module.run
                self.tool_definitions.append(tool_def)
                print(f"✅ Skill loaded: {skill_id}")
        except Exception as e:
            print(f"❌ Failed to load skill {path}: {str(e)}")

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """AI 에이전트에게 전달할 툴 목록을 반환합니다."""
        return self.tool_definitions

    def execute_skill(self, skill_id: str, **kwargs) -> Any:
        """
        스킬을 실행하기 전에 보안 후크(Guardrail)를 검사합니다.
        AI 에이전트가 민감 정보에 접근하거나 위험한 명령을 내리는 것을 물리적으로 차단합니다.
        """
        from src.ops.security_hooks import security_guard
        
        # 보안 체크: 파일 접근 시도 검사 (path, file_path, filename 등의 인자 확인)
        for key in ["path", "file_path", "filename", "src", "dest"]:
            if key in kwargs:
                if not security_guard.check_file_access(str(kwargs[key])):
                    raise PermissionError(f"🚫 [Guardrail] Access to '{kwargs[key]}' is strictly forbidden by QJC-OS Policy.")

        # 보안 체크: 명령어 실행 시도 검사 (bash, shell, cmd 등의 인자 확인)
        for key in ["command", "cmd", "shell_script"]:
            if key in kwargs:
                if not security_guard.check_command_execution(str(kwargs[key])):
                    raise PermissionError(f"🚫 [Guardrail] Execution of command '{kwargs[key]}' is strictly forbidden by QJC-OS Policy.")

        if skill_id in self.skills:
            print(f"🛠️ [SkillManager] Executing skill: {skill_id}")
            result = self.skills[skill_id](**kwargs)
            
            # 결과물 유출 검사 (민감 정보 필터링)
            if isinstance(result, str) and not security_guard.check_content_leak(result):
                 print("⚠️ [Guardrail] Sensitive data detected in output. Redacting...")
                 return "[Security Warning]: Sensitive data detected and redacted by QJC-OS GuardrailHook."
                 
            return result
        raise ValueError(f"Skill '{skill_id}' not found.")

if __name__ == "__main__":
    # 간단한 테스트 실행
    manager = SkillManager()
    print(f"Loaded {len(manager.get_tool_definitions())} skills.")
