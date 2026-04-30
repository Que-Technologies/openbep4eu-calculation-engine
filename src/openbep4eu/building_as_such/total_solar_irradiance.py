# src/openbep4eu/engine/calculator/total_solar_irradiance.py
from __future__ import annotations
from typing import Iterable, Optional
import pandas as pd
import pvlib
from openbep4eu.building_as_such.models.epw import EPWData,extract_irradiance_components
from openbep4eu.building_as_such.models.envelope_element import EnvelopeElement
from openbep4eu.building_as_such.models.definitions import SurfaceIrradianceSummary,IrradianceTimeseries

def _south0_to_north0(azimuth_deg_south0: float) -> float:
    return (azimuth_deg_south0 + 180.0) % 360.0


def _ensure_datetime_index(df: pd.DataFrame) -> pd.DatetimeIndex:
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("Weather dataframe must be indexed by pandas.DatetimeIndex.")
    return df.index


def _poa_energy_kwh_m2(poa_w_m2: pd.Series) -> float:
    return float(poa_w_m2.fillna(0.0).sum() / 1000.0)

def _monthly_energy_kwh_m2(poa_global: pd.Series) -> dict[str, float]:
    monthly = (poa_global.resample("MS").mean() * 24 * poa_global.resample("MS").size()).fillna(0.0)
    return {ts.strftime("%Y-%m"): float(val) for ts, val in monthly.items()}

def get_total_irradiance(
        surfaces: Iterable[EnvelopeElement],
        epw: EPWData,
        *,
        albedo: float = 0.2,
        model: str = "perez",
) -> list:
    irr = extract_irradiance_components(epw)
    times = _ensure_datetime_index(irr)

    # Site and solar position
    meta = epw.meta
    lat = meta.latitude
    lon = meta.longitude


    location = pvlib.location.Location(latitude=lat, longitude=lon, tz=int(epw.meta.raw['TZ']), altitude=meta.altitude)

    solpos = location.get_solarposition(times)
    dni_extra = pvlib.irradiance.get_extra_radiation(times)

    airmass_rel = pvlib.atmosphere.get_relative_airmass(solpos["apparent_zenith"])

    results: list[SurfaceIrradianceSummary] = []

    ghi = irr["ghi"]
    dni = irr["dni"]
    dhi = irr["dhi"]

    for s in surfaces:
        surface_tilt = float(s.tilt_deg)
        surface_az_north0 = float(s.azimuth_deg)

        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=surface_tilt,
            surface_azimuth=surface_az_north0,
            solar_zenith=solpos["apparent_zenith"],
            solar_azimuth=solpos["azimuth"],
            dni=dni,
            ghi=ghi,
            dhi=dhi,
            dni_extra=dni_extra,
            airmass=airmass_rel,
            albedo=albedo,
            model=model,
            model_perez="allsitescomposite1990",
        )

        poa_global = poa["poa_global"]
        poa_direct = poa.get("poa_direct")
        poa_diffuse = poa.get("poa_diffuse")

        annual_kwh_m2 = _poa_energy_kwh_m2(poa_global)
        monthly_kwh_m2 = _monthly_energy_kwh_m2(poa_global)

        if poa_global.dropna().empty:
            peak_val = 0.0
            peak_ts = None
        else:
            peak_val = float(poa_global.max())
            peak_ts = poa_global.idxmax()

        results.append(
            SurfaceIrradianceSummary(
                surface_id=s.element_id,
                surface_type=s.surface_type,
                tilt_deg=surface_tilt,
                azimuth_deg_north0=surface_az_north0,
                annual_poa_global_kwh_m2=annual_kwh_m2,
                monthly_poa_global_kwh_m2=monthly_kwh_m2,
                peak_poa_global_w_m2=peak_val,
                peak_timestamp=peak_ts,
                timeseries=IrradianceTimeseries.from_poa_df(poa)
            )
        )

    return results
