"""Deploy exchange credentials from local secure file into environment.

Expected file: secrets/exchange_credentials.json
{
  "EXCHANGE_API_KEY": "...",
  "EXCHANGE_API_SECRET": "..."
}
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from src.ops.secrets_loader import load_exchange_credentials_from_file


def main() -> int:
    if not load_exchange_credentials_from_file(ROOT, overwrite=True):
        print("credentials_file_missing_or_invalid")
        return 1
    print("credentials_loaded_into_process_env")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
