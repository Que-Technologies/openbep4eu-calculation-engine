from enum import Enum
from typing import List, Optional, Union

LAMBDA_GR = 2.0
R_GR = 0.5 / LAMBDA_GR

def build_h_pli_eli(
        n_nodes: int,
        typology: str,
        total_resistance: float,
        R_eff: Optional[float] = None
) -> List[float]:

    if n_nodes == 2:
        return [1.0 / total_resistance] if total_resistance != 0 else [0.0]

    h_pli_array = [0.0] * 4

    if total_resistance == 0:
        return h_pli_array

    if typology == "Opaque":
        h_pli_array[0] = 6.0 / total_resistance
        h_pli_array[1] = 3.0 / total_resistance
        h_pli_array[2] = 3.0 / total_resistance
        h_pli_array[3] = 6.0 / total_resistance

    elif typology == "Ground" and R_eff is not None:
        h_pli_array[0] = 2.0 / R_GR
        h_pli_array[1] = 1.0 / (R_eff / 4.0 + R_GR / 2.0)
        h_pli_array[2] = 2.0 / R_eff
        h_pli_array[3] = 4.0 / R_eff

    return h_pli_array