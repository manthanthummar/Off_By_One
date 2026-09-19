from __future__ import annotations

from typing import Optional
from app.config import T, SEVERITY_RANK, SEVERITY_SCORE
from app.models.schemas import Farm, SoilReading, WeatherReading, DroneReading, Risk


def _max_sev(*sevs: Optional[str]) -> Optional[str]:
    present = [s for s in sevs if s]
    return max(present, key=lambda s: SEVERITY_RANK[s]) if present else None


class RiskDetectionAgent:
    name = "RiskDetectionAgent"

    def detect(
        self,
        farm: Farm,
        soil: dict[str, SoilReading],
        weather: Optional[WeatherReading],
        drone: dict[str, DroneReading],
        drone_prev: dict[str, DroneReading],
    ) -> list[Risk]:
        risks: list[Risk] = []
        plot_ids = list(dict.fromkeys([*soil.keys(), *drone.keys()])) or [farm.plots[0].id]

        for pid in plot_ids:
            s, d = soil.get(pid), drone.get(pid)

            # --- water stress
            if s is not None:
                sev = (
                    "critical"
                    if s.moisture_pct < T["moisture_critical"]
                    else "high"
                    if s.moisture_pct < T["moisture_high"]
                    else "medium"
                    if s.moisture_pct < T["moisture_medium"]
                    else None
                )
                if sev:
                    risks.append(
                        self._risk(
                            farm,
                            pid,
                            "water_stress",
                            sev,
                            f"Soil moisture {s.moisture_pct:.0f}% in {pid} ({sev} water stress).",
                            {
                                "moisture_pct": s.moisture_pct,
                                "critical_below": T["moisture_critical"],
                                "high_below": T["moisture_high"],
                                "evaporation_mm": weather.evaporation_mm if weather else None,
                            },
                        )
                    )

            # --- nutrient deficiency (nitrogen)
            if s is not None and s.nitrogen_ppm is not None:
                sev = (
                    "critical"
                    if s.nitrogen_ppm < T["n_critical"]
                    else "high"
                    if s.nitrogen_ppm < T["n_high"]
                    else None
                )
                if sev:
                    risks.append(
                        self._risk(
                            farm,
                            pid,
                            "nutrient_deficiency",
                            sev,
                            f"Nitrogen {s.nitrogen_ppm:.0f} ppm in {pid} is below {T['n_high']:.0f} ppm.",
                            {"nitrogen_ppm": s.nitrogen_ppm, "threshold_ppm": T["n_high"]},
                        )
                    )

            # --- NDVI / vegetation decline
            if d is not None:
                prev = (
                    d.ndvi_prev
                    if d.ndvi_prev is not None
                    else (drone_prev[pid].ndvi if pid in drone_prev else None)
                )
                drop = round(prev - d.ndvi, 4) if prev is not None else 0.0
                sev_drop = (
                    "high"
                    if drop >= T["ndvi_drop_high"]
                    else "medium"
                    if drop >= T["ndvi_drop_medium"]
                    else None
                )
                sev_low = "critical" if d.ndvi < 0.20 else "high" if d.ndvi < T["ndvi_floor"] else None
                sev = _max_sev(sev_drop, sev_low)
                if sev:
                    risks.append(
                        self._risk(
                            farm,
                            pid,
                            "vegetation_decline",
                            sev,
                            f"NDVI {d.ndvi:.2f} in {pid} (drop {drop:.2f}).",
                            {
                                "ndvi": d.ndvi,
                                "ndvi_prev": prev,
                                "ndvi_drop": round(drop, 3),
                                "ndvi_floor": T["ndvi_floor"],
                            },
                        )
                    )

            # --- fungal disease (humidity + wet canopy + drone anomaly)
            if weather is not None:
                humid = weather.humidity_pct > T["humidity_fungal"]
                warm = weather.temp_c is None or 15 <= weather.temp_c <= 30
                anomaly = d is not None and (
                    d.anomaly_score >= T["anomaly_score"] or bool(d.anomaly_signature)
                )
                if humid and warm:
                    signals = 1 + int(weather.canopy_wet) + int(anomaly)
                    sev = {1: "medium", 2: "high", 3: "critical"}[signals]
                    risks.append(
                        self._risk(
                            farm,
                            pid,
                            "fungal_disease",
                            sev,
                            f"Fungal risk in {pid}: humidity {weather.humidity_pct:.0f}%"
                            f"{', wet canopy' if weather.canopy_wet else ''}"
                            f"{', drone anomaly' if anomaly else ''}.",
                            {
                                "humidity_pct": weather.humidity_pct,
                                "canopy_wet": weather.canopy_wet,
                                "temp_c": weather.temp_c,
                                "drone_anomaly_score": d.anomaly_score if d else None,
                                "drone_signature": d.anomaly_signature if d else None,
                            },
                        )
                    )
        return risks

    @staticmethod
    def _risk(farm: Farm, pid: str, kind: str, sev: str, summary: str, evidence: dict) -> Risk:
        return Risk(
            farm_id=farm.id,
            plot_id=pid,
            kind=kind,  # type: ignore[arg-type]
            severity=sev,  # type: ignore[arg-type]
            score=SEVERITY_SCORE[sev],
            summary=summary,
            evidence=evidence,
        )
