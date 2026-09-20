#!/usr/bin/env python3
"""
FarmSense Telemetry Simulator.
Publishes deterministic sensor, weather, and drone readings to MQTT or REST /ingest,
then triggers orchestration and displays resulting risks, plans, tasks, and escalations.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Optional
import httpx

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("simulator")


def get_scenario_payloads(scenario: str, farm_id: str, clear_rain: bool = False) -> dict[str, Any]:
    """Return deterministic readings for the given scenario."""
    if scenario == "drought":
        return {
            "soil": {"farm_id": farm_id, "plot_id": "plot-1", "moisture_pct": 10.5},
            "weather": {
                "farm_id": farm_id,
                "humidity_pct": 45.0,
                "rain_24h_mm": 0.0,
                "temp_c": 32.0,
                "evaporation_mm": 5.2,
                "wind_kph": 10.0,
            },
            "drone": None,
        }
    elif scenario == "fungal":
        return {
            "soil": {"farm_id": farm_id, "plot_id": "plot-1", "moisture_pct": 40.0},
            "weather": {
                "farm_id": farm_id,
                "humidity_pct": 88.0,
                "canopy_wet": True,
                "temp_c": 24.0,
                "rain_24h_mm": 0.0,
                "wind_kph": 5.0,
            },
            "drone": {
                "farm_id": farm_id,
                "plot_id": "plot-1",
                "ndvi": 0.55,
                "ndvi_prev": 0.72,
                "anomaly_score": 0.8,
                "anomaly_signature": "leaf-lesion-cluster",
            },
        }
    elif scenario == "nutrient":
        return {
            "soil": {
                "farm_id": farm_id,
                "plot_id": "plot-1",
                "moisture_pct": 45.0,
                "nitrogen_ppm": 30.0,
                "ph": 6.5,
            },
            "weather": {
                "farm_id": farm_id,
                "humidity_pct": 55.0,
                "rain_24h_mm": 0.0,
                "temp_c": 26.0,
                "wind_kph": 8.0,
            },
            "drone": None,
        }
    elif scenario == "rain_deferral":
        if clear_rain:
            return {
                "soil": None,
                "weather": {
                    "farm_id": farm_id,
                    "humidity_pct": 50.0,
                    "rain_24h_mm": 0.0,
                    "temp_c": 25.0,
                    "wind_kph": 8.0,
                },
                "drone": None,
            }
        return {
            "soil": {
                "farm_id": farm_id,
                "plot_id": "plot-1",
                "moisture_pct": 20.0,
                "nitrogen_ppm": 32.0,
            },
            "weather": {
                "farm_id": farm_id,
                "humidity_pct": 50.0,
                "rain_24h_mm": 30.0,
                "temp_c": 22.0,
                "wind_kph": 12.0,
            },
            "drone": None,
        }
    else:
        raise ValueError(f"Unknown scenario: {scenario}")


def ensure_farm_exists(client: httpx.Client, api_url: str, headers: dict[str, str], farm_id: str) -> None:
    """Creates the farm if not present, ignoring HTTP 409."""
    farm_payload = {
        "id": farm_id,
        "name": f"Simulator Farm ({farm_id})",
        "owner": "Simulator Farmer",
        "phone": "+919876543210",
        "budget_inr": 5000.0,
        "plots": [{"id": "plot-1", "name": "Plot 1", "crop": "wheat", "area_ha": 1.0}],
    }
    r = client.post(f"{api_url}/farms", json=farm_payload, headers=headers)
    if r.status_code == 201:
        log.info("Created farm '%s'", farm_id)
    elif r.status_code == 409:
        log.debug("Farm '%s' already exists", farm_id)
    else:
        r.raise_for_status()


def publish_mqtt(host: str, port: int, farm_id: str, payloads: dict[str, Any]) -> bool:
    """Publishes telemetry via MQTT. Returns True on success, False on failure."""
    try:
        import paho.mqtt.client as mqtt

        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except AttributeError:
            client = mqtt.Client()

        client.connect(host, port, keepalive=10)
        for kind, data in payloads.items():
            if data:
                topic = f"farms/{farm_id}/{kind}"
                client.publish(topic, json.dumps(data))
                log.info("MQTT published -> %s", topic)
        client.disconnect()
        return True
    except Exception as exc:
        log.warning("MQTT publication failed (%s), falling back to REST: %s", host, exc)
        return False


def publish_rest(client: httpx.Client, api_url: str, headers: dict[str, str], payloads: dict[str, Any]) -> None:
    """Publishes telemetry via REST /ingest/*."""
    for kind, data in payloads.items():
        if data:
            endpoint = f"{api_url}/ingest/{kind}"
            r = client.post(endpoint, json=data, headers=headers)
            r.raise_for_status()
            log.info("REST ingested -> %s", endpoint)


def run_simulation(
    scenario: str,
    farm_id: str = "sim-farm-01",
    api_url: str = "http://localhost:8000",
    api_key: str = "farmsense-dev-key",
    mqtt_host: Optional[str] = None,
    mqtt_port: int = 1883,
    rest_only: bool = False,
    clear_rain: bool = False,
    client: Optional[httpx.Client] = None,
) -> dict[str, Any]:
    """Executes the deterministic scenario pipeline."""
    headers = {"X-API-Key": api_key}
    
    def _execute(c: httpx.Client) -> dict[str, Any]:
        # Step 1: Ensure farm exists
        ensure_farm_exists(c, api_url, headers, farm_id)

        # Step 2: Get scenario payloads
        payloads = get_scenario_payloads(scenario, farm_id, clear_rain=clear_rain)

        # Step 3: Publish via MQTT (with REST fallback) or REST only
        mqtt_success = False
        if mqtt_host and not rest_only:
            mqtt_success = publish_mqtt(mqtt_host, mqtt_port, farm_id, payloads)
        if not mqtt_success:
            publish_rest(c, api_url, headers, payloads)

        # Step 4: Call POST /orchestrate/{farm_id}
        orch_res = c.post(f"{api_url}/orchestrate/{farm_id}", headers=headers)
        orch_res.raise_for_status()
        result = orch_res.json()

        # Step 5: Format and display summary
        print_summary(scenario, farm_id, result, clear_rain)
        return result

    if client is not None:
        return _execute(client)
    else:
        with httpx.Client(timeout=15.0) as c:
            return _execute(c)


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def print_summary(scenario: str, farm_id: str, result: dict[str, Any], clear_rain: bool = False) -> None:
    sep = "=" * 70
    print("\n" + sep)
    step_label = " (Step 2: Clear Rain)" if clear_rain else ""
    print(f" FARMSENSE SIMULATION: scenario={scenario.upper()}{step_label} | farm={farm_id}")
    print(sep)
    print(f"Run ID:        {result.get('run_id')}")
    print(f"Advice Source: {result.get('advice_source')} | Advice: {result.get('advice')}")

    # Risks
    risks = result.get("risks", [])
    print(f"\nDetected Risks ({len(risks)}):")
    for r in risks:
        print(f"  * [{r.get('severity').upper()}] {r.get('kind')}: {r.get('summary')} (Score: {r.get('score')})")

    # Plan
    plan = result.get("plan")
    if plan and plan.get("actions"):
        print(f"\nAction Plan ({len(plan['actions'])} actions, Total: Rs{plan.get('total_cost_inr', 0):.0f}):")
        for a in plan["actions"]:
            hold = f" [HOLD: {a.get('hold_reason')}]" if a.get("hold_reason") else ""
            gated = " [EXPERT APPROVAL REQUIRED]" if a.get("requires_expert_approval") else ""
            print(f"  * {a.get('title')} ({a.get('kind')}) -> status: {a.get('status')}{hold}{gated} (Cost: Rs{a.get('cost_inr'):.0f})")
    else:
        print("\nAction Plan: None (No new actions needed or unchanged)")

    # Tasks
    tasks = result.get("tasks", [])
    print(f"\nGenerated Tasks ({len(tasks)}):")
    for t in tasks:
        print(f"  * [{t.get('status')}] {t.get('title')} (Kind: {t.get('kind')}, Due: {t.get('due')})")

    # Escalations
    escalations = result.get("escalations", [])
    print(f"\nEscalations ({len(escalations)}):")
    for e in escalations:
        print(f"  * [{e.get('status').upper()}] {e.get('reason')}")

    # SMS Alerts
    alerts = result.get("alerts", [])
    print(f"\nSMS Alerts Sent ({len(alerts)}):")
    for al in alerts:
        print(f"  * [{len(al.get('message', ''))}/160 chars] {al.get('message')}")
    print(sep + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="FarmSense Telemetry Simulator")
    parser.add_argument(
        "--scenario",
        required=True,
        choices=["drought", "fungal", "nutrient", "rain_deferral"],
        help="Deterministic scenario to simulate",
    )
    parser.add_argument("--farm-id", default="sim-farm-01", help="Target farm ID")
    parser.add_argument("--api-url", default="http://localhost:8000", help="FarmSense API base URL")
    parser.add_argument("--api-key", default="farmsense-dev-key", help="X-API-Key for authentication")
    parser.add_argument("--mqtt-host", default=None, help="MQTT Broker host (optional)")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT Broker port")
    parser.add_argument("--rest-only", action="store_true", help="Force REST ingestion without MQTT")
    parser.add_argument("--clear-rain", action="store_true", help="Second step for rain_deferral scenario: clear rain")

    args = parser.parse_args()
    try:
        run_simulation(
            scenario=args.scenario,
            farm_id=args.farm_id,
            api_url=args.api_url.rstrip("/"),
            api_key=args.api_key,
            mqtt_host=args.mqtt_host,
            mqtt_port=args.mqtt_port,
            rest_only=args.rest_only,
            clear_rain=args.clear_rain,
        )
    except Exception as exc:
        log.error("Simulation failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
