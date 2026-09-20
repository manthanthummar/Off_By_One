from __future__ import annotations

from datetime import timedelta
from app.models.schemas import Farm, Plot, Risk, WeatherReading, Action, now
from app.agents.planner import PlannerAgent
from app.db.repository import store


def test_rain_skips_irrigation():
    planner = PlannerAgent()
    w_rain = WeatherReading(farm_id="f1", humidity_pct=50, rain_24h_mm=13.0)
    verdict, reason = planner.window("irrigate", w_rain)
    assert verdict == "skip"
    assert "irrigation skipped" in reason

    # 12.0 mm -> ok
    w_border = WeatherReading(farm_id="f1", humidity_pct=50, rain_24h_mm=12.0)
    verdict, _ = planner.window("irrigate", w_border)
    assert verdict == "ok"


def test_heavy_rain_defers_fertilizer():
    planner = PlannerAgent()
    w_heavy = WeatherReading(farm_id="f1", humidity_pct=50, rain_24h_mm=20.0)
    verdict, reason = planner.window("fertilize", w_heavy)
    assert verdict == "defer"
    assert "deferred 48h" in reason

    # 19.9 mm -> ok
    w_below = WeatherReading(farm_id="f1", humidity_pct=50, rain_24h_mm=19.9)
    verdict, _ = planner.window("fertilize", w_below)
    assert verdict == "ok"


def test_spray_weather_window():
    planner = PlannerAgent()
    # Rain > 5mm -> defer
    w_rain = WeatherReading(farm_id="f1", humidity_pct=50, rain_24h_mm=6.0, wind_kph=5)
    verdict, _ = planner.window("spray", w_rain)
    assert verdict == "defer"

    # Wind > 20kph -> defer
    w_wind = WeatherReading(farm_id="f1", humidity_pct=50, rain_24h_mm=0, wind_kph=21.0)
    verdict, _ = planner.window("spray", w_wind)
    assert verdict == "defer"

    # Clear -> ok
    w_clear = WeatherReading(farm_id="f1", humidity_pct=50, rain_24h_mm=2.0, wind_kph=10)
    verdict, _ = planner.window("spray", w_clear)
    assert verdict == "ok"


def test_urea_split_dose_timing():
    planner = PlannerAgent()
    farm = Farm(id="f1", name="F1", plots=[Plot(id="p1", area_ha=1.0)])
    risk = Risk(farm_id="f1", plot_id="p1", kind="nutrient_deficiency", severity="high", score=75, summary="Low N")

    plan = planner.plan(farm, [risk], None, [])
    assert plan is not None
    fertilize_actions = [a for a in plan.actions if a.kind == "fertilize"]
    assert len(fertilize_actions) == 2
    assert "dose 1/2" in fertilize_actions[0].title
    assert "dose 2/2" in fertilize_actions[1].title
    diff = fertilize_actions[1].when - fertilize_actions[0].when
    assert diff.days == 14


def test_fungal_high_produces_scout_and_spray():
    planner = PlannerAgent()
    farm = Farm(id="f1", name="F1", plots=[Plot(id="p1", area_ha=1.0)])
    risk = Risk(farm_id="f1", plot_id="p1", kind="fungal_disease", severity="high", score=75, summary="Fungal")

    plan = planner.plan(farm, [risk], None, [])
    assert plan is not None
    kinds = {a.kind: a for a in plan.actions}
    assert "scout" in kinds
    assert "spray" in kinds
    assert kinds["spray"].requires_expert_approval is True


def test_budget_exhaustion():
    planner = PlannerAgent()
    farm = Farm(id="f1", name="F1", budget_inr=150.0, plots=[Plot(id="p1", area_ha=1.0)])
    r1 = Risk(farm_id="f1", plot_id="p1", kind="water_stress", severity="critical", score=95, summary="Dry")
    r2 = Risk(farm_id="f1", plot_id="p1", kind="nutrient_deficiency", severity="high", score=75, summary="Low N")

    plan = planner.plan(farm, [r1, r2], None, [])
    assert plan is not None
    # r1 irrigate costs 250 > 150 -> skipped budget
    for a in plan.actions:
        if a.cost_inr > 150:
            assert a.status == "skipped"
            assert a.hold_reason == "budget"


def test_auto_defer_and_auto_resume():
    planner = PlannerAgent()
    store.reset()
    farm = Farm(id="f1", name="F1", plots=[Plot(id="p1")])
    store.farms[farm.id] = farm

    act = Action(
        id="act_irr",
        farm_id="f1",
        plot_id="p1",
        risk_id="r1",
        kind="irrigate",
        title="Irrigate p1",
        what="Irrigate",
        when=now(),
        where="p1",
        cost_inr=250.0,
        status="planned",
    )
    store.actions[act.id] = act

    # Rain comes in -> auto-defer/skip
    w_rain = WeatherReading(farm_id="f1", humidity_pct=50, rain_24h_mm=30.0)
    notes = planner.reevaluate([act], w_rain, store)
    assert act.status == "skipped"
    assert act.hold_reason == "weather"
    assert len(notes) == 1

    # Rain clears -> auto-resume
    w_clear = WeatherReading(farm_id="f1", humidity_pct=50, rain_24h_mm=0.0)
    notes2 = planner.reevaluate([act], w_clear, store)
    assert act.status == "planned"
    assert act.hold_reason is None
    assert len(notes2) == 1


def test_no_duplicate_plans_on_rerun():
    planner = PlannerAgent()
    farm = Farm(id="f1", name="F1", plots=[Plot(id="p1")])
    risk = Risk(farm_id="f1", plot_id="p1", kind="water_stress", severity="high", score=75, summary="Dry")

    plan1 = planner.plan(farm, [risk], None, [])
    assert plan1 is not None

    # Re-run with the existing action active
    plan2 = planner.plan(farm, [risk], None, plan1.actions)
    assert plan2 is None
