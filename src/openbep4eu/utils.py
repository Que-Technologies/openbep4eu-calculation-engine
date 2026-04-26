import pandas as pd
import math
import re


def build_schedule_series_from_id(
        schedule_id,
        timeline,
        schedule_constant_map=None,
        schedule_compact_map=None,
) -> pd.Series:

    if schedule_constant_map:
        sch = schedule_constant_map[schedule_id]
        return pd.Series(float(sch.hourlyValue), index=timeline)

    if schedule_compact_map:
        return expand_schedule_compact_to_series(
            schedule=schedule_compact_map[schedule_id],
            index=timeline,
        )

    raise ValueError(f"Schedule '{schedule_id}' not found.")


def expand_schedule_compact_to_series(
        schedule,
        index: pd.DatetimeIndex,
) -> pd.Series:
    """
    Expand a scheduleCompact object into a Series aligned to `index`.

    Supported compact pattern:
      Through: MM/DD
      For: AllDays | Weekdays | Weekends | Monday ... Sunday
      Until: HH:MM
      <numeric value>

    Example supported formats are the ones shown in the uploaded JSON examples.  [oai_citation:1‡scheduleCompact_examples.json](sediment://file_00000000dc8c71fda4930852086272ff)
    """
    if index.empty:
        return pd.Series(dtype=float, index=index)

    data = getattr(schedule, "data", None)
    if data is None:
        raise ValueError(f"scheduleCompact '{getattr(schedule, 'id', '<unknown>')}' has no data field.")

    fields = [_normalize_compact_field(item.field) for item in data]

    # Parse into blocks:
    # [
    #   {
    #     "through": (12, 31),
    #     "for_rules": [
    #         {
    #             "day_type": "AllDays",
    #             "until_rules": [((6,0), 16.0), ((22,0), 20.0), ((24,0), 16.0)]
    #         },
    #         ...
    #     ]
    #   },
    #   ...
    # ]
    through_blocks: list[dict] = []

    i = 0
    current_through = None
    current_for = None

    while i < len(fields):
        f = fields[i]

        if isinstance(f, str) and f.lower().startswith("through:"):
            current_through = {
                "through": _parse_through_date(f),
                "for_rules": [],
            }
            through_blocks.append(current_through)
            current_for = None
            i += 1
            continue

        if isinstance(f, str) and f.lower().startswith("for:"):
            if current_through is None:
                raise ValueError("Encountered 'For:' before any 'Through:' block.")
            current_for = {
                "day_type": _parse_for_type(f),
                "until_rules": [],
            }
            current_through["for_rules"].append(current_for)
            i += 1
            continue

        if isinstance(f, str) and f.lower().startswith("until:"):
            if current_for is None:
                raise ValueError("Encountered 'Until:' before any 'For:' block.")

            until_time = _parse_until_time(f)
            if i + 1 >= len(fields) or not isinstance(fields[i + 1], float):
                raise ValueError(f"'Until:' at position {i} is not followed by a numeric value.")

            value = float(fields[i + 1])
            current_for["until_rules"].append((until_time, value))
            i += 2
            continue

        raise ValueError(f"Unexpected scheduleCompact token at position {i}: {f!r}")

    # Build series
    out = pd.Series(index=index, dtype=float)

    for ts in index:
        mmdd = _date_mmdd(ts)
        matched_value = None

        for through_block in through_blocks:
            if not _month_day_leq(mmdd, through_block["through"]):
                continue

            for_rule_match = None
            for for_rule in through_block["for_rules"]:
                if _matches_day_type(ts, for_rule["day_type"]):
                    for_rule_match = for_rule
                    break

            if for_rule_match is None:
                continue

            minutes_now = ts.hour * 60 + ts.minute

            for (uh, um), value in for_rule_match["until_rules"]:
                until_minutes = 24 * 60 if (uh, um) == (24, 0) else uh * 60 + um
                if minutes_now < until_minutes:
                    matched_value = value
                    break

            if matched_value is None:
                raise ValueError(
                    f"No Until rule matched timestamp {ts} in scheduleCompact "
                    f"'{getattr(schedule, 'id', '<unknown>')}'."
                )

            break

        if matched_value is None:
            raise ValueError(
                f"No Through/For block matched timestamp {ts} in scheduleCompact "
                f"'{getattr(schedule, 'id', '<unknown>')}'."
            )

        out.loc[ts] = matched_value

    return out

def _normalize_compact_field(raw) -> str | float:
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        return raw.strip()
    raise ValueError(f"Unsupported scheduleCompact field type: {type(raw)}")


def _parse_through_date(text: str) -> tuple[int, int]:
    m = re.fullmatch(r"Through:\s*(\d{1,2})/(\d{1,2})", text, flags=re.IGNORECASE)
    if not m:
        raise ValueError(f"Invalid Through field: '{text}'")
    month = int(m.group(1))
    day = int(m.group(2))
    return month, day


def _parse_for_type(text: str) -> str:
    m = re.fullmatch(r"For:\s*(.+)", text, flags=re.IGNORECASE)
    if not m:
        raise ValueError(f"Invalid For field: '{text}'")
    return m.group(1).strip()


def _parse_until_time(text: str) -> tuple[int, int]:
    m = re.fullmatch(r"Until:\s*(\d{1,2}):(\d{2})", text, flags=re.IGNORECASE)
    if not m:
        raise ValueError(f"Invalid Until field: '{text}'")
    hour = int(m.group(1))
    minute = int(m.group(2))
    if hour == 24 and minute == 0:
        return 24, 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Invalid Until time: '{text}'")
    return hour, minute


def _matches_day_type(ts: pd.Timestamp, day_type: str) -> bool:
    d = day_type.strip().lower()
    wd = ts.weekday()  # Monday=0 ... Sunday=6

    if d == "alldays":
        return True
    if d == "weekdays":
        return wd < 5
    if d == "weekends":
        return wd >= 5
    if d == "monday":
        return wd == 0
    if d == "tuesday":
        return wd == 1
    if d == "wednesday":
        return wd == 2
    if d == "thursday":
        return wd == 3
    if d == "friday":
        return wd == 4
    if d == "saturday":
        return wd == 5
    if d == "sunday":
        return wd == 6

    raise ValueError(f"Unsupported For day type: '{day_type}'")


def _date_mmdd(ts: pd.Timestamp) -> tuple[int, int]:
    return ts.month, ts.day


def _month_day_leq(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a <= b