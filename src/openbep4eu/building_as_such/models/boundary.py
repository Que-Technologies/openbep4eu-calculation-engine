from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from openbep4eu.building_as_such.models.zone_context import ThermalZoneContext


@dataclass
class ExteriorBoundary:
    h_ce: float
    h_re: float
    Phi_sky: float

    def conductance_for_matrix(self) -> float:
        return self.h_ce + self.h_re

    def rhs_term(self, theta_ext_t: float, month: int) -> float:
        return (self.h_ce + self.h_re) * theta_ext_t - self.Phi_sky


@dataclass
class GroundBoundary:
    R_gr_ve: float
    Theta_gr_ve: list[float]

    @property
    def conductance(self) -> float:
        return 1.0 / self.R_gr_ve

    def T_ground(self, month: int) -> float:
        return self.Theta_gr_ve[month - 1]

    def conductance_for_matrix(self) -> float:
        return self.conductance

    def rhs_term(self, theta_ext_t: float, month: int) -> float:
        return self.conductance * self.T_ground(month)


@dataclass
class AdjacentZoneBoundary:
    neighbour: "ThermalZoneContext"
    h_ci: float
    h_ri: float

    @property
    def h_total(self) -> float:
        return self.h_ci + self.h_ri

    def conductance_for_matrix(self) -> float:
        return self.h_ci + self.h_ri

    def rhs_term(self, theta_ext_t: float, month: int) -> float:
        return self.h_total * self.neighbour.theta_adj


BoundaryCondition = Union[ExteriorBoundary, GroundBoundary, AdjacentZoneBoundary]