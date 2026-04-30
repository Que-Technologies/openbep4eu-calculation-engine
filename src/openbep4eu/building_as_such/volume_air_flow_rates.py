def compute_air_changes_per_hour(air_changes_per_hour:float,zone_volume:float):
    return air_changes_per_hour * zone_volume

def compute_air_flow_rate_per_floor_area(flow_rate_per_floor_area:float):
    return flow_rate_per_floor_area

def compute_air_flow_rate_per_zone(flow_rate:float,float_area:float):
    return flow_rate / float_area