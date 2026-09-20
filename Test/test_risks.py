from __future__ import annotations

from app.models.schemas import Farm, Plot, SoilReading, WeatherReading, DroneReading
from app.agents.detection import RiskDetectionAgent
from app.config import T


def test_moisture_threshold_boundaries():
    agent = RiskDetectionAgent()
    farm = Farm(id="f1", name="F1", plots=[Plot(id="p1")])

    # 14.9 < 15.0 -> critical
    r = agent.detect(farm, {"p1": SoilReading(farm_id="f1", plot_id="p1", moisture_pct=14.9)}, None, {}, {})
    assert any(x.kind == "water_stress" and x.severity == "critical" for x in r)

    # 15.0 -> high
    r = agent.detect(farm, {"p1": SoilReading(farm_id="f1", plot_id="p1", moisture_pct=15.0)}, None, {}, {})
    assert any(x.kind == "water_stress" and x.severity == "high" for x in r)

    # 24.9 < 25.0 -> high
    r = agent.detect(farm, {"p1": SoilReading(farm_id="f1", plot_id="p1", moisture_pct=24.9)}, None, {}, {})
    assert any(x.kind == "water_stress" and x.severity == "high" for x in r)

    # 25.0 -> medium
    r = agent.detect(farm, {"p1": SoilReading(farm_id="f1", plot_id="p1", moisture_pct=25.0)}, None, {}, {})
    assert any(x.kind == "water_stress" and x.severity == "medium" for x in r)

    # 34.9 < 35.0 -> medium
    r = agent.detect(farm, {"p1": SoilReading(farm_id="f1", plot_id="p1", moisture_pct=34.9)}, None, {}, {})
    assert any(x.kind == "water_stress" and x.severity == "medium" for x in r)

    # 35.0 -> no water stress
    r = agent.detect(farm, {"p1": SoilReading(farm_id="f1", plot_id="p1", moisture_pct=35.0)}, None, {}, {})
    assert not any(x.kind == "water_stress" for x in r)


def test_nitrogen_threshold_boundaries():
    agent = RiskDetectionAgent()
    farm = Farm(id="f1", name="F1", plots=[Plot(id="p1")])

    # 24.9 < 25.0 -> critical
    r = agent.detect(farm, {"p1": SoilReading(farm_id="f1", plot_id="p1", moisture_pct=40.0, nitrogen_ppm=24.9)}, None, {}, {})
    assert any(x.kind == "nutrient_deficiency" and x.severity == "critical" for x in r)

    # 25.0 -> high
    r = agent.detect(farm, {"p1": SoilReading(farm_id="f1", plot_id="p1", moisture_pct=40.0, nitrogen_ppm=25.0)}, None, {}, {})
    assert any(x.kind == "nutrient_deficiency" and x.severity == "high" for x in r)

    # 39.9 < 40.0 -> high
    r = agent.detect(farm, {"p1": SoilReading(farm_id="f1", plot_id="p1", moisture_pct=40.0, nitrogen_ppm=39.9)}, None, {}, {})
    assert any(x.kind == "nutrient_deficiency" and x.severity == "high" for x in r)

    # 40.0 -> no deficiency
    r = agent.detect(farm, {"p1": SoilReading(farm_id="f1", plot_id="p1", moisture_pct=40.0, nitrogen_ppm=40.0)}, None, {}, {})
    assert not any(x.kind == "nutrient_deficiency" for x in r)


def test_ndvi_threshold_boundaries():
    agent = RiskDetectionAgent()
    farm = Farm(id="f1", name="F1", plots=[Plot(id="p1")])

    # Drop >= 0.10 -> high
    r = agent.detect(farm, {}, None, {"p1": DroneReading(farm_id="f1", plot_id="p1", ndvi=0.60, ndvi_prev=0.70)}, {})
    assert any(x.kind == "vegetation_decline" and x.severity == "high" for x in r)

    # Drop 0.05 <= drop < 0.10 -> medium
    r = agent.detect(farm, {}, None, {"p1": DroneReading(farm_id="f1", plot_id="p1", ndvi=0.65, ndvi_prev=0.70)}, {})
    assert any(x.kind == "vegetation_decline" and x.severity == "medium" for x in r)

    # Drop 0.04 -> no risk if ndvi >= 0.30
    r = agent.detect(farm, {}, None, {"p1": DroneReading(farm_id="f1", plot_id="p1", ndvi=0.66, ndvi_prev=0.70)}, {})
    assert not any(x.kind == "vegetation_decline" for x in r)

    # Absolute ndvi < 0.20 -> critical
    r = agent.detect(farm, {}, None, {"p1": DroneReading(farm_id="f1", plot_id="p1", ndvi=0.19)}, {})
    assert any(x.kind == "vegetation_decline" and x.severity == "critical" for x in r)

    # Absolute 0.20 <= ndvi < 0.30 -> high
    r = agent.detect(farm, {}, None, {"p1": DroneReading(farm_id="f1", plot_id="p1", ndvi=0.25)}, {})
    assert any(x.kind == "vegetation_decline" and x.severity == "high" for x in r)


def test_fungal_conditions_and_boundaries():
    agent = RiskDetectionAgent()
    farm = Farm(id="f1", name="F1", plots=[Plot(id="p1")])

    # Boundary: humidity == 80.0% -> not > 80, no fungal risk
    w_border = WeatherReading(farm_id="f1", humidity_pct=80.0, temp_c=25.0)
    r = agent.detect(farm, {}, w_border, {}, {})
    assert not any(x.kind == "fungal_disease" for x in r)

    # Humidity 80.1%, temp 25C -> medium (1 signal)
    w_med = WeatherReading(farm_id="f1", humidity_pct=80.1, temp_c=25.0, canopy_wet=False)
    r = agent.detect(farm, {}, w_med, {}, {})
    assert any(x.kind == "fungal_disease" and x.severity == "medium" for x in r)

    # Humidity 85%, temp 25C, canopy wet -> high (2 signals)
    w_high = WeatherReading(farm_id="f1", humidity_pct=85.0, temp_c=25.0, canopy_wet=True)
    r = agent.detect(farm, {}, w_high, {}, {})
    assert any(x.kind == "fungal_disease" and x.severity == "high" for x in r)

    # Humidity 85%, temp 25C, canopy wet, drone anomaly score >= 0.6 -> critical (3 signals)
    d_crit = DroneReading(farm_id="f1", plot_id="p1", ndvi=0.70, anomaly_score=0.6)
    r = agent.detect(farm, {}, w_high, {"p1": d_crit}, {})
    assert any(x.kind == "fungal_disease" and x.severity == "critical" for x in r)

    # Boundary: temp outside 15-30 -> no fungal risk
    w_cold = WeatherReading(farm_id="f1", humidity_pct=85.0, temp_c=14.0, canopy_wet=True)
    r = agent.detect(farm, {}, w_cold, {"p1": d_crit}, {})
    assert not any(x.kind == "fungal_disease" for x in r)

    w_hot = WeatherReading(farm_id="f1", humidity_pct=85.0, temp_c=31.0, canopy_wet=True)
    r = agent.detect(farm, {}, w_hot, {"p1": d_crit}, {})
    assert not any(x.kind == "fungal_disease" for x in r)
