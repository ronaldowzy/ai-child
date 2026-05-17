from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TimePeriod(str, Enum):
    MORNING_BEFORE_SCHOOL = "morning_before_school"
    AFTER_SCHOOL = "after_school"
    HOMEWORK_TIME = "homework_time"
    BEDTIME = "bedtime"
    OTHER = "other"


class TimeScheduleEntry(BaseModel):
    period: TimePeriod
    start: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    goal: str
    preferred_interactions: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)


DEFAULT_DAILY_SCHEDULE: tuple[TimeScheduleEntry, ...] = (
    TimeScheduleEntry(
        period=TimePeriod.MORNING_BEFORE_SCHOOL,
        start="06:30",
        end="07:50",
        goal="轻量计划，不制造压力",
        preferred_interactions=["今日小目标", "带物品提醒", "一句鼓励"],
        avoid=["高强度学习", "复杂复盘"],
    ),
    TimeScheduleEntry(
        period=TimePeriod.AFTER_SCHOOL,
        start="15:30",
        end="18:00",
        goal="情绪缓冲、学校表达、作业衔接",
        preferred_interactions=["状态选择", "学校小事", "兴趣切入", "学习卡点"],
        avoid=["立刻连续追问", "一开始就要求学习"],
    ),
    TimeScheduleEntry(
        period=TimePeriod.HOMEWORK_TIME,
        start="18:00",
        end="20:20",
        goal="作业引导、错题分析、思路训练",
        preferred_interactions=["拍照识题", "分级提示", "复述思路"],
        avoid=["直接给答案", "替孩子完成作业"],
    ),
    TimeScheduleEntry(
        period=TimePeriod.BEDTIME,
        start="20:20",
        end="21:30",
        goal="低刺激复盘、情绪安定、明日计划",
        preferred_interactions=["三问复盘", "情绪总结", "晚安收尾"],
        avoid=["强刺激话题", "长时间聊天", "复杂学习任务"],
    ),
)


def default_daily_schedule() -> list[TimeScheduleEntry]:
    return [entry.model_copy(deep=True) for entry in DEFAULT_DAILY_SCHEDULE]


class TimeContext(BaseModel):
    now: datetime
    timezone: str
    time_period: TimePeriod
    weekday: bool
    schedule_goal: str | None = None
    preferred_interactions: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
