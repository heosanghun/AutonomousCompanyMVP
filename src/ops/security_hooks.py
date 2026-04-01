import re
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

class GuardrailHook:
    """
    AI 에이전트의 액션을 모니터링하고 차단하는 보안 후크 시스템.
    이미지 10의 'salary-guard.sh'와 같은 보이지 않는 방어선 역할을 수행합니다.
    """
    def __init__(self, rules_path: str = "configs/rules/security.json"):
        self.rules_path = Path(rules_path)
        self.rules = self._load_rules()
        
    def _load_rules(self) -> Dict[str, Any]:
        if not self.rules_path.parent.exists():
            self.rules_path.parent.mkdir(parents=True)
            
        if not self.rules_path.exists():
            # 기본 보안 규칙 생성
            default_rules = {
                "forbidden_files": [
                    ".env", "secrets.json", "credentials.json", 
                    "*.pem", "*.key", "db/passwords.txt", 
                    "configs/auth_tokens.json"
                ],
                "forbidden_commands": [
                    "rm -rf /", "format", "mkfs", "shutdown", 
                    "reboot", "nmap", "ssh-keygen", "chmod 777"
                ],
                "sensitive_keywords": [
                    "password", "api_key", "secret_key", 
                    "salary", "user_identity", "private_key"
                ]
            }
            self.rules_path.write_text(json.dumps(default_rules, indent=2), encoding="utf-8")
            return default_rules
            
        return json.loads(self.rules_path.read_text(encoding="utf-8"))

    def check_file_access(self, file_path: str, mode: str = "read") -> bool:
        """
        파일 접근 권한을 확인합니다.
        """
        filename = os.path.basename(file_path)
        
        # 금지된 파일 패턴 검사
        for forbidden in self.rules.get("forbidden_files", []):
            if forbidden.startswith("*."):
                if filename.endswith(forbidden[1:]):
                    print(f"🚫 [Guardrail] Blocked {mode} access to {file_path} (Matches pattern {forbidden})")
                    return False
            elif forbidden in file_path:
                print(f"🚫 [Guardrail] Blocked {mode} access to {file_path} (Forbidden file)")
                return False
        
        return True

    def check_command_execution(self, command: str) -> bool:
        """
        쉘 명령어 실행 권한을 확인합니다.
        """
        for forbidden_cmd in self.rules.get("forbidden_commands", []):
            if forbidden_cmd in command:
                print(f"🚫 [Guardrail] Blocked execution of command: '{command}' (Contains forbidden pattern '{forbidden_cmd}')")
                return False
        
        return True

    def check_content_leak(self, content: str) -> bool:
        """
        출력 결과물에 민감 정보가 포함되어 있는지 검사합니다.
        """
        for keyword in self.rules.get("sensitive_keywords", []):
            if keyword.lower() in content.lower():
                print(f"🚫 [Guardrail] Potential data leak detected! Content contains sensitive keyword: '{keyword}'")
                return False
        return True

# 글로벌 인스턴스 생성
security_guard = GuardrailHook()
