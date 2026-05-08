# engine/definitions.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Literal
import pandas as pd
import numpy as np

LayerKind = Literal["materialOpaque", "materialNoMass", "glazingSimpleSystem"]

class HeatFlowDirection(str, Enum):
    UPWARDS = "upwards"
    HORIZONTAL = "horizontal"
    DOWNWARDS = "downwards"


class SurfaceSide(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"

class OutsideBoundaryCondition(str, Enum):
    ADIABATIC = "Adiabatic"
    GROUND = "Ground"
    OUTDOORS = "Outdoors"
    ZONE = "Zone"

@dataclass(frozen=True)
class SideCoefficients:
    h_conv: float
    h_rad: float


@dataclass(frozen=True)
class SurfaceTransferCoefficients:
    direction: HeatFlowDirection
    internal: SideCoefficients
    external: SideCoefficients

class ScheduleCompactItem:
    field: float | str

class ScheduleCompact:
    id: str
    data: list[ScheduleCompactItem] = []


@dataclass
class MaterialOpaque:
    id: str
    thickness: float
    conductivity: float
    density: float
    specificHeat: float
    thermalAbsorptance: float = 0.9
    solarAbsorptance: float = 0.7
    visibleAbsorptance: float = 0.7

@dataclass
class MaterialNoMass:
    id: str
    thermalResistance: float
    thermalAbsorptance: float = 0.9
    solarAbsorptance: float    = 0.7
    visibleAbsorptance: float    = 0.7

@dataclass
class GlazingSimpleSystem:
    id: str
    uFactor: float
    solarHeatGainCoefficient: float
    visibleTransmittance: float

@dataclass
class MaterialLayerSummary:
    material_id: str
    kind: LayerKind
    thermal_conduction_resistance: float | None = None
    thermal_conduction_capacity: float | None = None
    thermal_conduction_transmittance: float | None = None

@dataclass
class ConstructionSummary:
    construction_id: str
    layers: list[MaterialLayerSummary]
    thermal_conduction_resistance: float
    thermal_conduction_capacity: float
    thermal_conduction_transmittance:float

@dataclass
class GroundTemperatureProperties:
    externalWallsThickness: float
    exposedPerimeter:float
    annualMeanInternalTemperature: float
    amplitudeOfInternalTemperatureVariations: float
    minExternalTemperatureMonth: int
    linearThermalTrasmittance: float
    conductivity: float
    heatCapacity: float

@dataclass
class ZoneSurfaceCoefficients:
    element_id: str
    convective_heat_transfer_coefficients_internal: float
    convective_heat_transfer_coefficients_external: float
    radiative_heat_transfer_coefficients_internal: float
    radiative_heat_transfer_coefficients_external: float
    convective_resistance_internal: float
    convective_resistance_external: float
    radiative_resistance_internal: float
    radiative_resistance_external: float
    total_thermal_resistance: float
    thermal_conduction_resistance: float
    thermal_conduction_capacity: float
    thermal_conduction_transmittance: float

@dataclass
class ZoneSurface:
    zone_id: str
    element_id: str
    first_ground_element: bool
    area: float
    outside_boundary_condition: OutsideBoundaryCondition
    zone_surface_coefficients: ZoneSurfaceCoefficients
    ground_temperature_properties: Optional[GroundTemperatureProperties] = None

@dataclass
class IrradianceTimeseries:
    timestamps: pd.DatetimeIndex
    poa_global_w_m2: np.ndarray
    poa_direct_w_m2: np.ndarray | None = None
    poa_diffuse_w_m2: np.ndarray | None = None

    @classmethod
    def from_poa_df(cls, poa: pd.DataFrame) -> "IrradianceTimeseries":
        if not isinstance(poa.index, pd.DatetimeIndex):
            raise TypeError("poa DataFrame index must be a DatetimeIndex")

        return cls(
            timestamps=poa.index,
            poa_global_w_m2=poa["poa_global"].to_numpy(dtype=float),
            poa_direct_w_m2=poa["poa_direct"].to_numpy(dtype=float) if "poa_direct" in poa.columns else None,
            poa_diffuse_w_m2=poa["poa_diffuse"].to_numpy(dtype=float) if "poa_diffuse" in poa.columns else None,
        )

@dataclass
class SurfaceIrradianceSummary:
    surface_id: str
    surface_type: str

    tilt_deg: float
    azimuth_deg_north0: float

    annual_poa_global_kwh_m2: float
    monthly_poa_global_kwh_m2: dict[str, float]
    peak_poa_global_w_m2: float
    timeseries: IrradianceTimeseries
    peak_timestamp: Optional[pd.Timestamp] = None



