from collections.abc import Iterable
from datetime import datetime, time, timezone as datetime_timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.time import (
    TimeContext,
    TimePeriod,
    TimeScheduleEntry,
    default_daily_schedule,
)


class TimeContextService:
    def build_context(
        self,
        *,
        device_time: datetime,
        timezone: str,
        schedule: Any | None = None,
    ) -> TimeContext:
        local_now = self._to_local_time(device_time, timezone)
        schedule_entries = self._normalize_schedule(schedule)
        matched_entry = self._match_schedule_entry(local_now.time(), schedule_entries)

        return TimeContext(
            now=local_now,
            timezone=timezone,
            time_period=matched_entry.period if matched_entry else TimePeriod.OTHER,
            weekday=local_now.weekday() < 5,
            schedule_goal=matched_entry.goal if matched_entry else None,
            preferred_interactions=(
                matched_entry.preferred_interactions if matched_entry else []
            ),
            avoid=matched_entry.avoid if matched_entry else [],
        )

    def _to_local_time(self, device_time: datetime, timezone: str) -> datetime:
        local_zone = self._resolve_timezone(device_time, timezone)
        if device_time.tzinfo is None:
            return device_time.replace(tzinfo=local_zone)
        return device_time.astimezone(local_zone)

    def _resolve_timezone(self, device_time: datetime, timezone: str):
        try:
            return ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            return device_time.tzinfo or datetime_timezone.utc

    def _normalize_schedule(self, schedule: Any | None) -> list[TimeScheduleEntry]:
        if schedule is None:
            return default_daily_schedule()

        if hasattr(schedule, "daily_schedule"):
            raw_entries = schedule.daily_schedule
        elif isinstance(schedule, dict):
            raw_entries = schedule.get("daily_schedule", [])
        else:
            raw_entries = schedule

        if not isinstance(raw_entries, Iterable):
            return default_daily_schedule()

        return [
            entry
            if isinstance(entry, TimeScheduleEntry)
            else TimeScheduleEntry.model_validate(entry)
            for entry in raw_entries
        ]

    def _match_schedule_entry(
        self, current_time: time, schedule_entries: list[TimeScheduleEntry]
    ) -> TimeScheduleEntry | None:
        for entry in schedule_entries:
            start = self._parse_time(entry.start)
            end = self._parse_time(entry.end)
            if self._time_in_range(current_time, start, end):
                return entry
        return None

    def _parse_time(self, value: str) -> time:
        return datetime.strptime(value, "%H:%M").time()

    def _time_in_range(self, current_time: time, start: time, end: time) -> bool:
        if start <= end:
            return start <= current_time < end
        return current_time >= start or current_time < end


_time_context_service = TimeContextService()


def get_time_context_service() -> TimeContextService:
    return _time_context_service
