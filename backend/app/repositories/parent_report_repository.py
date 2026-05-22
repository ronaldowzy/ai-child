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
from app.domain.parent_report import ParentReport


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
        record.created_at = report.created_at

    def _to_domain(self, record: ParentReportRecord) -> ParentReport:
        return ParentReport(
            child_id=record.child_id,
            date=record.report_date,
            summary=record.summary,
            learning_observations=list(record.learning_observations or []),
            expression_observations=list(record.expression_observations or []),
            emotion_observations=list(record.emotion_observations or []),
            safety_alerts=list(record.safety_alerts or []),
            suggested_parent_actions=list(record.suggested_parent_actions or []),
            created_at=self._aware_datetime(record.created_at),
        )

    def _aware_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def _record_id(self, child_id: str, report_date: date) -> str:
        digest = sha256(f"{child_id}:{report_date.isoformat()}".encode()).hexdigest()
        return f"report_{digest[:32]}"
