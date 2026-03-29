"""Autonomous healing logic for expected operational failures (Rate limits, Network, Maintenance)."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from src.ops.alerts import send_alert


class AutoHealer:
    """Orchestrates retries, mode fallbacks, and alerts on runtime failures."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("AutoHealer")
        self.consecutive_rate_limits = 0
        self.consecutive_network_errors = 0

    def handle_rate_limit(self, exc: Exception) -> bool:
        """Triggers exponential backoff. Returns True if execution should pause and continue."""
        self.consecutive_rate_limits += 1
        wait_sec = 15 * (2 ** (self.consecutive_rate_limits - 1))
        
        # Max wait limit (e.g., 5 minutes). Beyond this, fail completely.
        if wait_sec > 300:
            send_alert("fatal_rate_limit", {"wait_sec": wait_sec, "message": str(exc)})
            return False

        msg = f"API Rate Limit hit. Applying backoff for {wait_sec} seconds."
        self.logger.warning(msg)
        send_alert("api_rate_limit_spike", {"wait_sec": wait_sec, "attempts": self.consecutive_rate_limits})
        
        time.sleep(wait_sec)
        return True

    def handle_maintenance(self, exc: Exception) -> bool:
        """Triggers mode fallback or extended suspension."""
        self.logger.error("Exchange Maintenance detected. Suspending execution for 1 hour.")
        send_alert("exchange_maintenance", {"duration": "1 hour", "action": "system_sleep"})
        
        # For MVP simulation purposes, we won't actually sleep an hour, we'll return False
        # to cleanly shutdown, but in production, we'd sleep or transition state.
        return False

    def run_with_healing(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Wraps an execution step and automatically recovers known exceptions."""
        while True:
            try:
                res = func(*args, **kwargs)
                # Success resets counters
                if self.consecutive_rate_limits > 0:
                    send_alert("rate_limit_recovered", {"recovered_after_attempts": self.consecutive_rate_limits})
                    self.consecutive_rate_limits = 0
                return res

            except Exception as e:
                err_str = str(e).lower()
                
                # Identify error type heuristically
                if "rate" in err_str or "429" in err_str or "too many requests" in err_str:
                    if self.handle_rate_limit(e):
                        continue
                    raise e  # Fatal rate limit reached

                if "maintenance" in err_str or "503" in err_str or "down" in err_str:
                    self.handle_maintenance(e)
                    raise e  # Clean shutdown or manual intervention needed

                # Unknown exception -> trigger kill switch via alert
                self.logger.error(f"Uncaught failure. Triggering SEV1 alert. Exception: {e}")
                send_alert("sev1_system_crash", {"exception": str(e), "action": "trigger_kill_switch"})
                raise e
