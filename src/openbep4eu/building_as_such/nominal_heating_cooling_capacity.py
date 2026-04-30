import pandas as pd
from openbep4eu.utils import build_schedule_series_from_id

def get_zone_power_limits(
        zone_id: str,
        max_heating_power: float,
        max_cooling_power: float,
        timeline: pd.DatetimeIndex,
        schedule_id: str,
        schedule_constant_value=None,
        schedule_compact_map=None,
) -> tuple[list[pd.Series], list[pd.Series]]:
    power_heating_max = []
    power_cooling_max = []

    if (schedule_constant_value is None) == (schedule_compact_map is None):
        raise ValueError(
            "Provide exactly one of schedule_constant_value or schedule_compact_map"
        )

    avail = build_schedule_series_from_id(
        schedule_id=schedule_id,
        timeline=timeline,
        schedule_constant_value=schedule_constant_value,
        schedule_compact_map=schedule_compact_map,
    )

    max_heat = 0.0 if max_heating_power is None else float(max_heating_power)
    max_cool = 0.0 if max_cooling_power is None else float(max_cooling_power)

    power_heating_max.append(avail * max_heat)
    power_cooling_max.append(avail * (-max_cool))

    return power_heating_max, power_cooling_max

