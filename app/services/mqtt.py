from __future__ import annotations

import json
import logging
from typing import Set
from app.config import settings
from app.models.schemas import SoilReading, WeatherReading, DroneReading
from app.db.repository import store

log = logging.getLogger("farmsense.mqtt")


def ingest_payload(kind: str, farm_id: str, payload: dict) -> None:
    payload = {**payload, "farm_id": farm_id}
    model = {"soil": SoilReading, "weather": WeatherReading, "drone": DroneReading}[kind]
    reading = model(**payload)
    with store.lock:
        if farm_id not in store.farms:
            raise KeyError(f"unknown farm {farm_id}")
        getattr(store, f"add_{kind}")(reading)


class MqttService:
    """Subscribes to farms/<farm_id>/soil|weather|drone. Optional: only starts if MQTT_HOST is set."""

    def __init__(self) -> None:
        self.client = None
        self.fresh_farms: Set[str] = set()

    def get_and_clear_fresh_farms(self) -> Set[str]:
        with store.lock:
            fresh = set(self.fresh_farms)
            self.fresh_farms.clear()
            return fresh

    def start(self) -> None:
        if not settings.mqtt_host:
            log.info("MQTT disabled (MQTT_HOST not set); REST /ingest/* is the fallback.")
            return
        try:
            import paho.mqtt.client as mqtt

            try:
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # paho >= 2
            except AttributeError:
                client = mqtt.Client()  # paho 1.x

            def on_connect(c, *_args):
                c.subscribe("farms/+/soil")
                c.subscribe("farms/+/weather")
                c.subscribe("farms/+/drone")
                log.info("MQTT connected & subscribed")

            def on_message(_c, _u, msg):
                try:
                    _, farm_id, kind = msg.topic.split("/")
                    ingest_payload(kind, farm_id, json.loads(msg.payload.decode()))
                    with store.lock:
                        self.fresh_farms.add(farm_id)
                except Exception as exc:
                    log.warning("MQTT message rejected (%s): %s", msg.topic, exc)

            client.on_connect, client.on_message = on_connect, on_message
            client.connect_async(settings.mqtt_host, settings.mqtt_port, keepalive=60)
            client.loop_start()
            self.client = client
        except Exception as exc:
            log.warning("MQTT unavailable, continuing without it: %s", exc)

    def stop(self) -> None:
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()


mqtt_service = MqttService()
