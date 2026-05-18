import numpy as np
import math

def thermal_radiation_sky(
        element_id: str,
        boundary: str,
        tilt_deg: float,
        h_re: float,
        delta_theta_sky: float = 11.0,
) -> float:
    if boundary=='Ground' or boundary=='Zone' or boundary=='Adiabatic':
        sky_factor = 0.0
    elif boundary=='Outdoors':
        tilt_rad = math.radians(tilt_deg)
        phi_sky = (1.0 + math.cos(tilt_rad)) / 2.0
        sky_factor = phi_sky
    else:
        raise KeyError(
            f"Unknown ISO element boundary for element_id '{element_id}': {type(boundary)}"
        )

    return sky_factor * h_re * delta_theta_sky