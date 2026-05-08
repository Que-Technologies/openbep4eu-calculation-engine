from openbep4eu.building_as_such.models.definitions import ConstructionSummary,MaterialLayerSummary,MaterialOpaque,MaterialNoMass,GlazingSimpleSystem
from typing import Union

MaterialType = Union[MaterialOpaque, MaterialNoMass, GlazingSimpleSystem]

def construction_thermal_conduction(construction_id: str, material_list: list[MaterialType]) -> ConstructionSummary:

    calculated_layers = []
    for material in material_list:
        if isinstance(material, MaterialOpaque):
            calculated_layers.append(calculate_opaque(material))
        elif isinstance(material, MaterialNoMass):
            calculated_layers.append(calculate_nomass(material))
        elif isinstance(material, GlazingSimpleSystem):
            calculated_layers.append(calculate_glazing(material))
        else:
            raise Exception(f"Unsupported material type: {type(material).__name__}")

    total_thermal_conduction_resistance = sum(l.thermal_conduction_resistance for l in calculated_layers) if calculated_layers else 0.0
    total_thermal_conduction_capacity = sum(l.thermal_conduction_capacity for l in calculated_layers) if calculated_layers else 0.0

    return ConstructionSummary(
        construction_id=construction_id,layers=calculated_layers, thermal_conduction_resistance=total_thermal_conduction_resistance,
        thermal_conduction_capacity=total_thermal_conduction_capacity,
        thermal_conduction_transmittance=1 / total_thermal_conduction_resistance
    )

def calculate_opaque(m: MaterialOpaque) -> MaterialLayerSummary:
    resistance = opaque_thermal_resistance(m.thickness, m.conductivity)
    capacity = opaque_thermal_capacity(m.thickness,m.density,m.specificHeat)
    return MaterialLayerSummary(
        material_id=m.id, kind="materialOpaque",
        thermal_conduction_resistance=resistance, thermal_conduction_capacity=capacity,
        thermal_conduction_transmittance=1 / resistance
    )

def calculate_nomass(m: MaterialNoMass) -> MaterialLayerSummary:
    resistance = no_mass_thermal_resistance(m.thermalResistance)
    capacity = no_mass_thermal_capacity()
    return MaterialLayerSummary(
        material_id=m.id, kind="materialNoMass",
        thermal_conduction_resistance=resistance, thermal_conduction_capacity=capacity,
        thermal_conduction_transmittance=1 / resistance
    )

def calculate_glazing(m: GlazingSimpleSystem) -> MaterialLayerSummary:
    resistance = glazing_simple_thermal_resistance(m.uFactor)
    capacity = glazing_simple_thermal_capacity()
    return MaterialLayerSummary(
        material_id=m.id, kind="glazingSimpleSystem",
        thermal_conduction_resistance=resistance, thermal_conduction_capacity=capacity,
        thermal_conduction_transmittance=1 / resistance
    )


def opaque_thermal_resistance(thickness: float, conductivity: float) -> float:
    return thickness / conductivity

def no_mass_thermal_resistance(thermal_resistance: float) -> float:
    return thermal_resistance

def glazing_simple_thermal_resistance(u_factor: float) -> float:
    return 1/u_factor

# THERMAL CAPACITY
def opaque_thermal_capacity(thickness: float, density: float, specific_heat: float) -> float:
    return thickness * density * specific_heat

def no_mass_thermal_capacity() -> float:
    return 0

def glazing_simple_thermal_capacity() -> float:
    return 0

# THERMAL CAPACITY
def thermal_transmittance(thermal_resistance: float) -> float:
    return 1/thermal_resistance