from __future__ import annotations

from typing import Iterable, Mapping


def _to_minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def has_time_conflict(
    target_times: Iterable[Mapping[str, str]],
    existing_times: Iterable[Mapping[str, str]],
) -> bool:
    target_list = list(target_times)
    existing_list = list(existing_times)
    for target in target_list:
        t_day = target["day_of_week"]
        t_start = _to_minutes(target["start_time"])
        t_end = _to_minutes(target["end_time"])
        for existing in existing_list:
            if t_day != existing["day_of_week"]:
                continue
            e_start = _to_minutes(existing["start_time"])
            e_end = _to_minutes(existing["end_time"])
            if t_start < e_end and t_end > e_start:
                return True
    return False
