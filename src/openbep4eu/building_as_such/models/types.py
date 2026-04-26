# ISO 52016 internal dataclasses (calculator-internal, not schema models)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Sequence

import numpy as np
import pandas as pd

@dataclass(frozen=True)
class ZoneStatic:
    zone_index: int
    bui_eln: int
    area_elements_tot: float
    C_int: float
    Ah_ci: float
    h_ri_mn: float

@dataclass
class ZoneState:
    t_index: int
    theta_adj: np.ndarray
    theta_old_zone: List[np.ndarray]

@dataclass(frozen=True)
class ZoneStepOutputs:
    phi_hc_nd_act: float
    theta_int_act: float
    theta_op_act: float
    colB_act: int
    vecB_full: np.ndarray


@dataclass
class SimulationOutput:
    Phi_HC_nd_act: np.ndarray
    Theta_int_act: np.ndarray
    Theta_op_act: np.ndarray
    theta_adj: np.ndarray
    Theta_old_zone: List[np.ndarray]

@dataclass
class EnergySimulationResult:
    timeline: pd.DatetimeIndex
    Phi_HC: np.ndarray
    Theta_int: np.ndarray
    Theta_op: np.ndarray