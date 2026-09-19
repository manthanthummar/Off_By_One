"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  Cpu,
  Clock,
  Radio,
  CalendarCheck,
  ShieldCheck,
  Zap,
  Filter,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { TraceEntry, Farm } from "@/lib/types";

export default function TracePage() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [selectedFarm, setSelectedFarm] = useState<string>("");
  const [traces, setTraces] = useState<TraceEntry[]>([]);
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

  const loadTraces = async () => {
    try {
      setLoading(true);
      const res = await api.getTrace(selectedFarm || undefined, 100);
      setTraces(res.data);
    } catch (err) {
      console.error("Failed to load trace entries:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTraces();
    const interval = setInterval(() => {
      if (document.visibilityState === "visible") {
        loadTraces();
      }
    }, 15000);
    return () => clearInterval(interval);
  }, [selectedFarm]);

  // Group traces by run_id
  const runGroups = React.useMemo(() => {
    const groups = new Map<string, TraceEntry[]>();
    traces.forEach((tr) => {
      const list = groups.get(tr.run_id) || [];
      list.push(tr);
      groups.set(tr.run_id, list);
    });
    return Array.from(groups.entries()).reverse(); // Most recent first
  }, [traces]);

  const getAgentIcon = (agent: string) => {
    if (agent.includes("RiskDetection")) return Radio;
    if (agent.includes("Planner")) return CalendarCheck;
    if (agent.includes("Executor")) return ShieldCheck;
    if (agent.includes("LLMAdvisor")) return Cpu;
    return Activity;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-forest-950 tracking-tight flex items-center gap-2.5">
            <Activity className="w-7 h-7 text-forest-800" />
            <span>Agent Orchestration Trace</span>
          </h1>
          <p className="text-sm text-forest-700 mt-1">
            Real-time multi-agent execution telemetry: inputs, outputs, execution latencies, and token costs.
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
            onClick={loadTraces}
            className="touch-target px-3 py-2 rounded-xl bg-white hover:bg-wheat-100 border border-wheat-400 text-forest-900 text-xs font-bold flex items-center gap-1.5 shadow-sm"
          >
            <RefreshCw className="w-4 h-4 text-forest-700" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {loading && traces.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center text-forest-600 font-bold text-sm border border-wheat-400">
          Loading agent execution traces...
        </div>
      ) : runGroups.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-wheat-400">
          <p className="font-bold text-base text-forest-950">No orchestration runs logged</p>
          <p className="text-xs text-forest-600 mt-1">
            Execute the simulator or trigger orchestration to see live agent traces.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {runGroups.map(([runId, entries]) => {
            const totalLatency = entries.reduce((acc, curr) => acc + curr.latency_ms, 0);
            const totalTokens = entries.reduce((acc, curr) => acc + curr.output_tokens, 0);
            const farmId = entries[0]?.farm_id || "";
            const runTime = entries[0]?.ts ? new Date(entries[0].ts).toLocaleString() : "";

            return (
              <div
                key={runId}
                className="bg-white rounded-2xl border border-wheat-400 shadow-sm p-6 sm:p-8 space-y-6"
              >
                {/* Run Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-wheat-300 pb-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-black uppercase tracking-wider bg-forest-900 text-leaf px-2.5 py-0.5 rounded">
                        Run: {runId}
                      </span>
                      <span className="text-xs font-bold text-forest-800">Farm: {farmId}</span>
                    </div>
                    <span className="text-xs text-forest-500 block">{runTime}</span>
                  </div>

                  <div className="flex items-center gap-4 text-xs font-bold">
                    <div className="flex items-center gap-1.5 bg-wheat-100 px-3 py-1.5 rounded-lg border border-wheat-300 text-forest-900">
                      <Clock className="w-4 h-4 text-forest-700" />
                      <span>Total: {totalLatency.toFixed(1)} ms</span>
                    </div>
                    <div className="flex items-center gap-1.5 bg-purple-50 px-3 py-1.5 rounded-lg border border-purple-200 text-purple-900">
                      <Zap className="w-4 h-4 text-purple-600" />
                      <span>{totalTokens} tokens</span>
                    </div>
                  </div>
                </div>

                {/* Pipeline Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {entries.map((entry) => {
                    const Icon = getAgentIcon(entry.agent);
                    return (
                      <div
                        key={entry.id}
                        className="bg-wheat-100/60 rounded-xl p-4 border border-wheat-300 space-y-3 flex flex-col justify-between"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="w-7 h-7 rounded-md bg-forest-900 text-leaf flex items-center justify-center shrink-0">
                              <Icon className="w-4 h-4" />
                            </div>
                            <span className="text-[11px] font-mono font-bold text-forest-600">
                              {entry.latency_ms.toFixed(1)} ms
                            </span>
                          </div>

                          <h4 className="font-extrabold text-sm text-forest-950">{entry.agent}</h4>

                          <div className="space-y-1.5 text-xs">
                            <div>
                              <span className="font-bold uppercase tracking-wider text-forest-600 text-[10px] block">
                                Input Summary:
                              </span>
                              <p className="text-forest-800 leading-snug">{entry.input_summary}</p>
                            </div>

                            <div className="pt-1">
                              <span className="font-bold uppercase tracking-wider text-forest-600 text-[10px] block">
                                Output Summary:
                              </span>
                              <p className="text-forest-950 font-medium leading-snug">
                                {entry.output_summary}
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="pt-2 border-t border-wheat-300 flex items-center justify-between text-[10px] font-mono text-forest-500">
                          <span>Tokens: {entry.output_tokens}</span>
                          <span>{new Date(entry.ts).toLocaleTimeString()}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
