"""Security and access-control hooks for autonomous agents."""

import os
from pathlib import Path
from typing import List, Optional


class SecurityViolationError(Exception):
    """Raised when an agent attempts a forbidden action."""
    pass


class GuardrailHook:
    """
    Prevents specialized agents from accessing sensitive data or executing destructive commands.
    Acts as a 'brake' on the autonomous car (the AI).
    """

    def __init__(self, restricted_paths: Optional[List[str]] = None, restricted_commands: Optional[List[str]] = None):
        # Default physical files agents shouldn't read without explicit admin role
        self.restricted_paths = restricted_paths or [
            ".env",
            ".ENV",
            "secrets/",
            "configs/master_plan.json",
            "configs/operational_limits.json",
        ]
        
        # Commands that shouldn't be executed autonomously
        self.restricted_commands = restricted_commands or [
            "rm -rf",
            "git push --force",
            "wrangler pages secret put"
        ]

    def verify_file_access(self, path: str, mode: str = "read") -> bool:
        """
        Check if the file access is permitted for standard agents.
        Throws SecurityViolationError if forbidden.
        """
        normalized_path = Path(path).as_posix().lower()
        
        for restricted in self.restricted_paths:
            # Simple wildcard check
            if restricted.lower() in normalized_path:
                msg = f"[SECURITY HOOK TRIGGERED] Attempted to {mode} a restricted path: {path}."
                from src.ops.alerts import send_alert
                send_alert("agent_security_violation", {"path": path, "mode": mode, "hook": "FileAccess"})
                raise SecurityViolationError(msg)
                
        return True

    def verify_command(self, cmd: str) -> bool:
        """
        Prevents dangerous shell executions by an agent.
        """
        for r_cmd in self.restricted_commands:
            if r_cmd in cmd:
                msg = f"[SECURITY HOOK TRIGGERED] Attempted to run restricted command: {cmd}."
                from src.ops.alerts import send_alert
                send_alert("agent_security_violation", {"cmd": cmd, "hook": "CommandExecution"})
                raise SecurityViolationError(msg)
        return True
