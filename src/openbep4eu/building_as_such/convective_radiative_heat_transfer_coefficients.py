from dataclasses import dataclass
from openbep4eu.building_as_such.models.lookups import get_convectional_surface_heat_tranfer, HeatFlowDirection
@dataclass
class ElementCoefficients:
    h_ci: float
    h_ri: float
    h_ce: float
    h_re: float

def get_surface_coefficients(tilt_deg: float) -> ElementCoefficients:

    if tilt_deg < 45.0:
        direction = HeatFlowDirection.UPWARDS
    elif tilt_deg > 135.0:
        direction = HeatFlowDirection.DOWNWARDS
    else:
        direction = HeatFlowDirection.HORIZONTAL

    table_data = get_convectional_surface_heat_tranfer(direction)

    return ElementCoefficients(
        h_ci=table_data.internal.h_conv,
        h_ri=table_data.internal.h_rad,
        h_ce=table_data.external.h_conv,
        h_re=table_data.external.h_rad
    )