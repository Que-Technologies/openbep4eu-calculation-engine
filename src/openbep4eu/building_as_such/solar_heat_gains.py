import pandas as pd

def calculate_zone_phi_sol(
        areas: list[float],
        tau_sol_eli: list[float],
        irradiances: list[pd.Series],
) -> pd.Series:

    n = len(areas)
    if len(tau_sol_eli) != n or len(irradiances) != n:
        raise ValueError(
            f"areas, tau_sol_eli and irradiances must all have the same length "
            f"(got {len(areas)}, {len(tau_sol_eli)}, {len(irradiances)})."
        )
    if n == 0:
        raise ValueError("At least one element must be provided.")

    timeline = irradiances[0].index

    for i, irr in enumerate(irradiances[1:], start=1):
        if not irr.index.equals(timeline):
            raise ValueError(
                f"irradiances[{i}] has a different index than irradiances[0]."
            )


    phi_sol = pd.Series(0.0, index=timeline)

    for area, tau, irr in zip(areas, tau_sol_eli, irradiances):
        if tau == 0.0:
            continue
        phi_sol = phi_sol + tau * area * irr.fillna(0.0)

    return phi_sol