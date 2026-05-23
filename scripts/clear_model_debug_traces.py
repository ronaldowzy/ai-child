#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.repositories.model_debug_trace_repository import ModelDebugTraceRepository  # noqa: E402


def main() -> None:
    deleted = ModelDebugTraceRepository().clear()
    print(f"MODEL_DEBUG_TRACES_CLEARED rows={deleted}")


if __name__ == "__main__":
    main()
