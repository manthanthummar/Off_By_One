# FarmSense Telemetry Simulator

The FarmSense Telemetry Simulator generates deterministic sensor, weather, and drone telemetry to test the multi-agent detection, planning, safety gating, and escalation pipeline.

It communicates primarily via **MQTT** (topics: `farms/<farm_id>/soil|weather|drone`), and **automatically falls back to REST (`/ingest/*`)** if MQTT is unreachable or `--rest-only` is set.

---

## Command-Line Arguments

| Flag | Default | Description |
|---|---|---|
| `--scenario` | (Required) | `drought`, `fungal`, `nutrient`, `rain_deferral` |
| `--farm-id` | `sim-farm-01` | Target farm ID (automatically created if not present) |
| `--api-url` | `http://localhost:8000` | FarmSense API endpoint |
| `--api-key` | `farmsense-dev-key` | `X-API-Key` authentication header |
| `--mqtt-host` | None | MQTT Broker host (e.g. `localhost` or `mosquitto`) |
| `--mqtt-port` | `1883` | MQTT Broker port |
| `--rest-only` | `False` | Force REST ingestion without attempting MQTT |
| `--clear-rain` | `False` | Step 2 for `rain_deferral`: publishes rain 0 mm to resume actions |

---

## Scenarios & Expected Outcomes

### 1. Drought Scenario (`--scenario drought`)
- **Input Telemetry**: Soil moisture 10.5%, Humidity 45%, Rain 0 mm, Temp 32°C.
- **Expected Outcome**:
  - **Risk**: Critical water stress detected (`moisture < 15%`).
  - **Plan**: Urgent irrigation action scheduled immediately.
  - **Task**: 1 urgent irrigation task created.
  - **SMS Alert**: Farmer notified with SMS ≤ 160 characters.
```bash
python simulator/simulate.py --scenario drought --rest-only
```

### 2. Fungal Disease Scenario (`--scenario fungal`)
- **Input Telemetry**: Humidity 88%, Canopy wet, Temp 24°C, Drone NDVI drop 0.72 → 0.55, Anomaly score 0.8 with `leaf-lesion-cluster`.
- **Expected Outcome**:
  - **Risk**: Critical fungal disease detected (`humidity > 80%`, `15-30°C`, wet canopy + drone anomaly).
  - **Plan**: Scout action + chemical spray action (`requires_expert_approval = True`).
  - **Safety Gate**: Spray action status set to `awaiting_approval`.
  - **Escalation**: 1 agronomist escalation record created (`pending`).
  - **SMS Alert**: No spray SMS sent to farmer yet (blocked by safety gate).
```bash
python simulator/simulate.py --scenario fungal --rest-only
```

### 3. Nutrient Deficiency Scenario (`--scenario nutrient`)
- **Input Telemetry**: Soil moisture 45%, Nitrogen 30 ppm (`< 40 ppm`), Rain 0 mm.
- **Expected Outcome**:
  - **Risk**: High nutrient deficiency detected.
  - **Plan**: 2-stage split-dose urea application (Dose 1/2 morning, Dose 2/2 in 14 days).
  - **Tasks**: 2 urea application tasks created with exact 14-day interval.
```bash
python simulator/simulate.py --scenario nutrient --rest-only
```

### 4. Rain Deferral & Auto-Resume Scenario (`--scenario rain_deferral`)
- **Step 1: Heavy Rain Forecast**:
  - **Input Telemetry**: Moisture 20%, Nitrogen 32 ppm, Forecast rain 30 mm/24h.
  - **Expected Outcome**:
    - Irrigation **skipped** (`rain > 12 mm`).
    - Fertilizer **deferred 48h** (`rain >= 20 mm`).
    - Tasks list is empty (actions on hold).
```bash
python simulator/simulate.py --scenario rain_deferral --rest-only
```
- **Step 2: Weather Clears (`--clear-rain`)**:
  - **Input Telemetry**: Rain 0 mm.
  - **Expected Outcome**:
    - Weather window cleared.
    - Actions auto-resume to `planned` / `notified`.
    - 3 tasks created (1 irrigation + 2 split-dose urea).
```bash
python simulator/simulate.py --scenario rain_deferral --clear-rain --rest-only
```
