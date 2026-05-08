from dataclasses import dataclass
from openbep4eu.building_as_such.models.lookups import get_convectional_surface_heat_tranfer, HeatFlowDirection
from openbep4eu.building_as_such.models.definitions import ZoneSurfaceCoefficients, ConstructionSummary

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

def compute_surface_heat_transfer(element_id:str, outside_boundary_condition:str, coefficients: ElementCoefficients, conduction_summary: ConstructionSummary) -> ZoneSurfaceCoefficients:


    convective_resistance_internal = 1/coefficients.h_ci
    convective_resistance_external = 1/coefficients.h_ce
    radiative_resistance_internal = 1/coefficients.h_ri
    radiative_resistance_external = 1/coefficients.h_re


    if outside_boundary_condition == 'Outdoors':
        total_thermal_resistance = (convective_resistance_internal*radiative_resistance_internal)/(convective_resistance_internal+radiative_resistance_internal)+(convective_resistance_external*radiative_resistance_external)/(convective_resistance_external+radiative_resistance_external)+conduction_summary.thermal_conduction_capacity
    elif outside_boundary_condition == 'Zone':
        total_thermal_resistance = 2*(convective_resistance_internal*radiative_resistance_internal)/(convective_resistance_internal+radiative_resistance_internal)+conduction_summary.thermal_conduction_capacity
    elif outside_boundary_condition == 'Adiabatic':
        total_thermal_resistance = conduction_summary.thermal_conduction_capacity
    elif outside_boundary_condition == 'Ground':
        total_thermal_resistance = (convective_resistance_internal*radiative_resistance_internal)/(convective_resistance_internal+radiative_resistance_internal)+conduction_summary.thermal_conduction_capacity
    else:
        raise ValueError(f"Unsupported outsideBoundaryCondition: {outside_boundary_condition}")

    return ZoneSurfaceCoefficients(
        element_id=element_id,
        convective_heat_transfer_coefficients_internal=coefficients.h_ci,
        convective_heat_transfer_coefficients_external=coefficients.h_ce,
        radiative_heat_transfer_coefficients_internal=coefficients.h_ri,
        radiative_heat_transfer_coefficients_external=coefficients.h_re,
        convective_resistance_internal=convective_resistance_internal,
        convective_resistance_external=convective_resistance_external,
        radiative_resistance_internal=radiative_resistance_internal,
        radiative_resistance_external=radiative_resistance_external,
        total_thermal_resistance=total_thermal_resistance,
        thermal_conduction_resistance=conduction_summary.thermal_conduction_resistance,
        thermal_conduction_capacity=conduction_summary.thermal_conduction_capacity,
        thermal_conduction_transmittance=conduction_summary.thermal_conduction_transmittance
    )