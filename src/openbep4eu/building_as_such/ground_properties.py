import pandas as pd
import numpy as np
from openbep4eu.building_as_such.models.definitions import ZoneSurface, OutsideBoundaryCondition

def contact_with_ground_calculations_for_zone(
        zone_id: str,
        zone_surfaces: list[ZoneSurface],
        theta_sup: pd.Series,
) -> tuple[np.ndarray, float, float]:

    ground_surfaces = [
        s for s in zone_surfaces
        if s.outside_boundary_condition == OutsideBoundaryCondition.GROUND
    ]

    if not ground_surfaces:
        Theta_gr_ve = np.zeros(12, dtype=float)
        R_gr_ve = 0.0
        R_eff = 6.0465
        return Theta_gr_ve, R_gr_ve, R_eff

    first_ground_element = next(
        (s for s in ground_surfaces if s.first_ground_element), None
    )

    if first_ground_element is None:
        raise ValueError(
            f"Zone '{zone_id}': no surface flagged as first_ground_element."
        )

    gtcp = first_ground_element.ground_temperature_properties
    if gtcp is None:
        raise ValueError(
            f"Ground temperature properties not found for surface '{first_ground_element.element_id}'."
        )

    psi_k = gtcp.linearThermalTrasmittance
    periodic_penetration_depth = 3.2

    amplitude_of_internal_temperature_variations = gtcp.amplitudeOfInternalTemperatureVariations
    amplitude_of_external_temperature_variations = (theta_sup.iloc[:, 0].resample("ME").max() - theta_sup.iloc[:, 0].resample("ME").min()).mean() / 2

    lambda_gr = gtcp.conductivity
    R_gr = 0.5 / lambda_gr

    external_temperature_monthly_averages = theta_sup.iloc[:, 0].resample("ME").mean()
    annual_mean_external_temperature = external_temperature_monthly_averages.mean()

    annual_mean_internal_temperature = gtcp.annualMeanInternalTemperature

    coldest_month = gtcp.minExternalTemperatureMonth

    internal_temperature_by_month = np.zeros(12, dtype=float)
    for month in range(12):
        internal_temperature_by_month[month] = (
                annual_mean_internal_temperature
                - amplitude_of_internal_temperature_variations
                * np.cos(2 * np.pi * (month + 1 - coldest_month) / 12)
        )

    wall_thickness_for_ground = gtcp.externalWallsThickness

    exposed_perimeter = gtcp.exposedPerimeter

    sog_area = first_ground_element.area
    characteristic_floor_dimension = sog_area / (0.5 * exposed_perimeter)

    surface_heat_transfer_result = first_ground_element.zone_surface_coefficients

    thermal_resistance_floor = surface_heat_transfer_result.thermal_conduction_resistance
    R_si = (surface_heat_transfer_result.convective_resistance_internal*surface_heat_transfer_result.radiative_resistance_internal)/(surface_heat_transfer_result.convective_resistance_internal+surface_heat_transfer_result.radiative_resistance_internal)
    R_se = 0

    equivalent_ground_thickness = wall_thickness_for_ground + lambda_gr * (
            thermal_resistance_floor + R_si + R_se
    )

    if equivalent_ground_thickness < characteristic_floor_dimension:
        U_sog = (
                2
                * lambda_gr
                / (np.pi * characteristic_floor_dimension + equivalent_ground_thickness)
                * np.log(np.pi * characteristic_floor_dimension / equivalent_ground_thickness + 1)
        )
    else:
        U_sog = lambda_gr / (
                0.457 * characteristic_floor_dimension + equivalent_ground_thickness
        )

    R_gr_ve = 1.0 / U_sog - R_si - thermal_resistance_floor - R_gr

    steady_state_heat_transfer_coefficient = sog_area * U_sog + exposed_perimeter * psi_k

    H_pi = (
            sog_area
            * lambda_gr
            / equivalent_ground_thickness
            * np.sqrt(2 / ( (1 + periodic_penetration_depth / equivalent_ground_thickness) ** 2 + 1
        )
    )
    )

    H_pe = (
            0.37
            * exposed_perimeter
            * lambda_gr
            * np.log(periodic_penetration_depth / equivalent_ground_thickness + 1)
    )

    annual_average_heat_flow_rate = steady_state_heat_transfer_coefficient * (
            annual_mean_internal_temperature - annual_mean_external_temperature
    )

    periodic_heat_flow_due_to_internal_temperature_variation = np.zeros(12, dtype=float)
    a_tl = 0
    for month in range(12):
        periodic_heat_flow_due_to_internal_temperature_variation[month] = (
                -H_pi
                * amplitude_of_internal_temperature_variations
                * np.cos(2 * np.pi * (month + 1 - coldest_month + a_tl) / 12)
        )

    periodic_heat_flow_due_to_external_temperature_variation = np.zeros(12, dtype=float)
    b_tl = 1
    for month in range(12):
        periodic_heat_flow_due_to_external_temperature_variation[month] = (
                H_pe
                * amplitude_of_external_temperature_variations
                * np.cos(
            2 * np.pi * (month + 1 - coldest_month - b_tl) / 12)
        )

    average_heat_flow_rate = (
            annual_average_heat_flow_rate
            + periodic_heat_flow_due_to_internal_temperature_variation
            + periodic_heat_flow_due_to_external_temperature_variation
    )

    Theta_gr_ve = internal_temperature_by_month - (
            average_heat_flow_rate
            - exposed_perimeter
            * psi_k
            * (annual_mean_internal_temperature - annual_mean_external_temperature)
    ) / (sog_area * U_sog)

    R_eff = 1.0 / U_sog - R_si

    return Theta_gr_ve, R_gr_ve, R_eff