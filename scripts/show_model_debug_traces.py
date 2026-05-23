#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.repositories.model_debug_trace_repository import ModelDebugTraceRepository  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show recent local model_debug_traces rows.",
    )
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    traces = ModelDebugTraceRepository().list_recent(limit=args.limit)
    for trace in traces:
        print(
            json.dumps(
                {
                    "created_at": trace.created_at.isoformat(),
                    "task_type": trace.task_type,
                    "provider_name": trace.provider_name,
                    "model_name": trace.model_name,
                    "child_id": trace.child_id,
                    "session_id": trace.session_id,
                    "fallback_used": trace.fallback_used,
                    "policy_blocked": trace.policy_blocked,
                    "error_type": trace.error_type,
                    "elapsed_ms": trace.elapsed_ms,
                    "request_input_text": trace.request_input_text,
                    "response_text": trace.response_text,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
