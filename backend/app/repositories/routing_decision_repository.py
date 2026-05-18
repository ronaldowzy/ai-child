from datetime import datetime, timezone
from uuid import uuid4

from app.domain.scene import RoutingDecisionRecord, SceneRouteDecision


class InMemoryRoutingDecisionRepository:
    """In-memory routing decision log for the v0.1 orchestrator skeleton."""

    def __init__(self) -> None:
        self._records: list[RoutingDecisionRecord] = []

    def save(self, decision: SceneRouteDecision) -> RoutingDecisionRecord:
        record = RoutingDecisionRecord(
            id=str(uuid4()),
            message_id=decision.message_id or str(uuid4()),
            session_id=decision.session_id,
            primary_intent=decision.primary_intent,
            active_scene=decision.active_scene,
            sub_scene=decision.sub_scene,
            risk_level=decision.risk_level,
            decision_json=decision.model_dump(mode="json"),
            signals_json=decision.signals,
            confidence=decision.confidence,
            created_at=datetime.now(timezone.utc),
        )
        self._records.append(record)
        return record

    def list_by_session(self, session_id: str) -> list[RoutingDecisionRecord]:
        return [record for record in self._records if record.session_id == session_id]

    def latest_for_session(self, session_id: str) -> RoutingDecisionRecord | None:
        for record in reversed(self._records):
            if record.session_id == session_id:
                return record
        return None

    def clear(self) -> None:
        self._records.clear()


_routing_decision_repository = InMemoryRoutingDecisionRepository()


def get_routing_decision_repository() -> InMemoryRoutingDecisionRepository:
    return _routing_decision_repository
