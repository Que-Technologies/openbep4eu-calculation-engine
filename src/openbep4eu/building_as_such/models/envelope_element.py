from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from openbep4eu.building_as_such.models.boundary import BoundaryCondition

DTIME_S = 3600.0


@dataclass
class ConstructionLayer:
    index: int
    kappa: float
    h_pli_inner: float | None
    h_pli_outer: float | None
    a_sol: float

    @property
    def is_outermost(self) -> bool:
        return self.h_pli_outer is None

    @property
    def is_innermost(self) -> bool:
        return self.h_pli_inner is None


@dataclass
class EnvelopeElement:
    element_id: str
    surface_type: str
    area: float
    tilt_deg: float
    azimuth_deg: float

    h_ci: float
    h_ri: float
    h_ce: float
    h_re: float

    boundary: "BoundaryCondition"

    irradiance: list[float]

    layers: list[ConstructionLayer] = field(default_factory=list)

    node_offset: int = 0

    @property
    def n_nodes(self) -> int:
        return len(self.layers)

    def irradiance_at(self, t: int) -> float:
        return self.irradiance[t]

    def add_to_matrix(
            self,
            MatA: np.ndarray,
            area_tot: float,
            h_ri_mn: float,
    ) -> None:

        for layer in self.layers:
            ci = 1 + self.node_offset + layer.index

            MatA[ci, ci] += layer.kappa / DTIME_S

            if layer.h_pli_outer is not None:
                MatA[ci, ci]     += layer.h_pli_outer
                MatA[ci, ci - 1] -= layer.h_pli_outer
            if layer.h_pli_inner is not None:
                MatA[ci, ci]     += layer.h_pli_inner
                MatA[ci, ci + 1] -= layer.h_pli_inner


            if layer.is_innermost:

                MatA[ci, ci] += self.h_ci
                MatA[ci, 0]  -= self.h_ci

                MatA[0, ci]  -= self.area * self.h_ci

                MatA[ci, ci] += h_ri_mn

            elif layer.is_outermost:
                MatA[ci, ci] += self.boundary.conductance_for_matrix()


    def rhs_contribution(
            self,
            t: int,
            theta_node: np.ndarray,
            phi_int_t: float,
            phi_sol_t: float,
            theta_ext_t: float,
            area_tot: float,
            f_int_c: float,
            f_sol_c: float,
            Phi_HC_col: float,
            f_HC_c: float,
            month: int,
    ) -> np.ndarray:

        b = np.zeros(self.n_nodes, dtype=float)
        irr_t = self.irradiance_at(t)

        for layer in self.layers:
            li = layer.index   # local index 0..n_nodes-1
            global_ri = 1 + self.node_offset + li


            b[li] += layer.a_sol * irr_t + (layer.kappa / DTIME_S) * theta_node[global_ri]

            if layer.is_innermost:

                b[li] += (
                                 (1.0 - f_int_c) * phi_int_t
                                 + (1.0 - f_sol_c) * phi_sol_t
                                 + (1.0 - f_HC_c) * Phi_HC_col
                         ) / area_tot

            elif layer.is_outermost:

                b[li] += self.boundary.rhs_term(theta_ext_t, month)

        return b