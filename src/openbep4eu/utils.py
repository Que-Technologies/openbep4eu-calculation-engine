import pandas as pd
import math
import re
from openbep4eu.building_as_such.models.definitions import ScheduleCompact
from openbep4eu.building_as_such.models.epw import EPWData
from typing import Literal
from typing import List, Optional, Union
from openbep4eu.building_as_such.models.envelope_element import ConstructionLayer

ElementType = Literal["Ceiling", "Floor", "Roof", "Wall", "Door", "GlassDoor", "Window"]

def prepend_last_month_series(series: pd.Series) -> pd.Series:
    dec = series[series.index.month == 12]
    return pd.concat([dec, series])

def prepend_last_month_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    dec = df[df.index.month == 12]
    return pd.concat([dec, df])


def prepend_last_month_list(values, original_index: pd.DatetimeIndex):
    dec_idx = [i for i, ts in enumerate(original_index) if ts.month == 12]
    dec_values = [values[i] for i in dec_idx]
    return dec_values + list(values)


def build_simulation_timeline(epw_data: EPWData) -> pd.DatetimeIndex:
    return epw_data.data.index

def build_supply_air_temperature_series(
        temp_air: pd.Series,
        delta: float = 0.0,
) -> pd.Series:
    return temp_air + delta

def constant_series(index: pd.DatetimeIndex, value: float) -> pd.Series:
    return pd.Series(value, index=index, dtype=float)


def build_schedule_series_from_id(
        schedule_id,
        timeline,
        schedule_constant_value=None,
        schedule_compact_map: dict[str, ScheduleCompact] | None = None,
) -> pd.Series:

    if schedule_constant_value:
        return pd.Series(schedule_constant_value, index=timeline)

    if schedule_compact_map:
        return expand_schedule_compact_to_series(
            schedule_id=schedule_id,
            schedule=schedule_compact_map,
            index=timeline,
        )

    raise ValueError(f"Schedule '{schedule_id}' not provided.")


def build_t_ext_series(epw_data: EPWData) -> pd.Series:

    t_ext = epw_data.data["temp_air"]

    return t_ext

def expand_schedule_compact_to_series(
        schedule_id,
        schedule,
        index: pd.DatetimeIndex,
) -> pd.Series:
    if index.empty:
        return pd.Series(dtype=float, index=index)

    data = getattr(schedule, "data", None)
    if data is None:
        raise ValueError(f"scheduleCompact '{schedule_id}' has no data field.")

    fields = [_normalize_compact_field(item.field) for item in data]

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


def make_typology_element(
        element_type: ElementType,
        outside_boundary_condition: str | None = None,
) -> str:

    if element_type in {"Ceiling", "Floor", "Roof", "Wall"}:
        return "Ground" if outside_boundary_condition == "Ground" else "Opaque"

    if element_type in {"Window", "GlassDoor"}:
        return "Window"

    if element_type == "Door":
        return "Opaque"

    raise ValueError(f"Unsupported element type: {element_type!r}")

def _build_elements_for_zone(
        n_nodes: int,
        kappa_array: List[float],
        a_sol_array: List[float],
        h_pli_array: List[float]
) -> List[ConstructionLayer]:

    layers = []
    for i in range(n_nodes):
        h_inner = h_pli_array[i] if i < n_nodes - 1 else None
        h_outer = h_pli_array[i - 1] if i > 0 else None

        layer = ConstructionLayer(
            index=i,
            kappa=kappa_array[i],
            a_sol=a_sol_array[i],
            h_pli_inner=h_inner,
            h_pli_outer=h_outer
        )
        layers.append(layer)

    return layers
