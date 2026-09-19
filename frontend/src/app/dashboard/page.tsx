"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sprout,
  Droplets,
  Wind,
  CloudRain,
  Sun,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Clock,
  ArrowRight,
  ShieldAlert,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  Area,
  ComposedChart,
} from "recharts";
import { api, ApiError } from "@/lib/api";
import { Farm, TelemetryData, Risk, Task, Action } from "@/lib/types";
import { SeverityBadge } from "@/components/SeverityBadge";

export default function DashboardPage() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [selectedFarmId, setSelectedFarmId] = useState<string>("");
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [risks, setRisks] = useState<Risk[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshingWeather, setRefreshingWeather] = useState(false);
  const [weatherMsg, setWeatherMsg] = useState<string | null>(null);
  const [taskError, setTaskError] = useState<string | null>(null);
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);

  // Load farms
  useEffect(() => {
    async function loadFarms() {
      try {
        const res = await api.getFarms();
        setFarms(res.data);
        if (res.data.length > 0 && !selectedFarmId) {
          setSelectedFarmId(res.data[0].id);
        }
      } catch (err) {
        console.error("Failed to load farms:", err);
      }
    }
    loadFarms();
  }, []);

  // Load farm data whenever selectedFarmId changes
  const loadFarmData = async (farmId: string) => {
    if (!farmId) return;
    try {
      setLoading(true);
      const [telemRes, risksRes, tasksRes] = await Promise.all([
        api.getTelemetry(farmId, 48),
        api.getRisks(farmId, "open"),
        api.getTasks(farmId),
      ]);
      setTelemetry(telemRes.data);
      setRisks(risksRes.data);
      setTasks(tasksRes.data);
    } catch (err) {
      console.error("Failed to load farm details:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedFarmId) {
      loadFarmData(selectedFarmId);
      const interval = setInterval(() => {
        if (document.visibilityState === "visible") {
          loadFarmData(selectedFarmId);
        }
      }, 15000);
      return () => clearInterval(interval);
    }
  }, [selectedFarmId]);

  const handleRefreshWeather = async () => {
    if (!selectedFarmId) return;
    try {
      setRefreshingWeather(true);
      setWeatherMsg(null);
      const res = await api.refreshWeather(selectedFarmId);
      setWeatherMsg(`Weather updated from ${res.data.source}`);
      await loadFarmData(selectedFarmId);
      setTimeout(() => setWeatherMsg(null), 4000);
    } catch (err) {
      console.error("Weather refresh failed:", err);
    } finally {
      setRefreshingWeather(false);
    }
  };

  const handleTaskStatus = async (task: Task, newStatus: any) => {
    try {
      setUpdatingTaskId(task.id);
      setTaskError(null);
      await api.patchTask(task.id, newStatus);
      await loadFarmData(selectedFarmId);
    } catch (err: any) {
      if (err instanceof ApiError && err.status === 409) {
        setTaskError(`Waiting for agronomist approval: This spray task cannot be completed until approved.`);
      } else {
        setTaskError(err.message || "Failed to update task");
      }
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const currentFarm = farms.find((f) => f.id === selectedFarmId);

  // Prepare chart data (combine soil moisture & weather evaporation)
  const chartData = React.useMemo(() => {
    if (!telemetry) return [];
    const map = new Map<string, { time: string; moisture: number; evap: number }>();
    
    (telemetry.soil || []).forEach((s) => {
      const timeStr = new Date(s.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const entry = map.get(timeStr) || { time: timeStr, moisture: s.moisture_pct, evap: 0 };
      entry.moisture = s.moisture_pct;
      map.set(timeStr, entry);
    });

    (telemetry.weather || []).forEach((w) => {
      const timeStr = new Date(w.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const entry = map.get(timeStr) || { time: timeStr, moisture: 0, evap: w.evaporation_mm };
      entry.evap = w.evaporation_mm;
      map.set(timeStr, entry);
    });

    return Array.from(map.values()).slice(-24); // Show last 24 points
  }, [telemetry]);

  const latestSoil = telemetry?.soil?.[telemetry.soil.length - 1];
  const latestWeather = telemetry?.weather?.[telemetry.weather.length - 1];

  return (
    <div className="space-y-8">
      {/* Top Bar: Farm Selector & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-wheat-400 shadow-sm">
        <div>
          <label htmlFor="farm-select" className="text-xs font-bold uppercase tracking-wider text-forest-700 block mb-1">
            Active Farm
          </label>
          <div className="flex items-center gap-3">
            <select
              id="farm-select"
              value={selectedFarmId}
              onChange={(e) => setSelectedFarmId(e.target.value)}
              className="touch-target bg-wheat-100 border border-wheat-400 rounded-xl px-4 py-2 font-bold text-forest-950 text-base focus:outline-none focus:ring-2 focus:ring-forest-800"
            >
              {farms.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name} ({f.id})
                </option>
              ))}
            </select>

            {currentFarm && (
              <span className="text-xs text-forest-700 font-medium hidden md:inline">
                Owner: <strong>{currentFarm.owner || "N/A"}</strong> | Budget: <strong>Rs{currentFarm.budget_inr}</strong>
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRefreshWeather}
            disabled={refreshingWeather}
            className="touch-target px-4 py-2 rounded-xl bg-forest-900 hover:bg-forest-800 text-white text-sm font-bold flex items-center gap-2 shadow-sm transition-all"
          >
            <RefreshCw className={`w-4 h-4 text-leaf ${refreshingWeather ? "animate-spin" : ""}`} />
            <span>{refreshingWeather ? "Refreshing..." : "Refresh Forecast"}</span>
          </button>
        </div>
      </div>

      {weatherMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{weatherMsg}</span>
        </div>
      )}

      {taskError && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-800 rounded-xl text-sm font-semibold flex items-center gap-3 shadow-sm">
          <ShieldAlert className="w-5 h-5 text-red-600 shrink-0" />
          <div className="flex-1">
            <p className="font-bold">Chemical Spray Gating Notice</p>
            <p className="text-xs text-red-700 mt-0.5">{taskError}</p>
          </div>
          <Link
            href="/escalations"
            className="touch-target px-3 py-1.5 rounded-lg bg-red-800 text-white text-xs font-bold uppercase tracking-wider hover:bg-red-900"
          >
            Go to Escalations
          </Link>
        </div>
      )}

      {/* Telemetry Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 border border-wheat-400 shadow-sm">
          <div className="flex items-center justify-between text-forest-600 mb-2">
            <span className="text-xs font-bold uppercase">Soil Moisture</span>
            <Droplets className="w-4 h-4 text-blue-500" />
          </div>
          <span className="text-3xl font-black text-forest-950">
            {latestSoil ? `${latestSoil.moisture_pct}%` : "--"}
          </span>
          <span className="text-xs text-forest-500 mt-1 block">
            {latestSoil && latestSoil.moisture_pct < 15
              ? "Critical deficit"
              : latestSoil && latestSoil.moisture_pct < 25
              ? "High water stress"
              : "Adequate zone"}
          </span>
        </div>

        <div className="bg-white rounded-xl p-5 border border-wheat-400 shadow-sm">
          <div className="flex items-center justify-between text-forest-600 mb-2">
            <span className="text-xs font-bold uppercase">Soil Nitrogen</span>
            <Sprout className="w-4 h-4 text-emerald-500" />
          </div>
          <span className="text-3xl font-black text-forest-950">
            {latestSoil?.nitrogen_ppm ? `${latestSoil.nitrogen_ppm} ppm` : "--"}
          </span>
          <span className="text-xs text-forest-500 mt-1 block">
            {latestSoil?.nitrogen_ppm && latestSoil.nitrogen_ppm < 40 ? "Deficiency detected" : "Optimal"}
          </span>
        </div>

        <div className="bg-white rounded-xl p-5 border border-wheat-400 shadow-sm">
          <div className="flex items-center justify-between text-forest-600 mb-2">
            <span className="text-xs font-bold uppercase">24h Rain Forecast</span>
            <CloudRain className="w-4 h-4 text-indigo-500" />
          </div>
          <span className="text-3xl font-black text-forest-950">
            {latestWeather ? `${latestWeather.rain_24h_mm} mm` : "0 mm"}
          </span>
          <span className="text-xs text-forest-500 mt-1 block">
            {latestWeather && latestWeather.rain_24h_mm > 12 ? "Irrigation skip window" : "Normal"}
          </span>
        </div>

        <div className="bg-white rounded-xl p-5 border border-wheat-400 shadow-sm">
          <div className="flex items-center justify-between text-forest-600 mb-2">
            <span className="text-xs font-bold uppercase">Humidity & Temp</span>
            <Sun className="w-4 h-4 text-amber-500" />
          </div>
          <span className="text-3xl font-black text-forest-950">
            {latestWeather ? `${latestWeather.temp_c?.toFixed(0) || 25}°C` : "--"}
          </span>
          <span className="text-xs text-forest-500 mt-1 block">
            {latestWeather ? `RH ${latestWeather.humidity_pct}%` : "--"}
          </span>
        </div>
      </div>

      {/* 48-Hour Recharts Telemetry Chart */}
      <section className="bg-white rounded-2xl p-6 border border-wheat-400 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-black text-forest-950 tracking-tight">
              48-Hour Soil Moisture & Evaporation Telemetry
            </h2>
            <p className="text-xs text-forest-600">
              Sensor readings over time with evaporation rate (ET0) tracking
            </p>
          </div>
        </div>

        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#EED7B0" />
              <XAxis dataKey="time" stroke="#166534" fontSize={11} />
              <YAxis yAxisId="left" stroke="#14532D" fontSize={11} domain={[0, 60]} />
              <YAxis yAxisId="right" orientation="right" stroke="#D97706" fontSize={11} domain={[0, 10]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#FBF7EE",
                  borderColor: "#14532D",
                  borderRadius: "10px",
                  fontSize: "12px",
                }}
              />
              <Legend verticalAlign="top" height={36} />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="moisture"
                name="Soil Moisture (%)"
                stroke="#14532D"
                strokeWidth={3}
                dot={false}
              />
              <Area
                yAxisId="right"
                type="monotone"
                dataKey="evap"
                name="Evaporation (mm)"
                stroke="#D97706"
                fill="#D97706"
                fillOpacity={0.15}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Open Risks Strip & Today's Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Open Risks Strip */}
        <section className="bg-white rounded-2xl p-6 border border-wheat-400 shadow-sm space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-black text-forest-950 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <span>Open Agronomic Risks</span>
              </h2>
              <Link href="/risks" className="text-xs font-bold text-forest-800 hover:underline flex items-center gap-1">
                <span>View all</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {risks.length === 0 ? (
              <div className="p-8 text-center bg-wheat-100 rounded-xl border border-dashed border-wheat-400">
                <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
                <p className="text-sm font-bold text-forest-900">No active risks detected</p>
                <p className="text-xs text-forest-600 mt-1">All monitored plots are in optimal conditions.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {risks.slice(0, 4).map((r) => (
                  <div
                    key={r.id}
                    className="p-3.5 rounded-xl border border-wheat-400 bg-wheat-100/60 flex items-start justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <SeverityBadge severity={r.severity} />
                        <span className="text-xs font-bold text-forest-700 uppercase">{r.plot_id}</span>
                      </div>
                      <p className="text-sm font-bold text-forest-950">{r.summary}</p>
                    </div>
                    <span className="text-xs font-mono font-bold text-forest-600 bg-white px-2 py-1 rounded border border-wheat-400">
                      Score: {r.score}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Today's Tasks */}
        <section className="bg-white rounded-2xl p-6 border border-wheat-400 shadow-sm space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-black text-forest-950 flex items-center gap-2">
                <Clock className="w-5 h-5 text-forest-700" />
                <span>Today&apos;s Field Tasks</span>
              </h2>
              <Link href="/tasks" className="text-xs font-bold text-forest-800 hover:underline flex items-center gap-1">
                <span>Kanban Board</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {tasks.length === 0 ? (
              <div className="p-8 text-center bg-wheat-100 rounded-xl border border-dashed border-wheat-400">
                <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
                <p className="text-sm font-bold text-forest-900">No scheduled tasks</p>
                <p className="text-xs text-forest-600 mt-1">Run orchestration or simulator to generate tasks.</p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {tasks.slice(0, 4).map((t) => (
                  <div
                    key={t.id}
                    className="p-3.5 rounded-xl border border-wheat-400 bg-white flex items-center justify-between gap-3"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-extrabold uppercase text-forest-800">{t.kind}</span>
                        {t.requires_expert_approval && (
                          <span className="text-[10px] uppercase font-bold text-red-700 bg-red-100 px-1.5 py-0.5 rounded border border-red-200">
                            Gated
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-bold text-forest-950">{t.title}</p>
                    </div>

                    <button
                      onClick={() => handleTaskStatus(t, t.status === "done" ? "pending" : "done")}
                      disabled={updatingTaskId === t.id}
                      className={`touch-target px-3 py-1.5 rounded-lg text-xs font-bold uppercase transition-all ${
                        t.status === "done"
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          : "bg-forest-900 text-white hover:bg-forest-800"
                      }`}
                    >
                      {updatingTaskId === t.id ? "..." : t.status === "done" ? "Done ✓" : "Mark Done"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
