#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
RUN_MIGRATE="${DB_SMOKE_RUN_MIGRATE:-true}"

resolve_python_cmd() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    read -r -a PYTHON_CMD <<< "${PYTHON_BIN}"
    return
  fi
  if command -v conda >/dev/null 2>&1 && conda env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME:-child-ai}"; then
    PYTHON_CMD=(conda run --no-capture-output -n "${CONDA_ENV_NAME:-child-ai}" python)
    return
  fi
  if [[ -x "/opt/homebrew/bin/conda" ]] && /opt/homebrew/bin/conda env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME:-child-ai}"; then
    PYTHON_CMD=(/opt/homebrew/bin/conda run --no-capture-output -n "${CONDA_ENV_NAME:-child-ai}" python)
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
    return
  fi
  if command -v python >/dev/null 2>&1; then
    PYTHON_CMD=(python)
    return
  fi
  echo "No Python interpreter found. Set PYTHON_BIN." >&2
  exit 1
}

resolve_python_cmd

cd "${BACKEND_DIR}"
DB_PRECHECK_OUTPUT="$("${PYTHON_CMD[@]}" - <<'PY'
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal

try:
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
except SQLAlchemyError as exc:
    print("DB_PERSISTENCE_SMOKE: SKIP database unavailable. Start local PostgreSQL first:")
    print("  bash scripts/setup_local_postgres.sh")
    print(f"error_type={exc.__class__.__name__}")
    print("DB_PRECHECK_STATUS=unavailable")
else:
    print("DB_PRECHECK_STATUS=ok")
PY
)"
sed '/DB_PRECHECK_STATUS=/d' <<< "${DB_PRECHECK_OUTPUT}"
if grep -q "DB_PRECHECK_STATUS=unavailable" <<< "${DB_PRECHECK_OUTPUT}"; then
  exit 2
fi

if [[ "${RUN_MIGRATE}" == "true" ]]; then
  if ! bash "${ROOT_DIR}/scripts/db_migrate.sh"; then
    echo "DB_PERSISTENCE_SMOKE: SKIP database migration failed. Start local PostgreSQL first:" >&2
    echo "  bash scripts/setup_local_postgres.sh" >&2
    exit 2
  fi
fi

"${PYTHON_CMD[@]}" - <<'PY'
from datetime import date
import os
from uuid import uuid4

os.environ["CHILD_AI_MODEL_PROVIDER"] = "mock"
os.environ["CHILD_AI_CHILD_CHAT_PROFILE"] = "child_chat_primary"
os.environ["CHILD_AI_PARENT_REPORT_PROFILE"] = "parent_report_mock"
os.environ["CHILD_AI_MIMO_ENABLED"] = "false"
os.environ["CHILD_AI_CONVERSATION_TTS_ENABLED"] = "false"

from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.models import (
    ConversationMessageRecord,
    ConversationSessionRecord,
    MemoryItemRecord,
    ParentPolicyRecord,
    ParentReportRecord,
    RoutingDecisionRecord,
)
from app.db.session import SessionLocal
from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemorySensitivity,
    MemoryType,
)
from app.domain.model_types import ModelResponse, ModelTaskType
from app.domain.schemas.conversation import (
    ClientContext,
    ConversationInput,
    ConversationMessageRequest,
)
from app.domain.schemas.parent_policy import ParentPolicyUpdateRequest
from app.providers.model.mock_provider import MockModelProvider
from app.repositories.memory_sql_repository import SqlAlchemyMemoryRepository
from app.services.child_agent_runtime import ChildAgentRuntime
from app.services.conversation_service import ConversationService
from app.services.memory_service import MemoryService
from app.services.model_registry import ModelRegistry
from app.services.parent_policy_service import ParentPolicyService
from app.services.parent_report_service import ParentReportService

get_settings.cache_clear()
mock_registry = ModelRegistry(providers={"mock": MockModelProvider(provider_name="mock")})


class DbSmokeParentReportRegistry:
    def generate(self, request):
        return ModelResponse(
            task_type=ModelTaskType.PARENT_REPORT,
            response_text="",
            structured_output={
                "daily_report": {
                    "summary": "DB smoke synthetic parent report.",
                    "learning_observations": [
                        "synthetic learning support summary; no raw child text"
                    ],
                    "expression_observations": [],
                    "emotion_observations": [],
                    "safety_alerts": [],
                    "suggested_parent_actions": [
                        "今晚可以轻轻问一个具体小细节；避免连续追问。"
                    ],
                    "tonight_parent_bridge": (
                        "今晚先轻松陪孩子聊一个小细节，不追问完整对话。"
                    ),
                }
            },
            provider_name="db_smoke",
            model_name="db-smoke-parent-report-v0",
            metadata={},
        )

try:
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
except SQLAlchemyError as exc:
    print("DB_PERSISTENCE_SMOKE: SKIP database unavailable. Start local PostgreSQL first:")
    print("  bash scripts/setup_local_postgres.sh")
    print(f"error_type={exc.__class__.__name__}")
    raise SystemExit(2)


suffix = uuid4().hex[:10]
child_id = f"child_db_smoke_{suffix}"
session_id = f"session_db_smoke_{suffix}"
policy_service = ParentPolicyService()
conversation_service = ConversationService(
    child_agent_runtime=ChildAgentRuntime(model_registry=mock_registry),
    debug_enabled=False,
)
memory_service = MemoryService(repository=SqlAlchemyMemoryRepository())
report_service = ParentReportService(
    memory_service=memory_service,
    model_registry=DbSmokeParentReportRegistry(),
)

policy = policy_service.update_policy(
    ParentPolicyUpdateRequest(
        child_id=child_id,
        child_nickname="豆豆",
        parent_message_raw="用低压力方式引导孩子先说题目在问什么。",
        goals=["学习问题先讲题意和第一步"],
    )
)
assert policy.child_nickname == "豆豆"

response = conversation_service.handle_message(
    ConversationMessageRequest(
        child_id=child_id,
        session_id=session_id,
        input=ConversationInput(type="text", text="我有一道题不会", attachments=[]),
        client_context=ClientContext(
            device_time="2026-05-22T16:35:00+08:00",
            timezone="Asia/Shanghai",
            app_mode="child",
        ),
    )
)
assert response.session_state.active_scene == "learning.homework_help"

memory_service.create(
    MemoryCreateRequest(
        child_id=child_id,
        memory_type=MemoryType.INTEREST,
        content="DB smoke synthetic summary: child likes low-pressure dinosaur chat.",
        tags=["db_smoke", "synthetic"],
        evidence=[
            MemoryEvidence(
                source="db_smoke_summary",
                session_id=session_id,
                quote_summary="synthetic summary only; no raw child text",
                metadata={"source": "db_smoke"},
            )
        ],
        confidence=0.8,
        importance=0.4,
        sensitivity=MemorySensitivity.LOW,
        visible_to_parent=True,
        visible_to_child=False,
    )
)

report = report_service.get_daily_report(child_id, report_date=date.today())
assert report.child_id == child_id

with SessionLocal() as session:
    policy_count = session.scalar(
        select(func.count()).select_from(ParentPolicyRecord).where(
            ParentPolicyRecord.child_id == child_id
        )
    )
    conversation_session = session.get(ConversationSessionRecord, session_id)
    message_count = session.scalar(
        select(func.count()).select_from(ConversationMessageRecord).where(
            ConversationMessageRecord.session_id == session_id
        )
    )
    routing_count = session.scalar(
        select(func.count()).select_from(RoutingDecisionRecord).where(
            RoutingDecisionRecord.session_id == session_id
        )
    )
    memory_count = session.scalar(
        select(func.count()).select_from(MemoryItemRecord).where(
            MemoryItemRecord.child_id == child_id
        )
    )
    report_count = session.scalar(
        select(func.count()).select_from(ParentReportRecord).where(
            ParentReportRecord.child_id == child_id
        )
    )

print(f"child_id={child_id}")
print(f"session_id={session_id}")
print(f"conversation_messages={message_count}")
print(f"routing_decisions={routing_count}")
print(f"memory_items={memory_count}")
print(f"parent_reports={report_count}")

assert policy_count == 1
assert conversation_session is not None
assert message_count and message_count >= 2
assert routing_count and routing_count >= 1
assert memory_count and memory_count >= 1
assert report_count and report_count >= 1

print("DB_PERSISTENCE_SMOKE: PASS")
PY
