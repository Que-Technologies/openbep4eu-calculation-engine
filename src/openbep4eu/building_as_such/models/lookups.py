from __future__ import annotations
from typing import Optional, Dict, Any
from .definitions import (
    HeatFlowDirection,
    SurfaceTransferCoefficients,
    SideCoefficients,
)


_SURFACE_HT_TABLE: Dict[HeatFlowDirection, SurfaceTransferCoefficients] = {
    HeatFlowDirection.UPWARDS: SurfaceTransferCoefficients(
        direction=HeatFlowDirection.UPWARDS,
        internal=SideCoefficients(h_conv=5.0, h_rad=5.13),
        external=SideCoefficients(h_conv=20.0, h_rad=4.14),
    ),
    HeatFlowDirection.HORIZONTAL: SurfaceTransferCoefficients(
        direction=HeatFlowDirection.HORIZONTAL,
        internal=SideCoefficients(h_conv=2.5, h_rad=5.13),
        external=SideCoefficients(h_conv=20.0, h_rad=4.14),
    ),
    HeatFlowDirection.DOWNWARDS: SurfaceTransferCoefficients(
        direction=HeatFlowDirection.DOWNWARDS,
        internal=SideCoefficients(h_conv=0.7, h_rad=5.13),
        external=SideCoefficients(h_conv=20.0, h_rad=4.14),
    ),
}

def get_construction_layer_ids(construction) -> list[str]:
    return [x for x in [
        construction.outsideLayerId, construction.layer2Id, construction.layer3Id,
        construction.layer4Id, construction.layer5Id, construction.layer6Id,
        construction.layer7Id, construction.layer8Id, construction.layer9Id,
        construction.layer10Id
    ] if x]


def get_convectional_surface_heat_tranfer(direction: HeatFlowDirection) -> SurfaceTransferCoefficients:
    return _SURFACE_HT_TABLE[direction]
