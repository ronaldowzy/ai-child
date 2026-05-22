from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.parent_report import ParentReport
from app.repositories.parent_report_repository import ParentReportRepository


def _sqlite_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def _report(
    *,
    child_id: str = "child_parent_report_sql",
    report_date: date = date(2026, 5, 22),
    summary: str = "今天记录了 1 条结构化观察，重点集中在学习支持。",
    created_at: datetime = datetime(2026, 5, 22, 20, 0, tzinfo=timezone.utc),
) -> ParentReport:
    return ParentReport(
        child_id=child_id,
        date=report_date,
        summary=summary,
        learning_observations=["孩子在学习求助时适合先复述题意。"],
        expression_observations=["选择题式引导更容易开始表达。"],
        emotion_observations=["先回应感受，再进入问题解决。"],
        safety_alerts=["今天出现需要父亲关注的安全信号。"],
        suggested_parent_actions=["今晚先做安全确认。"],
        created_at=created_at,
    )


def test_parent_report_repository_save_get_roundtrips_all_fields() -> None:
    repository = ParentReportRepository(session_factory=_sqlite_session_factory())
    report = _report()

    saved = repository.save(report)
    reloaded = repository.get(report.child_id, report.date)

    assert reloaded is not None
    assert saved.child_id == report.child_id
    assert reloaded.date == report.date
    assert reloaded.summary == report.summary
    assert reloaded.learning_observations == report.learning_observations
    assert reloaded.expression_observations == report.expression_observations
    assert reloaded.emotion_observations == report.emotion_observations
    assert reloaded.safety_alerts == report.safety_alerts
    assert reloaded.suggested_parent_actions == report.suggested_parent_actions
    assert reloaded.created_at == report.created_at


def test_parent_report_repository_same_child_date_updates_without_duplicate() -> None:
    repository = ParentReportRepository(session_factory=_sqlite_session_factory())
    original = _report(summary="旧摘要。")
    updated = original.model_copy(
        update={
            "summary": "新摘要。",
            "learning_observations": ["更新后的学习观察。"],
            "created_at": datetime(2026, 5, 22, 21, 0, tzinfo=timezone.utc),
        },
        deep=True,
    )

    repository.save(original)
    repository.save(updated)
    reports = repository.list_by_child(original.child_id)

    assert len(reports) == 1
    assert reports[0].summary == "新摘要。"
    assert reports[0].learning_observations == ["更新后的学习观察。"]
    assert reports[0].created_at == updated.created_at


def test_parent_report_repository_list_by_child_orders_by_date_desc() -> None:
    repository = ParentReportRepository(session_factory=_sqlite_session_factory())
    older = _report(report_date=date(2026, 5, 20), summary="older")
    newer = _report(report_date=date(2026, 5, 22), summary="newer")
    other_child = _report(
        child_id="child_parent_report_sql_other",
        report_date=date(2026, 5, 23),
        summary="other",
    )

    repository.save(older)
    repository.save(newer)
    repository.save(other_child)

    assert [report.summary for report in repository.list_by_child(older.child_id)] == [
        "newer",
        "older",
    ]
    assert [report.summary for report in repository.list_by_child(older.child_id, limit=1)] == [
        "newer"
    ]


def test_parent_report_repository_delete_returns_bool() -> None:
    repository = ParentReportRepository(session_factory=_sqlite_session_factory())
    report = _report()
    repository.save(report)

    assert repository.delete(report.child_id, report.date) is True
    assert repository.delete(report.child_id, report.date) is False
    assert repository.get(report.child_id, report.date) is None


def test_parent_report_repository_json_list_fields_roundtrip_empty_lists() -> None:
    repository = ParentReportRepository(session_factory=_sqlite_session_factory())
    report = _report().model_copy(
        update={
            "learning_observations": [],
            "expression_observations": [],
            "emotion_observations": [],
            "safety_alerts": [],
            "suggested_parent_actions": [],
        },
        deep=True,
    )

    repository.save(report)
    reloaded = repository.get(report.child_id, report.date)

    assert reloaded is not None
    assert reloaded.learning_observations == []
    assert reloaded.expression_observations == []
    assert reloaded.emotion_observations == []
    assert reloaded.safety_alerts == []
    assert reloaded.suggested_parent_actions == []
