"use client";

import React, { useEffect, useState } from "react";
import {
  MessageSquare,
  Smartphone,
  Send,
  Clock,
  Filter,
  RefreshCw,
  CheckCheck,
} from "lucide-react";
import { api } from "@/lib/api";
import { SmsAlert, Farm } from "@/lib/types";

export default function AlertsPage() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [alerts, setAlerts] = useState<SmsAlert[]>([]);
  const [selectedFarm, setSelectedFarm] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadFarms() {
      try {
        const res = await api.getFarms();
        setFarms(res.data);
      } catch (err) {
        console.error("Failed to load farms:", err);
      }
    }
    loadFarms();
  }, []);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const res = await api.getAlerts(selectedFarm || undefined, 100);
      setAlerts(res.data);
    } catch (err) {
      console.error("Failed to load alerts:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(() => {
      if (document.visibilityState === "visible") {
        loadAlerts();
      }
    }, 15000);
    return () => clearInterval(interval);
  }, [selectedFarm]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-forest-950 tracking-tight flex items-center gap-2.5">
            <MessageSquare className="w-7 h-7 text-forest-800" />
            <span>Rural SMS Dispatch Feed</span>
          </h1>
          <p className="text-sm text-forest-700 mt-1">
            Simulated low-bandwidth telecom feed. Every dispatched message strictly complies with the ≤160 character standard.
          </p>
        </div>

        {/* Filter & Refresh */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-white p-2 rounded-xl border border-wheat-400 shadow-sm">
            <Filter className="w-4 h-4 text-forest-700 ml-2" />
            <select
              value={selectedFarm}
              onChange={(e) => setSelectedFarm(e.target.value)}
              className="touch-target bg-transparent text-xs font-bold text-forest-950 pr-2 focus:outline-none"
            >
              <option value="">All Farms</option>
              {farms.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={loadAlerts}
            className="touch-target px-3 py-2 rounded-xl bg-white hover:bg-wheat-100 border border-wheat-400 text-forest-900 text-xs font-bold flex items-center gap-1.5 shadow-sm"
          >
            <RefreshCw className="w-4 h-4 text-forest-700" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Side: Feature Phone Mockup */}
        <div className="lg:col-span-5 flex justify-center sticky top-24">
          <div className="w-72 bg-neutral-900 rounded-[40px] p-4 shadow-2xl border-4 border-neutral-700 flex flex-col items-center space-y-4">
            {/* Phone Speaker */}
            <div className="w-16 h-1 bg-neutral-600 rounded-full mt-2" />

            {/* Monochrome / Backlit Screen */}
            <div className="w-full bg-[#9EA792] rounded-2xl p-4 shadow-inner border-2 border-neutral-800 text-neutral-950 font-mono text-xs min-h-[280px] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-neutral-700/40 pb-1 mb-2 text-[10px] font-bold">
                  <span>FarmSense 4G</span>
                  <span>100% 🔋</span>
                </div>

                <div className="space-y-2">
                  <span className="text-[10px] uppercase tracking-wider block font-bold text-neutral-800">
                    Latest Inbox (SMS)
                  </span>

                  {alerts.length > 0 ? (
                    <div className="bg-[#B2BAA7] p-2.5 rounded-lg border border-neutral-700/30 text-xs font-medium leading-tight">
                      <p>{alerts[0].message}</p>
                      <div className="flex items-center justify-between pt-2 mt-1 border-t border-neutral-700/20 text-[9px] text-neutral-800">
                        <span>To: {alerts[0].to || "+91 Farmer"}</span>
                        <span>{alerts[0].message.length}/160 chars</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-[11px] text-neutral-700 italic pt-4">No incoming SMS</p>
                  )}
                </div>
              </div>

              <div className="text-[9px] text-center text-neutral-800 font-bold border-t border-neutral-700/40 pt-1">
                Options | Back
              </div>
            </div>

            {/* Phone Keypad Mockup */}
            <div className="grid grid-cols-3 gap-2 w-full px-2">
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">1</div>
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">2</div>
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">3</div>
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">4</div>
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">5</div>
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">6</div>
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">7</div>
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">8</div>
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">9</div>
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">*</div>
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">0</div>
              <div className="h-8 bg-neutral-800 rounded-lg text-white font-bold text-xs flex items-center justify-center shadow">#</div>
            </div>
          </div>
        </div>

        {/* Right Side: Message Feed */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white rounded-2xl border border-wheat-400 shadow-sm p-6">
            <h2 className="text-lg font-black text-forest-950 mb-1">Dispatched Farmer Telegrams</h2>
            <p className="text-xs text-forest-600 mb-6">
              Messages generated by ExecutorAgent whenever field actions are notified or delayed.
            </p>

            {loading && alerts.length === 0 ? (
              <div className="p-8 text-center text-forest-600 font-bold text-xs">
                Loading SMS alerts...
              </div>
            ) : alerts.length === 0 ? (
              <div className="p-8 text-center bg-wheat-100 rounded-xl border border-dashed border-wheat-400">
                <Smartphone className="w-8 h-8 text-forest-500 mx-auto mb-2" />
                <p className="text-sm font-bold text-forest-950">No alerts sent yet</p>
                <p className="text-xs text-forest-600 mt-1">
                  Alerts are dispatched when tasks are scheduled or rescheduled.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {alerts.map((alert) => {
                  const len = alert.message.length;
                  const isSafe = len <= 160;

                  return (
                    <div
                      key={alert.id}
                      className="p-4 rounded-xl border border-wheat-400 bg-wheat-50 hover:bg-wheat-100/70 transition-colors space-y-2.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <Send className="w-3.5 h-3.5 text-forest-700" />
                          <span className="text-xs font-bold text-forest-900">
                            To: <strong>{alert.to || "Farmer Device"}</strong>
                          </span>
                          <span className="text-xs text-forest-600">({alert.farm_id})</span>
                        </div>

                        {/* 160-Character Badge Counter */}
                        <span
                          className={`text-xs font-mono font-bold px-2 py-0.5 rounded-full border ${
                            isSafe
                              ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                              : "bg-red-100 text-red-800 border-red-300"
                          }`}
                        >
                          {len}/160 chars
                        </span>
                      </div>

                      <p className="text-sm font-medium text-forest-950 leading-relaxed bg-white p-3 rounded-lg border border-wheat-300 shadow-sm font-sans">
                        {alert.message}
                      </p>

                      <div className="flex items-center justify-between text-[11px] text-forest-500 font-mono pt-1">
                        <span className="flex items-center gap-1">
                          <CheckCheck className="w-3.5 h-3.5 text-emerald-600" /> Dispatched
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(alert.ts).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
