from datetime import datetime

from app.domain.time import TimePeriod
from app.services.time_context_service import TimeContextService


def test_time_context_resolves_after_school() -> None:
    context = TimeContextService().build_context(
        device_time=datetime.fromisoformat("2026-05-18T16:30:00+08:00"),
        timezone="Asia/Shanghai",
    )

    assert context.time_period == TimePeriod.AFTER_SCHOOL
    assert context.schedule_goal == "情绪缓冲、学校表达、作业衔接"


def test_time_context_resolves_bedtime() -> None:
    context = TimeContextService().build_context(
        device_time=datetime.fromisoformat("2026-05-18T20:45:00+08:00"),
        timezone="Asia/Shanghai",
    )

    assert context.time_period == TimePeriod.BEDTIME
    assert "晚安收尾" in context.preferred_interactions


def test_time_context_resolves_other_period() -> None:
    context = TimeContextService().build_context(
        device_time=datetime.fromisoformat("2026-05-18T22:00:00+08:00"),
        timezone="Asia/Shanghai",
    )

    assert context.time_period == TimePeriod.OTHER
    assert context.schedule_goal is None


def test_time_context_uses_configured_schedule() -> None:
    context = TimeContextService().build_context(
        device_time=datetime.fromisoformat("2026-05-18T14:30:00+08:00"),
        timezone="Asia/Shanghai",
        schedule={
            "daily_schedule": [
                {
                    "period": "after_school",
                    "start": "14:00",
                    "end": "15:00",
                    "goal": "自定义放学后缓冲",
                    "preferred_interactions": ["状态选择"],
                    "avoid": ["连续追问"],
                }
            ]
        },
    )

    assert context.time_period == TimePeriod.AFTER_SCHOOL
    assert context.schedule_goal == "自定义放学后缓冲"
