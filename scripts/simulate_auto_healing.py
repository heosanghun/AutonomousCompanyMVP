"""Simulate operational incidents and test the auto-healing framework."""

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ops.auto_healer import AutoHealer

logging.basicConfig(level=logging.INFO)

def simulate_rate_limit() -> None:
    """Mock a 429 Rate Limit Error."""
    print("--- Simulating Rate Limit Hit ---")
    healer = AutoHealer()
    
    attempts = 0
    def failing_api_call():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception("HTTP 429 Too Many Requests: Rate limit exceeded")
        return "Success on attempt 3!"

    result = healer.run_with_healing(failing_api_call)
    print(f"Final Result: {result}\n")


def simulate_exchange_maintenance() -> None:
    """Mock an Exchange Maintenance Error."""
    print("--- Simulating Exchange Maintenance ---")
    healer = AutoHealer()
    
    def failing_api_call():
        raise Exception("Binance API Error: 503 System Maintenance")

    try:
        healer.run_with_healing(failing_api_call)
    except Exception as e:
        print(f"AutoHealer correctly escalated fatal error: {e}\n")


def simulate_unknown_crash() -> None:
    """Mock an Uncaught System Crash."""
    print("--- Simulating Unknown Crash ---")
    healer = AutoHealer()
    
    def failing_api_call():
        raise ValueError("Unexpected TypeError in strategy matrix calculation")

    try:
        healer.run_with_healing(failing_api_call)
    except Exception as e:
        print(f"AutoHealer triggered SEV1 alert and aborted: {e}\n")


if __name__ == "__main__":
    print("Starting Auto Healing Simulation...\n")
    
    # Enable test output (you can set OPS_ALERT_WEBHOOK_URL to a discord channel to see real messages)
    simulate_rate_limit()
    simulate_exchange_maintenance()
    simulate_unknown_crash()
    
    print("Simulation Complete.")
