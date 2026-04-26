# src/openbep4eu/adapters/weather/epw_adapter.py
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple
import pandas as pd

from pvlib.iotools import read_epw


@dataclass(frozen=True)
class EPWMetadata:
    source_path: str
    file_sha256: str

    city: Optional[str]
    state: Optional[str]
    country: Optional[str]

    latitude: float
    longitude: float
    tz: Any
    altitude: Optional[float]

    raw: dict[str, Any]


@dataclass(frozen=True)
class EPWData:
    data: pd.DataFrame
    meta: EPWMetadata


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_epw(path: str | Path) -> EPWData:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"EPW file not found: {p}")

    df, meta = read_epw(str(p))  # (DataFrame, dict)

    file_hash = _sha256_file(p)

    epw_meta = EPWMetadata(
        source_path=str(p),
        file_sha256=file_hash,
        city=meta.get("city"),
        state=meta.get("state-prov") or meta.get("state"),
        country=meta.get("country"),
        latitude=float(meta["latitude"]),
        longitude=float(meta["longitude"]),
        tz=meta['TZ'],
        altitude=float(meta["altitude"]) if meta.get("altitude") is not None else None,
        raw=meta,
    )

    return EPWData(data=df, meta=epw_meta)


def extract_irradiance_components(epw: EPWData) -> pd.DataFrame:
    df = epw.data

    required = ["ghi", "dni", "dhi"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"EPW is missing irradiance columns {missing}. "
            f"Available columns: {list(df.columns)[:30]}..."
        )

    out = df[required].copy()

    # Ensure numeric
    for c in required:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    return out


_EPW_CACHE: dict[str, EPWData] = {}


def load_epw_cached(path: str | Path) -> EPWData:
    p = str(Path(path).expanduser().resolve())
    if p in _EPW_CACHE:
        return _EPW_CACHE[p]
    epw = load_epw(p)
    _EPW_CACHE[p] = epw
    return epw
