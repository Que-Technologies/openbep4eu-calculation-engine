from __future__ import annotations

import numpy as np

from openbep4eu.building_as_such.models.zone_context import ThermalZoneContext


class ZoneStepResult:
    __slots__ = ("phi_hc_nd_act", "theta_int_act", "theta_op_act", "colB_act", "vecB_full")

    def __init__(
            self,
            phi_hc_nd_act: float,
            theta_int_act: float,
            theta_op_act: float,
            colB_act: int,
            vecB_full: np.ndarray,
    ) -> None:
        self.phi_hc_nd_act = phi_hc_nd_act
        self.theta_int_act = theta_int_act
        self.theta_op_act  = theta_op_act
        self.colB_act      = colB_act
        self.vecB_full     = vecB_full


def step_zone(ctx: ThermalZoneContext, t: int) -> ZoneStepResult:
    Theta_H_set = ctx.heat_set_at(t)
    Theta_C_set = ctx.cool_set_at(t)

    ph_t: float = ctx.power_heating_max_at(t)
    pc_t: float = ctx.power_cooling_max_at(t)

    power_heating_max_act: float = 0.0 if Theta_H_set < -995.0 else ph_t
    power_cooling_max_act: float = 0.0 if Theta_C_set >  995.0 else pc_t

    theta_ext_t = ctx.T_ext_at(t)
    phi_int_t   = ctx.Phi_int_at(t)
    phi_sol_t   = float(ctx.Phi_sol_zi[t])
    theta_sup_t = ctx.theta_sup_at(t)
    H_ve_t      = ctx.H_ve_at(t)
    month       = int(ctx.T_ext.index[t].month)

    area_tot    = ctx.area_elements_tot

    Phi_HC_nd_calc = np.zeros(3, dtype=float)
    colB_H = colB_C = 1

    if power_heating_max_act == 0.0 and power_cooling_max_act == 0.0:
        nrHCmodes = 1
    elif power_cooling_max_act == 0.0:
        colB_H    = 1
        nrHCmodes = 2
        Phi_HC_nd_calc[colB_H] = +abs(power_heating_max_act)
    elif power_heating_max_act == 0.0:
        colB_C    = 1
        nrHCmodes = 2
        Phi_HC_nd_calc[colB_C] = power_cooling_max_act
    else:
        nrHCmodes = 3
        colB_H    = 1
        colB_C    = 2
        Phi_HC_nd_calc[colB_H] = +abs(power_heating_max_act)
        Phi_HC_nd_calc[colB_C] = power_cooling_max_act

    Phi_HC_nd_act = 0.0
    Theta_op_act  = 0.0
    Theta_int_act = 0.0
    colB_act      = 0

    rhs_kwargs = dict(
        t=t,
        theta_ext_t=theta_ext_t,
        phi_int_t=phi_int_t,
        phi_sol_t=phi_sol_t,
        theta_sup_t=theta_sup_t,
        H_ve_t=H_ve_t,
        month=month,
    )

    VecB = np.zeros((ctx.Rn, 3), dtype=float)

    for _pass in range(2):

        VecB = ctx.assemble_rhs(Phi_HC_nd_calc=Phi_HC_nd_calc, nrHCmodes=nrHCmodes, **rhs_kwargs)
        VecB = ctx.solve_timestep(VecB, H_ve_t)

        Theta_int_air  = VecB[0, :].copy()
        Theta_int_r_mn = np.zeros(3, dtype=float)
        for element in ctx.elements:
            ri_inner = 1 + element.node_offset + (element.n_nodes - 1)
            Theta_int_r_mn += element.area * VecB[ri_inner, :]
        Theta_int_r_mn /= area_tot
        Theta_int_op = 0.5 * (Theta_int_air + Theta_int_r_mn)

        needs_second_pass = False

        if nrHCmodes > 1:
            if Theta_int_op[0] < Theta_H_set:
                denom = Theta_int_op[colB_H] - Theta_int_op[0]
                Phi_HC_nd_act = (
                        power_heating_max_act * (Theta_H_set - Theta_int_op[0]) / denom
                )
                if Phi_HC_nd_act > power_heating_max_act:
                    Phi_HC_nd_act = power_heating_max_act
                    Theta_op_act  = Theta_int_op[colB_H]
                    Theta_int_act = Theta_int_air[colB_H]
                    colB_act      = colB_H
                else:
                    Phi_HC_nd_calc[0] = Phi_HC_nd_act
                    Theta_op_act      = Theta_H_set
                    Theta_int_act     = Theta_int_air[colB_H]
                    colB_act          = 0
                    nrHCmodes         = 1
                    needs_second_pass = True

            elif Theta_int_op[0] > Theta_C_set:
                denom = Theta_int_op[colB_C] - Theta_int_op[0]
                Phi_HC_nd_act = (
                        power_cooling_max_act * (Theta_C_set - Theta_int_op[0]) / denom
                )
                if Phi_HC_nd_act < power_cooling_max_act:
                    Phi_HC_nd_act = power_cooling_max_act
                    Theta_op_act  = Theta_int_op[colB_C]
                    Theta_int_act = Theta_int_air[colB_C]
                    colB_act      = colB_C
                else:
                    Phi_HC_nd_calc[0] = Phi_HC_nd_act
                    Theta_op_act      = Theta_C_set
                    Theta_int_act     = Theta_int_air[colB_C]
                    colB_act          = 0
                    nrHCmodes         = 1
                    needs_second_pass = True

            else:
                Phi_HC_nd_act = 0.0
                Theta_op_act  = Theta_int_op[0]
                Theta_int_act = Theta_int_air[0]
                colB_act      = 0
        else:
            Phi_HC_nd_act = float(Phi_HC_nd_calc[0])
            Theta_op_act  = Theta_int_op[0]
            Theta_int_act = Theta_int_air[0]
            colB_act      = 0

        if not needs_second_pass:
            break


    ctx.update_state(VecB[:, colB_act])

    return ZoneStepResult(
        phi_hc_nd_act=float(Phi_HC_nd_act),
        theta_int_act=float(Theta_int_act),
        theta_op_act=float(Theta_op_act),
        colB_act=int(colB_act),
        vecB_full=VecB,
    )