from __future__ import annotations

import numpy as np
from openbep4eu.building_as_such.models.zone_context import ThermalZoneContext
from openbep4eu.building_as_such.models.step_zone import step_zone
from openbep4eu.building_as_such.models.types import EnergySimulationResult
from openbep4eu.building_as_such.models.epw import EPWData


def run_energy_simulation(
        n_zones: int,
        zone_ids: list[str],
        contexts: dict[str, ThermalZoneContext],
        epw_data: EPWData,
) -> tuple[EnergySimulationResult, dict]:

    for ctx in contexts.values():
        ctx.init_state()
        ctx.build_static_matrix()

    timeline = epw_data.data.index
    last_month = epw_data.data.index.month[-1]
    warmup_timesteps = int((epw_data.data.index.month == last_month).sum())
    n_timesteps      = len(timeline) + warmup_timesteps

    Phi_HC   = []
    Theta_int = []
    Theta_op  = []

    for t in range(n_timesteps):
        phi_t   = np.zeros(n_zones, dtype=float)
        t_int_t = np.zeros(n_zones, dtype=float)
        t_op_t  = np.zeros(n_zones, dtype=float)

        for m, zid in enumerate(zone_ids):
            ctx = contexts[zid]

            result = step_zone(ctx=ctx, t=t)

            phi_t[m]   = result.phi_hc_nd_act
            t_int_t[m] = result.theta_int_act
            t_op_t[m]  = result.theta_op_act

        Phi_HC.append(phi_t)
        Theta_int.append(t_int_t)
        Theta_op.append(t_op_t)


    return EnergySimulationResult(
        timeline=epw_data.data.index,
        Phi_HC=np.array(Phi_HC[warmup_timesteps:]),
        Theta_int=np.array(Theta_int[warmup_timesteps:]),
        Theta_op=np.array(Theta_op[warmup_timesteps:]),
    ), contexts