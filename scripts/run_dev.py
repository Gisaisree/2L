"""Cross-platform local run helper: python scripts/run_dev.py"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if not (ROOT / ".env").is_file() and not os.environ.get("SECRET_KEY"):
    print("No .env file found. Copy .env.example to .env and set SECRET_KEY first.")
    sys.exit(1)

import run  # noqa: E402

if __name__ == "__main__":
    print("Starting on http://127.0.0.1:5000 (Ctrl+C to stop)")
    run.main()
