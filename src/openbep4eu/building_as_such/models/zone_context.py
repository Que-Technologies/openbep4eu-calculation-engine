
from __future__ import annotations
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from openbep4eu.building_as_such.models.envelope_element import EnvelopeElement, DTIME_S


@dataclass
class ThermalZoneContext:
    zone_id: str

    elements: list[EnvelopeElement] = field(default_factory=list)

    a_use: float = 0.0
    c_int_per_A_us: float = 0.0

    power_heating_max: pd.Series = field(default_factory=pd.Series)
    power_cooling_max: pd.Series = field(default_factory=pd.Series)

    thermal_bridge_heat: float = 0.0   # H_TB [W/K]

    H_ve: pd.Series    = field(default_factory=pd.Series)   # [W/K]
    heat_sets: pd.Series = field(default_factory=pd.Series) # [°C]
    cool_sets: pd.Series = field(default_factory=pd.Series) # [°C]
    theta_sup: pd.Series = field(default_factory=pd.Series) # [°C]
    Phi_int: pd.Series   = field(default_factory=pd.Series) # [W]
    Phi_sol_zi: list[float] = field(default_factory=list)   # [W] per timestep

    f_int_c: float = 0.4
    f_sol_c: float = 0.4
    f_H_c:   float = 0.4
    f_C_c:   float = 0.4

    T_ext: pd.Series = field(default_factory=pd.Series)  # [°C]

    Rn: int = 0
    Pln:    list[int] = field(default_factory=list)
    PlnSum: list[int] = field(default_factory=list)


    theta_adj:  float       = 20.0
    theta_node: np.ndarray  = field(default_factory=lambda: np.array([], dtype=float))

    _MatA_base: np.ndarray | None = field(default=None, repr=False)

    @property
    def bui_eln(self) -> int:
        return len(self.elements)

    @property
    def area_elements_tot(self) -> float:
        return float(sum(e.area for e in self.elements))

    @property
    def C_int(self) -> float:
        return self.c_int_per_A_us * self.a_use

    @property
    def Ah_ci(self) -> float:
        return float(sum(e.area * e.h_ci for e in self.elements))

    @property
    def h_ri_mn(self) -> float:
        return float(
            sum(e.area * e.h_ri for e in self.elements) / self.area_elements_tot
        )

    def T_ext_at(self, t: int) -> float:
        return float(self.T_ext.iloc[t])

    def H_ve_at(self, t: int) -> float:
        return float(self.H_ve.iloc[t])

    def theta_sup_at(self, t: int) -> float:
        return float(self.theta_sup.iloc[t])

    def Phi_int_at(self, t: int) -> float:
        return float(self.Phi_int.iloc[t])

    def heat_set_at(self, t: int) -> float:
        return float(self.heat_sets.iloc[t])

    def cool_set_at(self, t: int) -> float:
        return float(self.cool_sets.iloc[t])

    def power_heating_max_at(self, t: int) -> float:
        s = self.power_heating_max
        return float(s.iloc[t]) if hasattr(s, "iloc") else float(s)

    def power_cooling_max_at(self, t: int) -> float:
        s = self.power_cooling_max
        return float(s.iloc[t]) if hasattr(s, "iloc") else float(s)

    def finalise(self) -> None:
        self.Pln    = [e.n_nodes for e in self.elements]
        self.PlnSum = []
        cumulative  = 0
        for e in self.elements:
            self.PlnSum.append(cumulative)
            e.node_offset = cumulative
            cumulative   += e.n_nodes
        self.Rn        = 1 + sum(self.Pln)   # +1 for zone-air node (row 0)
        self.theta_node = 20.0 * np.ones(self.Rn, dtype=float)

    def build_static_matrix(self) -> None:

        Rn       = self.Rn
        area_tot = self.area_elements_tot
        h_ri_mn  = self.h_ri_mn
        H_TB     = self.thermal_bridge_heat

        MatA = np.zeros((Rn, Rn), dtype=float)

        MatA[0, 0] = self.C_int / DTIME_S + self.Ah_ci + H_TB

        for element in self.elements:
            element.add_to_matrix(MatA, area_tot, h_ri_mn)

        for element in self.elements:
            ri_inner = 1 + element.node_offset + (element.n_nodes - 1)
            for other in self.elements:
                ck = 1 + other.node_offset + (other.n_nodes - 1)
                MatA[ri_inner, ck] -= (other.area / area_tot) * other.h_ri

        self._MatA_base = MatA


    def assemble_rhs(
            self,
            t: int,
            Phi_HC_nd_calc: np.ndarray,
            nrHCmodes: int,
            theta_ext_t: float,
            phi_int_t: float,
            phi_sol_t: float,
            theta_sup_t: float,
            H_ve_t: float,
            month: int,
    ) -> np.ndarray:

        Rn       = self.Rn
        area_tot = self.area_elements_tot
        f_int_c  = self.f_int_c
        f_sol_c  = self.f_sol_c
        f_H_c    = self.f_H_c
        f_C_c    = self.f_C_c
        C_int    = self.C_int
        H_TB     = self.thermal_bridge_heat

        VecB = np.zeros((Rn, 3), dtype=float)

        for cBi in range(nrHCmodes):
            Phi_col = Phi_HC_nd_calc[cBi]
            f_HC_c  = f_H_c if Phi_col > 0.0 else f_C_c

            VecB[0, cBi] = (
                    H_TB    * theta_ext_t
                    + H_ve_t  * theta_sup_t
                    + f_int_c * phi_int_t
                    + f_sol_c * phi_sol_t
                    + (C_int / DTIME_S) * self.theta_node[0]
                    + f_HC_c  * Phi_col
            )

            for element in self.elements:
                b_elem = element.rhs_contribution(
                    t=t,
                    theta_node=self.theta_node,
                    phi_int_t=phi_int_t,
                    phi_sol_t=phi_sol_t,
                    theta_ext_t=theta_ext_t,
                    area_tot=area_tot,
                    f_int_c=f_int_c,
                    f_sol_c=f_sol_c,
                    Phi_HC_col=Phi_col,
                    f_HC_c=f_HC_c,
                    month=month,
                )
                start = 1 + element.node_offset
                VecB[start : start + element.n_nodes, cBi] += b_elem

        return VecB

    def solve_timestep(self, VecB: np.ndarray, H_ve_t: float) -> np.ndarray:
        MatA = self._MatA_base.copy()
        MatA[0, 0] += H_ve_t
        return np.linalg.solve(MatA, VecB)


    def init_state(self) -> None:
        self.theta_adj  = 20.0
        self.theta_node = 20.0 * np.ones(self.Rn, dtype=float)

    def update_state(self, theta_node_new: np.ndarray) -> None:
        self.theta_node = theta_node_new.copy()
        self.theta_adj  = float(theta_node_new[0])