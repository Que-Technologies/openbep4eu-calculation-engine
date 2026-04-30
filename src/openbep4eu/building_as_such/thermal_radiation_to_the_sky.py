import numpy as np
import math
from openbep4eu.building_as_such.models.boundary import (
    GroundBoundary,
    AdjacentZoneBoundary,
    ExteriorBoundary
)
from openbep4eu.building_as_such.models.envelope_element import EnvelopeElement


def thermal_radiation_sky(
        zone_id:str,
        zone_elements: list[EnvelopeElement],
        delta_theta_sky: float = 11.0,
) -> np.ndarray:

    sky_factor_elements = []

    for i, elem_id in enumerate(zone_elements):

        if isinstance(elem_id.boundary, GroundBoundary):
            sky_factor_elements.append(0.0)
            continue


        if isinstance(elem_id.boundary, AdjacentZoneBoundary):
            sky_factor_elements.append(0.0)
            continue


        if isinstance(elem_id.boundary, ExteriorBoundary):
            tilt_angle = math.radians(elem_id.tilt_deg)
            sky_view_factor = (1.0 + math.cos(tilt_angle)) / 2.0
            sky_factor_elements.append(sky_view_factor * elem_id.h_re)

        else:
            raise KeyError(f"Unknown ISO element boundary '{type(elem_id.boundary)}'.")

    return np.multiply(sky_factor_elements, delta_theta_sky)