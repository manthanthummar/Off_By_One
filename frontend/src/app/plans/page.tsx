"use client";

import React, { useEffect, useState } from "react";
import {
  CalendarDays,
  Clock,
  MapPin,
  IndianRupee,
  CloudSun,
  ShieldAlert,
  AlertCircle,
  PauseCircle,
  CheckCircle2,
  Filter,
} from "lucide-react";
import { api } from "@/lib/api";
import { Farm, Plan, Action } from "@/lib/types";

export default function PlansPage() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
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

  const loadPlans = async () => {
    try {
      setLoading(true);
      const res = await api.getPlans(selectedFarm || undefined);
      setPlans(res.data);
    } catch (err) {
      console.error("Failed to load plans:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlans();
  }, [selectedFarm]);

  const getStatusBadge = (action: Action) => {
    if (action.status === "deferred" || action.status === "skipped") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300">
          <PauseCircle className="w-3.5 h-3.5" />
          <span>Held ({action.hold_reason || action.status})</span>
        </span>
      );
    }
    if (action.status === "awaiting_approval") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-purple-100 text-purple-800 border border-purple-300">
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Awaiting Agronomist</span>
        </span>
      );
    }
    if (action.status === "done") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-300">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Done</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-100 text-blue-800 border border-blue-300">
        <Clock className="w-3.5 h-3.5" />
        <span>{action.status}</span>
      </span>
    );
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-forest-950 tracking-tight flex items-center gap-2.5">
            <CalendarDays className="w-7 h-7 text-forest-800" />
            <span>Action Plans Timeline</span>
          </h1>
          <p className="text-sm text-forest-700 mt-1">
            Cost-, safety-, and weather-constrained execution schedules produced by PlannerAgent.
          </p>
        </div>

        {/* Farm Filter */}
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
      </div>

      {loading ? (
        <div className="bg-white rounded-2xl p-12 text-center text-forest-600 font-bold text-sm border border-wheat-400">
          Loading action plans...
        </div>
      ) : plans.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-wheat-400">
          <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto mb-2" />
          <p className="font-bold text-base text-forest-950">No action plans recorded</p>
          <p className="text-xs text-forest-600 mt-1">
            Run orchestration or use the demo seeder to generate plans.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {plans.map((plan) => {
            const budgetPct =
              plan.budget_inr > 0
                ? Math.min(100, Math.round((plan.total_cost_inr / plan.budget_inr) * 100))
                : 0;

            return (
              <div
                key={plan.id}
                className="bg-white rounded-2xl border border-wheat-400 shadow-sm p-6 sm:p-8 space-y-6"
              >
                {/* Plan Header & Cost Gauge */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-wheat-300 pb-6">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-black uppercase tracking-wider bg-forest-900 text-leaf px-2.5 py-0.5 rounded">
                        Farm: {plan.farm_id}
                      </span>
                      <span className="text-xs font-mono text-forest-600">ID: {plan.id}</span>
                      <span className="text-xs text-forest-500">
                        {new Date(plan.created_at).toLocaleString()}
                      </span>
                    </div>
                    <h2 className="text-xl font-extrabold text-forest-950">
                      Orchestrated Plan ({plan.actions?.length || 0} Actions)
                    </h2>
                  </div>

                  {/* Cost vs Budget Gauge */}
                  <div className="bg-wheat-100 p-4 rounded-xl border border-wheat-400 w-full md:w-72 space-y-2">
                    <div className="flex items-center justify-between text-xs font-bold text-forest-900">
                      <span>Committed Budget</span>
                      <span>
                        Rs{plan.total_cost_inr.toFixed(0)} / Rs{plan.budget_inr.toFixed(0)}
                      </span>
                    </div>
                    <div className="w-full bg-wheat-300 h-2.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          budgetPct > 90 ? "bg-red-600" : budgetPct > 70 ? "bg-amber-600" : "bg-forest-700"
                        }`}
                        style={{ width: `${budgetPct}%` }}
                      />
                    </div>
                    <span className="text-[11px] text-forest-600 block text-right font-semibold">
                      {budgetPct}% budget allocated
                    </span>
                  </div>
                </div>

                {/* Weather Rationale Banner */}
                {plan.weather_rationale && plan.weather_rationale.length > 0 && (
                  <div className="bg-wheat-50 border border-wheat-300 rounded-xl p-4 space-y-1.5">
                    <div className="flex items-center gap-2 text-xs font-extrabold uppercase text-forest-900">
                      <CloudSun className="w-4 h-4 text-forest-700" />
                      <span>Weather Window Rationale</span>
                    </div>
                    <ul className="list-disc list-inside text-xs text-forest-800 space-y-1">
                      {plan.weather_rationale.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Timeline: WHAT / WHEN / WHERE */}
                <div className="space-y-4">
                  <h3 className="text-sm font-black uppercase tracking-wider text-forest-900">
                    Execution Schedule (WHAT / WHEN / WHERE)
                  </h3>

                  <div className="relative border-l-2 border-forest-700 ml-4 space-y-6 pl-6 py-2">
                    {(plan.actions || []).map((action) => (
                      <div key={action.id} className="relative group">
                        {/* Timeline Marker */}
                        <div className="absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full bg-forest-900 border-2 border-leaf shadow" />

                        <div className="bg-wheat-100/70 p-5 rounded-xl border border-wheat-400 space-y-3">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-black uppercase text-forest-900">
                                {action.kind}
                              </span>
                              <h4 className="text-base font-extrabold text-forest-950">
                                {action.title}
                              </h4>
                            </div>
                            {getStatusBadge(action)}
                          </div>

                          {/* Grid for WHAT / WHEN / WHERE */}
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs border-t border-wheat-300">
                            <div>
                              <span className="font-bold uppercase tracking-wider text-forest-600 block mb-0.5">
                                WHAT
                              </span>
                              <p className="font-semibold text-forest-950 leading-relaxed">
                                {action.what}
                              </p>
                            </div>

                            <div>
                              <span className="font-bold uppercase tracking-wider text-forest-600 block mb-0.5 flex items-center gap-1">
                                <Clock className="w-3.5 h-3.5" /> WHEN
                              </span>
                              <p className="font-semibold text-forest-950">
                                {new Date(action.when).toLocaleString()}
                              </p>
                              {action.deferred_until && (
                                <span className="text-amber-800 font-bold text-[11px] block mt-0.5">
                                  Deferred until: {new Date(action.deferred_until).toLocaleDateString()}
                                </span>
                              )}
                            </div>

                            <div>
                              <span className="font-bold uppercase tracking-wider text-forest-600 block mb-0.5 flex items-center gap-1">
                                <MapPin className="w-3.5 h-3.5" /> WHERE & COST
                              </span>
                              <p className="font-semibold text-forest-950">
                                {action.where || action.plot_id}
                              </p>
                              <span className="font-extrabold text-forest-900 block mt-0.5">
                                ~Rs{action.cost_inr.toFixed(0)}
                              </span>
                            </div>
                          </div>

                          {/* Safety Notes */}
                          {action.safety_notes && action.safety_notes.length > 0 && (
                            <div className="pt-2 border-t border-wheat-300">
                              <span className="text-[11px] font-bold uppercase text-forest-700 block mb-1">
                                Safety & Agronomic Protocols:
                              </span>
                              <ul className="list-disc list-inside text-xs text-forest-800 space-y-0.5">
                                {action.safety_notes.map((note, i) => (
                                  <li key={i}>{note}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
