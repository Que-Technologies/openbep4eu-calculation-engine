import pandas as pd

def get_zone_h_ve(air_flow_rate:float,c_air:float,rho_air:float, schedule:pd.Series):
    return (c_air * rho_air / 3600.0) * schedule * air_flow_rate
