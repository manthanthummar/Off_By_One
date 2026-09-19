from __future__ import annotations

import logging
from typing import Optional
import httpx
from app.models.schemas import Farm, WeatherReading

log = logging.getLogger("farmsense.weather")


def fetch_open_meteo(farm: Farm) -> Optional[WeatherReading]:
    """Free Open-Meteo forecast -> WeatherReading. Returns None offline / on error."""
    if farm.lat is None or farm.lon is None:
        return None
    try:
        with httpx.Client(timeout=6.0) as c:
            r = c.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": farm.lat,
                    "longitude": farm.lon,
                    "forecast_days": 2,
                    "timezone": "auto",
                    "hourly": "temperature_2m,relative_humidity_2m,precipitation,et0_fao_evapotranspiration,wind_speed_10m",
                },
            )
            r.raise_for_status()
            h = r.json()["hourly"]
        n = 24
        return WeatherReading(
            farm_id=farm.id,
            temp_c=h["temperature_2m"][0],
            humidity_pct=h["relative_humidity_2m"][0],
            rain_24h_mm=round(sum(h["precipitation"][:n]), 1),
            wind_kph=max(h["wind_speed_10m"][:n]),
            evaporation_mm=round(sum(h["et0_fao_evapotranspiration"][:n]), 2),
            forecast=[
                {"time": h["time"][i], "rain_mm": h["precipitation"][i], "temp_c": h["temperature_2m"][i]}
                for i in range(0, 48, 3)
            ],
        )
    except Exception as exc:
        log.warning("Open-Meteo unavailable: %s", exc)
        return None
