from collections.abc import Callable
from datetime import date, datetime, timezone
from hashlib import sha256
from typing import Protocol

from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Child, ParentReportRecord
from app.db.session import SessionLocal
from app.domain.parent_report import (
    ParentReport,
    ParentReportGenerationStatus,
    ParentReportTopicOverview,
)


class ParentReportRepositoryUnavailable(RuntimeError):
    pass


class ParentReportRepositoryProtocol(Protocol):
    def save(self, report: ParentReport) -> ParentReport:
        ...

    def get(self, child_id: str, report_date: date) -> ParentReport | None:
        ...

    def list_by_child(self, child_id: str, limit: int = 30) -> list[ParentReport]:
        ...

    def delete(self, child_id: str, report_date: date) -> bool:
        ...

    def clear(self) -> None:
        ...


class InMemoryParentReportRepository:
    """Process-local fallback repository for dev/test DB outage paths."""

    def __init__(self) -> None:
        self._reports: dict[tuple[str, date], ParentReport] = {}

    def save(self, report: ParentReport) -> ParentReport:
        key = (report.child_id, report.date)
        self._reports[key] = report.model_copy(deep=True)
        return self._reports[key].model_copy(deep=True)

    def get(self, child_id: str, report_date: date) -> ParentReport | None:
        report = self._reports.get((child_id, report_date))
        if report is None:
            return None
        return report.model_copy(deep=True)

    def list_by_child(self, child_id: str, limit: int = 30) -> list[ParentReport]:
        reports = [
            report.model_copy(deep=True)
            for (report_child_id, _), report in self._reports.items()
            if report_child_id == child_id
        ]
        reports.sort(key=lambda report: (report.date, report.created_at), reverse=True)
        return reports[: max(limit, 0)]

    def delete(self, child_id: str, report_date: date) -> bool:
        key = (child_id, report_date)
        if key not in self._reports:
            return False
        del self._reports[key]
        return True

    def clear(self) -> None:
        self._reports.clear()


class ParentReportRepository:
    """SQLAlchemy-backed repository for DB1-B5 parent_reports persistence."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
    ) -> None:
        self._session_factory = session_factory

    def save(self, report: ParentReport) -> ParentReport:
        try:
            with self._session_factory() as session:
                self._ensure_child(session, report.child_id)
                record = self._find_record(
                    session,
                    child_id=report.child_id,
                    report_date=report.date,
                )
                if record is None:
                    record = ParentReportRecord(
                        id=self._record_id(report.child_id, report.date),
                        child_id=report.child_id,
                        report_date=report.date,
                        summary=report.summary,
                    )
                    session.add(record)
                self._apply_report(record, report)
                session.commit()
                session.refresh(record)
                return self._to_domain(record)
        except SQLAlchemyError as exc:
            raise ParentReportRepositoryUnavailable(str(exc)) from exc

    def get(self, child_id: str, report_date: date) -> ParentReport | None:
        try:
            with self._session_factory() as session:
                record = self._find_record(
                    session,
                    child_id=child_id,
                    report_date=report_date,
                )
                if record is None:
                    return None
                return self._to_domain(record)
        except SQLAlchemyError as exc:
            raise ParentReportRepositoryUnavailable(str(exc)) from exc

    def list_by_child(self, child_id: str, limit: int = 30) -> list[ParentReport]:
        try:
            with self._session_factory() as session:
                records = (
                    session.execute(
                        select(ParentReportRecord)
                        .where(ParentReportRecord.child_id == child_id)
                        .order_by(
                            ParentReportRecord.report_date.desc(),
                            ParentReportRecord.created_at.desc(),
                        )
                        .limit(max(limit, 0))
                    )
                    .scalars()
                    .all()
                )
                return [self._to_domain(record) for record in records]
        except SQLAlchemyError as exc:
            raise ParentReportRepositoryUnavailable(str(exc)) from exc

    def delete(self, child_id: str, report_date: date) -> bool:
        try:
            with self._session_factory() as session:
                record = self._find_record(
                    session,
                    child_id=child_id,
                    report_date=report_date,
                )
                if record is None:
                    return False
                session.delete(record)
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise ParentReportRepositoryUnavailable(str(exc)) from exc

    def clear(self) -> None:
        try:
            with self._session_factory() as session:
                session.execute(sqlalchemy_delete(ParentReportRecord))
                session.commit()
        except SQLAlchemyError as exc:
            raise ParentReportRepositoryUnavailable(str(exc)) from exc

    def _find_record(
        self,
        session: Session,
        *,
        child_id: str,
        report_date: date,
    ) -> ParentReportRecord | None:
        return session.execute(
            select(ParentReportRecord).where(
                ParentReportRecord.child_id == child_id,
                ParentReportRecord.report_date == report_date,
            )
        ).scalar_one_or_none()

    def _ensure_child(self, session: Session, child_id: str) -> None:
        child = session.get(Child, child_id)
        if child is not None:
            return
        session.add(
            Child(
                id=child_id,
                nickname=child_id,
                timezone="Asia/Shanghai",
                profile={},
            )
        )

    def _apply_report(
        self,
        record: ParentReportRecord,
        report: ParentReport,
    ) -> None:
        record.child_id = report.child_id
        record.report_date = report.date
        record.summary = report.summary
        record.learning_observations = list(report.learning_observations)
        record.expression_observations = list(report.expression_observations)
        record.emotion_observations = list(report.emotion_observations)
        record.safety_alerts = list(report.safety_alerts)
        record.suggested_parent_actions = list(report.suggested_parent_actions)
        record.generation_status = report.generation_status.value
        record.generated_by = report.generated_by
        record.generation_error_code = report.generation_error_code
        record.material_fingerprint = report.material_fingerprint
        record.created_at = report.created_at

    def _to_domain(self, record: ParentReportRecord) -> ParentReport:
        return ParentReport(
            child_id=record.child_id,
            date=record.report_date,
            summary=record.summary,
            topic_overview=self._topic_overview_from_legacy_record(record),
            conversation_summary=record.summary,
            learning_observations=list(record.learning_observations or []),
            expression_observations=list(record.expression_observations or []),
            emotion_observations=list(record.emotion_observations or []),
            safety_alerts=list(record.safety_alerts or []),
            suggested_parent_actions=list(record.suggested_parent_actions or []),
            tonight_parent_bridge=self._bridge_from_actions(
                list(record.suggested_parent_actions or []),
            ),
            created_at=self._aware_datetime(record.created_at),
            generation_status=ParentReportGenerationStatus(
                record.generation_status or ParentReportGenerationStatus.LEGACY.value
            ),
            generated_by=record.generated_by or "legacy",
            generation_error_code=record.generation_error_code,
            material_fingerprint=record.material_fingerprint,
            avoid_followup=self._avoid_followup_from_legacy_actions(
                list(record.suggested_parent_actions or []),
            ),
        )

    def _aware_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def _bridge_from_actions(self, actions: list[str]) -> str | None:
        for action in actions:
            clean = " ".join(action.strip().split())
            if not clean:
                continue
            if clean.startswith("今晚可以"):
                return clean[:260]
            if "图片" in clean:
                return (
                    "今晚可以轻轻问：“你今天那张图，最想让我看哪里？”"
                    "如果孩子不想说，就换轻松方式，不追问。"
                )
            if "学习" in clean or "作业" in clean:
                return (
                    "今晚可以轻轻说：“如果有题卡住，我们先听你说题目在问什么。”"
                    "如果孩子不想说，就先休息，不追问答案。"
                )
        return None

    def _topic_overview_from_legacy_record(
        self,
        record: ParentReportRecord,
    ) -> list[ParentReportTopicOverview]:
        actions = list(record.suggested_parent_actions or [])
        bridge = self._bridge_from_actions(actions) or ""
        summary = " ".join((record.summary or "").split())[:260]
        if record.learning_observations:
            topic = "学习求助"
            intent = "学习或题目支持"
        elif record.safety_alerts:
            topic = "安全或隐私边界"
            intent = "需要父亲平静关注"
        elif record.expression_observations:
            topic = "表达观察"
            intent = "日常表达和沟通节奏"
        elif record.emotion_observations:
            topic = "情绪表达"
            intent = "情绪或状态线索"
        else:
            topic = "日常聊天"
            intent = "轻量日常交流"
        return [
            ParentReportTopicOverview(
                topic=topic,
                child_intent=intent,
                summary=summary or "旧版日报记录没有单独的话题卡片。",
                emotion_tone="",
                parent_bridge=bridge,
            )
        ]

    def _avoid_followup_from_legacy_actions(self, actions: list[str]) -> list[str]:
        avoid = ["不要追问孩子今天在小白狐里逐字聊了什么。"]
        if any("答案" in action or "作业" in action for action in actions):
            avoid.append("不要直接追问最终答案或替孩子完成作业。")
        if any("图片" in action for action in actions):
            avoid.append("不要把所有图片都默认当成作业或隐私问题。")
        return avoid

    def _record_id(self, child_id: str, report_date: date) -> str:
        digest = sha256(f"{child_id}:{report_date.isoformat()}".encode()).hexdigest()
        return f"report_{digest[:32]}"
