import pandas as pd
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass
from openbep4eu.utils import build_schedule_series_from_id


class OccupancyMethod(str, Enum):
    PEOPLE = "People"
    PEOPLE_PER_AREA = "People/Area"
    AREA_PER_PERSON = "Area/Person"


@dataclass
class PeopleConfig:
    numberOfPeopleCalculationMethod: OccupancyMethod
    numberOfPeopleSchedule: Optional[str] = None
    activityLevelSchedule: Optional[str] = None
    numberOfPeople: Optional[float] = None
    peoplePerFloorArea: Optional[float] = None
    floorAreaPerPerson: Optional[float] = None



def get_people_density_factor(config: PeopleConfig, floor_area: Optional[float] = None) -> float:

    if floor_area <= 0:
        raise ValueError("Floor area must be greater than zero for occupancy calculations.")

    method = config.numberOfPeopleCalculationMethod

    if method == OccupancyMethod.PEOPLE:
        if config.numberOfPeople is None:
            raise ValueError(f"Method is {method.value} but numberOfPeople is missing.")
        return config.numberOfPeople / floor_area

    elif method == OccupancyMethod.PEOPLE_PER_AREA:
        if config.peoplePerFloorArea is None:
            raise ValueError(f"Method is {method.value} but peoplePerFloorArea is missing.")
        return config.peoplePerFloorArea

    elif method == OccupancyMethod.AREA_PER_PERSON:
        if not config.floorAreaPerPerson:
            raise ValueError(f"Method is {method.value} but floorAreaPerPerson is missing or zero.")
        return 1.0 / config.floorAreaPerPerson

    else:
        raise ValueError(f"Unsupported calculation method '{method}'.")


def calculate_single_occupancy_heat_gain(
        people: PeopleConfig,
        timeline: pd.DatetimeIndex,
        floor_area: Optional[float] = None,
        occ_schedule_constant_value: Optional[float] = None,
        occ_schedule_compact_object: Optional[Any] = None,
        act_schedule_constant_value: Optional[float] = None,
        act_schedule_compact_object: Optional[Any] = None,
) -> pd.Series:

    people_factor = get_people_density_factor(config=people, floor_area=floor_area)

    occ_schedule = build_schedule_series_from_id(
        schedule_id=people.numberOfPeopleSchedule,
        timeline=timeline,
        schedule_constant_value=occ_schedule_constant_value,
        schedule_compact_map=occ_schedule_compact_object,
    )

    act_schedule = build_schedule_series_from_id(
        schedule_id=people.activityLevelSchedule,
        timeline=timeline,
        schedule_constant_value=act_schedule_constant_value,
        schedule_compact_map=act_schedule_compact_object,
    )

    return occ_schedule * act_schedule * people_factor