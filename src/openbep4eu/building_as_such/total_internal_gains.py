import pandas as pd
from typing import Optional


def calculate_zone_phi_int(
        q_int_occ: Optional[pd.Series] = None,
        q_int_a: Optional[pd.Series] = None,
        q_int_l: Optional[pd.Series] = None,
        a_use: Optional[float] = None,
) -> pd.Series:


    if a_use is None or a_use <= 0:
        raise ValueError("Floor area must be explicitly provided and greater than zero for Phi_int calculation.")


    internal_gains = [
        series for series in (q_int_occ, q_int_a, q_int_l)
        if series is not None
    ]

    if not internal_gains:
        raise ValueError("At least one heat gain series (q_int_occ, q_int_a, or q_int_l) must be provided.")

    total_internal_gains = sum(internal_gains)

    phi_int = total_internal_gains * a_use

    return phi_int