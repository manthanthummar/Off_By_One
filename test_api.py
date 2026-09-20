import sys; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__file__)) if "tests" in __file__ else ".")
from fastapi.testclient import TestClient
import main
c = TestClient(main.app); H = {"X-API-Key": "farmsense-dev-key"}

def mkfarm(fid="f1", budget=5000):
    r = c.post("/farms", json={"id": fid, "name": "T", "phone": "+91", "budget_inr": budget}, headers=H); assert r.status_code == 201, r.text

def setup(): c.post("/demo/reset", headers=H); mkfarm()

def test_auth():
    assert c.get("/health").status_code == 200
    assert c.get("/farms").status_code == 401
    assert c.get("/farms", headers={"X-API-Key": "bad"}).status_code == 401
    assert c.get("/farms", headers=H).status_code == 200

def test_cors():
    r = c.options("/farms", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"

def test_drought():
    setup()
    c.post("/ingest/soil", json={"farm_id":"f1","moisture_pct":10}, headers=H)
    c.post("/ingest/weather", json={"farm_id":"f1","humidity_pct":50,"rain_24h_mm":0,"temp_c":30}, headers=H)
    r = c.post("/orchestrate/f1", headers=H).json()
    assert r["risks"][0]["severity"] == "critical"
    a = r["plan"]["actions"][0]; assert a["kind"]=="irrigate" and a["status"]=="notified"
    assert len(r["tasks"])==1 and all(len(x["message"])<=160 for x in r["alerts"])
    # idempotent re-run: no duplicate plan/tasks
    r2 = c.post("/orchestrate/f1", headers=H).json(); assert r2["plan"] is None and len(c.get("/tasks?farm_id=f1", headers=H).json())==1
    assert r["advice_source"]=="offline"

def test_rain_skip_and_defer():
    setup()
    c.post("/ingest/soil", json={"farm_id":"f1","moisture_pct":12,"nitrogen_ppm":30}, headers=H)
    c.post("/ingest/weather", json={"farm_id":"f1","humidity_pct":50,"rain_24h_mm":30}, headers=H)
    r = c.post("/orchestrate/f1", headers=H).json()
    st = {a["kind"]: a["status"] for a in r["plan"]["actions"]}
    assert st["irrigate"]=="skipped" and st["fertilize"]=="deferred", st
    assert r["tasks"]==[]
    # rain clears -> auto-resume
    c.post("/ingest/weather", json={"farm_id":"f1","humidity_pct":50,"rain_24h_mm":0}, headers=H)
    r = c.post("/orchestrate/f1", headers=H).json()
    assert len(r["tasks"])==3, r["tasks"]   # irrigate + 2 urea doses

def test_defer_existing_on_rain():
    setup()
    c.post("/ingest/soil", json={"farm_id":"f1","moisture_pct":20}, headers=H)
    c.post("/orchestrate/f1", headers=H)
    assert c.get("/tasks?farm_id=f1", headers=H).json()
    c.post("/ingest/weather", json={"farm_id":"f1","humidity_pct":50,"rain_24h_mm":30}, headers=H)
    r = c.post("/orchestrate/f1", headers=H).json(); assert r["weather_changes"]
    assert c.get("/tasks?farm_id=f1", headers=H).json()==[]

def test_budget():
    setup(); c.delete("/farms/f1", headers=H); mkfarm(budget=100)
    c.post("/ingest/soil", json={"farm_id":"f1","moisture_pct":10,"nitrogen_ppm":10}, headers=H)
    r = c.post("/orchestrate/f1", headers=H).json()
    assert all(a["status"]=="skipped" and a["hold_reason"]=="budget" for a in r["plan"]["actions"] if a["cost_inr"]>100)

def test_fungal_spray_gate():
    setup()
    c.post("/ingest/weather", json={"farm_id":"f1","humidity_pct":88,"canopy_wet":True,"temp_c":24,"rain_24h_mm":0,"wind_kph":5}, headers=H)
    c.post("/ingest/drone", json={"farm_id":"f1","ndvi":0.55,"ndvi_prev":0.72,"anomaly_score":0.8,"anomaly_signature":"lesion"}, headers=H)
    c.post("/ingest/soil", json={"farm_id":"f1","moisture_pct":40}, headers=H)
    r = c.post("/orchestrate/f1", headers=H).json()
    kinds = {a["kind"]: a for a in r["plan"]["actions"]}
    assert "scout" in kinds and kinds["spray"]["status"]=="awaiting_approval"
    assert len(r["escalations"])==1
    assert not any(kinds["spray"]["id"]==x["action_id"] for x in r["alerts"])   # no farmer SMS yet
    spray_task = next(t for t in c.get("/tasks?farm_id=f1", headers=H).json() if t["kind"]=="spray")
    assert c.patch(f"/tasks/{spray_task['id']}", json={"status":"done"}, headers=H).status_code==409  # GATE
    esc = r["escalations"][0]
    assert c.post(f"/escalations/{esc['id']}/resolve", json={"approved":True,"advice":"Mancozeb 2g/L"}, headers=H).status_code==200
    assert c.patch(f"/tasks/{spray_task['id']}", json={"status":"done"}, headers=H).status_code==200
    assert c.post(f"/escalations/{esc['id']}/resolve", json={"approved":True}, headers=H).status_code==409

def test_reject_and_direct_gate():
    setup()
    a = main.Action(farm_id="f1",plot_id="p",risk_id="r",kind="spray",title="s",what="w",when=main.now(),where="x")
    assert a.requires_expert_approval
    try: main.set_action_status(a,"notified"); assert False
    except main.SafetyGateError: pass
    try: main.set_action_status(a,"done"); assert False
    except main.SafetyGateError: pass
    a2 = main.Action(farm_id="f1",plot_id="p",risk_id="r",kind="scout",title="s",what="w",when=main.now(),where="x",requires_expert_approval=True)
    try: main.set_action_status(a2,"done"); assert False
    except main.SafetyGateError: pass

def test_seed_and_views():
    r = c.post("/demo/seed", headers=H).json(); assert r["ok"]
    assert len(c.get("/farms/farm-001/telemetry?hours=48", headers=H).json()["soil"])>=96
    assert c.get("/risks", headers=H).json() and c.get("/plans", headers=H).json()
    assert c.get("/risks?farm_id=farm-002", headers=H).json() and c.get("/farms/farm-001/plans", headers=H).json()
    assert c.get("/trace", headers=H).json() and c.get("/alerts", headers=H).json()
    assert c.get("/insights/stats", headers=H).json()["farms"]==2
    assert c.get("/insights/farm-001", headers=H).json()["source"]=="offline"
    assert c.post("/ingest/soil", json={"farm_id":"nope","moisture_pct":1}, headers=H).status_code==404
