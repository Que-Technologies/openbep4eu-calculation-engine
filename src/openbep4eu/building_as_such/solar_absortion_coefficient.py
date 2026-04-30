from typing import List, Optional, Union
from openbep4eu.building_as_such.models.boundary import BoundaryCondition, ExteriorBoundary

def build_a_sol_pli_eli(
        n_nodes: int,
        boundary_condition: BoundaryCondition,
        material_solar_absorptance: float
) -> List[float]:

    a_sol_array = [0.0] * n_nodes
    if isinstance(boundary_condition, ExteriorBoundary) and n_nodes == 5:
        a_sol_array[0] = material_solar_absorptance
    return a_sol_array