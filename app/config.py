from __future__ import annotations

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    farmsense_api_key: str = Field(default="farmsense-dev-key", alias="FARMSENSE_API_KEY")
    database_url: str = Field(default="", alias="DATABASE_URL")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-5", alias="ANTHROPIC_MODEL")
    mqtt_host: str = Field(default="", alias="MQTT_HOST")
    mqtt_port: int = Field(default=1883, alias="MQTT_PORT")
    cors_origins_raw: str = Field(default="", alias="CORS_ORIGINS")
    auto_orchestrate_interval: int = Field(default=0, alias="AUTO_ORCHESTRATE_INTERVAL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def api_key(self) -> str:
        return self.farmsense_api_key

    @property
    def anthropic_key(self) -> str:
        return self.anthropic_api_key

    @property
    def cors_origins(self) -> list[str]:
        extra = [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]
        return ["http://localhost:3000", "http://127.0.0.1:3000", *extra]


settings = Settings()

# Agronomic thresholds (single source of truth for detection + planning)
T = dict(
    moisture_critical=15.0, moisture_high=25.0, moisture_medium=35.0,   # soil moisture %
    ndvi_drop_high=0.10, ndvi_drop_medium=0.05, ndvi_floor=0.30,        # NDVI
    humidity_fungal=80.0, anomaly_score=0.6,                             # fungal conditions
    n_high=40.0, n_critical=25.0,                                        # nitrogen ppm
    rain_skip_irrigation_mm=12.0, rain_heavy_mm=20.0,                    # 24h rain windows
    spray_max_rain_mm=5.0, spray_max_wind_kph=20.0,
)
SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
SEVERITY_SCORE = {"low": 25, "medium": 50, "high": 75, "critical": 95}
