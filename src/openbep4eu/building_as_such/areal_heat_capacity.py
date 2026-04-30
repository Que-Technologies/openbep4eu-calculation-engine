from enum import Enum
from typing import List, Optional, Union

LAMBDA_GR = 2.0
R_GR = 0.5 / LAMBDA_GR

class MassDistribution(str, Enum):
    INTERNAL = "mass concentrated at internal"
    EXTERNAL = "mass concentrated at external"
    DIVIDED = "mass divided over internal and external"
    EQUAL = "mass equally distributed"


def build_kappa_pli_eli(
        n_nodes: int,
        typology: str,
        total_capacity: float,
        construction_class: Union[str, MassDistribution]
) -> List[float]:

    try:
        cc = MassDistribution(construction_class)
    except ValueError:
        valid_options = [e.value for e in MassDistribution]
        raise ValueError(
            f"Invalid construction_class '{construction_class}'. "
            f"Valid options are: {valid_options}"
        )

    kappa_array = [0.0] * n_nodes

    if n_nodes == 2:
        return kappa_array

    km = total_capacity

    if cc == MassDistribution.INTERNAL:
        if typology == "Ground":
            kappa_array[1] = 20000.0
            kappa_array[4] = km
        else:
            kappa_array[4] = km

    elif cc == MassDistribution.EXTERNAL:
        if typology == "Ground":
            kappa_array[2] = km
        else:
            kappa_array[0] = km

    elif cc == MassDistribution.DIVIDED:
        kappa_array[0] = km / 2.0
        kappa_array[4] = km / 2.0

    elif cc == MassDistribution.EQUAL:
        if typology == "Ground":
            kappa_array[2] = km / 4.0
            kappa_array[3] = km / 2.0
            kappa_array[4] = km / 4.0
        else:
            kappa_array[0] = km / 8.0
            kappa_array[1] = km / 4.0
            kappa_array[2] = km / 4.0
            kappa_array[3] = km / 4.0
            kappa_array[4] = km / 8.0

    return kappa_array