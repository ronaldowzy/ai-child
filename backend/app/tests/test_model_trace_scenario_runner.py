from __future__ import annotations

from pathlib import Path
import py_compile
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.repositories.model_debug_trace_repository import ModelDebugTraceRepository


def _sqlite_trace_repository() -> ModelDebugTraceRepository:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    return ModelDebugTraceRepository(session_factory=session_factory)


def _import_runner():
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.run_model_trace_scenarios import run_trace_scenarios

    return run_trace_scenarios


def test_trace_scenario_runner_generates_traces_and_report(tmp_path: Path) -> None:
    run_trace_scenarios = _import_runner()

    repository = _sqlite_trace_repository()
    report_path = tmp_path / "trace_review.md"

    scenarios, traces, generated_path = run_trace_scenarios(
        repository=repository,
        report_path=report_path,
    )

    assert generated_path == report_path
    assert len(scenarios) >= 15
    assert len(traces) >= 14
    assert any(trace.task_type == "child_chat" for trace in traces)
    assert any(trace.task_type == "parent_report" for trace in traces)
    assert all(trace.provider_name == "mock" for trace in traces)
    assert repository.list_recent(limit=500)

    report = report_path.read_text(encoding="utf-8")
    assert "default after-school opening" in report
    assert "运动夸张表达" in report
    assert "父亲日报" in report
    assert "mock responses do not represent real MiMo quality" in report
    assert "Trace count" in report


def test_trace_scenario_report_does_not_include_secrets_or_raw_base64(
    tmp_path: Path,
) -> None:
    run_trace_scenarios = _import_runner()

    repository = _sqlite_trace_repository()
    report_path = tmp_path / "trace_review.md"

    run_trace_scenarios(repository=repository, report_path=report_path)

    report = report_path.read_text(encoding="utf-8").lower()
    assert "sk-" not in report
    assert "authorization:" not in report
    assert "bearer " not in report
    assert "data:image" not in report
    assert "data:audio" not in report
    assert ";base64," not in report


def test_trace_scripts_compile() -> None:
    root = Path(__file__).resolve().parents[3]
    for script_name in (
        "run_model_trace_scenarios.py",
        "show_model_debug_traces.py",
        "clear_model_debug_traces.py",
    ):
        py_compile.compile(
            str(root / "scripts" / script_name),
            doraise=True,
        )
