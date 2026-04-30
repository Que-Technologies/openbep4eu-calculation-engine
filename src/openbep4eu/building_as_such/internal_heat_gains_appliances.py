import pandas as pd
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass
from openbep4eu.utils import build_schedule_series_from_id


class DesignLevelMethod(str, Enum):
    EQUIPMENT_LEVEL = "EquipmentLevel"
    POWER_PER_AREA = "Power/Area"


@dataclass
class EquipmentConfig:
    designLevelCalculationMethod: DesignLevelMethod
    fuelType: str
    schedule: Optional[str] = None
    designLevel: Optional[float] = None
    powerPerFloorArea: Optional[float] = None


def get_equipment_power_density(config: EquipmentConfig, floor_area: Optional[float] = None) -> float:

    if floor_area is None or floor_area <= 0:
        raise ValueError("Floor area must be explicitly provided and greater than zero for equipment calculations.")

    method = config.designLevelCalculationMethod

    if method == DesignLevelMethod.EQUIPMENT_LEVEL:
        if config.designLevel is None:
            raise ValueError(f"Method is {method.value} but designLevel is missing.")
        return config.designLevel / floor_area

    elif method == DesignLevelMethod.POWER_PER_AREA:
        if config.powerPerFloorArea is None:
            raise ValueError(f"Method is {method.value} but powerPerFloorArea is missing.")
        return config.powerPerFloorArea

    else:
        raise ValueError(f"Unsupported calculation method '{method}'.")


def calculate_single_equipment_heat_gain(
        equipment: EquipmentConfig,
        timeline: pd.DatetimeIndex,
        floor_area: Optional[float] = None,
        schedule_constant_value: Optional[float] = None,
        schedule_compact_map: Optional[dict[str, Any]] = None,
) -> pd.Series:

    excluded_fuel_types = {
        "Electricity Appliances",
        "Artificial Lighting",
    }

    if equipment.fuelType in excluded_fuel_types:
        return pd.Series(0.0, index=timeline)

    power_density = get_equipment_power_density(config=equipment, floor_area=floor_area)

    sched = build_schedule_series_from_id(
        schedule_id=equipment.schedule,
        timeline=timeline,
        schedule_constant_value=schedule_constant_value,
        schedule_compact_map=schedule_compact_map,
    )

    return sched * power_density