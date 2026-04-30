import pandas as pd
from openbep4eu.utils import constant_series, expand_schedule_compact_to_series

def build_heating_setpoint_series(
        timeline: pd.DatetimeIndex,
        heating_setpoint: float,
        schedule_id: str,
        schedule_constant_value=None,
        schedule_compact_map=None
) -> pd.Series:
    return build_setpoint_series(timeline, heating_setpoint, schedule_id, schedule_constant_value, schedule_compact_map)

def build_cooling_setpoint_series(
        timeline: pd.DatetimeIndex,
        cooling_setpoint: float,
        schedule_id: str,
        schedule_constant_value=None,
        schedule_compact_map=None
) -> pd.Series:
    return build_setpoint_series(timeline, cooling_setpoint, schedule_id, schedule_constant_value, schedule_compact_map)

def build_setpoint_series(
        timeline: pd.DatetimeIndex,
        constant_setpoint: float,
        schedule_id: str,
        schedule_constant_value=None,
        schedule_compact_map=None
) -> pd.Series:
    if (schedule_constant_value is None) == (schedule_compact_map is None):
        raise ValueError(
            "Provide exactly one of schedule_constant_value or schedule_compact_map"
        )

    has_constant = constant_setpoint is not None

    if schedule_constant_value and has_constant and schedule_id:
        return constant_series(timeline, constant_setpoint)

    if schedule_compact_map and schedule_id:
        return expand_schedule_compact_to_series(
            schedule_id=schedule_id,
            schedule=schedule_compact_map,
            index=timeline,
        )

    raise ValueError(f"Heating schedule '{schedule_id}' not found.")