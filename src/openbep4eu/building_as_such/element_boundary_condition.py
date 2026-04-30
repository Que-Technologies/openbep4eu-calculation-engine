from __future__ import annotations

from openbep4eu.building_as_such.models.boundary import (
    ExteriorBoundary,
    GroundBoundary,
    AdjacentZoneBoundary,
    BoundaryCondition
)

def create_boundary_condition(
        boundary_type: str,
        h_ce: float,
        h_re: float,
        h_ci: float,
        h_ri: float,
        phi_sky: float,
        r_gr_ve: float,
        theta_gr_ve: list[float],
) -> "BoundaryCondition":

    if boundary_type == "Outdoors":
        return ExteriorBoundary(
            h_ce=h_ce,
            h_re=h_re,
            Phi_sky=phi_sky
        )

    elif boundary_type == "Ground":
        return GroundBoundary(
            R_gr_ve=r_gr_ve,
            Theta_gr_ve=list(theta_gr_ve)
        )

    elif boundary_type == "Zone":
        return AdjacentZoneBoundary(
            neighbour=None,
            h_ci=h_ci,
            h_ri=h_ri
        )

    elif boundary_type == "Adiabatic":
        return ExteriorBoundary(
            h_ce=0.0,
            h_re=0.0,
            Phi_sky=0.0
        )

    else:
        raise ValueError(
            f"Unknown outsideBoundaryCondition value: '{boundary_type}'. "
            f"Expected one of: 'Outdoors', 'Ground', 'Zone', 'Adiabatic'."
        )