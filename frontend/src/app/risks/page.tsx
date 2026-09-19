"use client";

import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  Filter,
  X,
  ChevronRight,
  Sparkles,
  Info,
  CalendarCheck,
  CheckCircle2,
} from "lucide-react";
import { api } from "@/lib/api";
import { Farm, Risk, Severity, Action } from "@/lib/types";
import { SeverityBadge } from "@/components/SeverityBadge";

export default function RisksPage() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [risks, setRisks] = useState<Risk[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedFarm, setSelectedFarm] = useState<string>("");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("");
  const [selectedKind, setSelectedKind] = useState<string>("");
  const [selectedStatus, setSelectedStatus] = useState<string>("open");

  // Slide-over drawer state
  const [drawerRisk, setDrawerRisk] = useState<Risk | null>(null);
  const [linkedActions, setLinkedActions] = useState<Action[]>([]);
  const [loadingActions, setLoadingActions] = useState(false);

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

  const loadRisks = async () => {
    try {
      setLoading(true);
      const res = await api.getRisks(
        selectedFarm || undefined,
        selectedStatus || undefined,
        selectedSeverity || undefined
      );
      let filtered = res.data;
      if (selectedKind) {
        filtered = filtered.filter((r) => r.kind === selectedKind);
      }
      setRisks(filtered);
    } catch (err) {
      console.error("Failed to load risks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRisks();
  }, [selectedFarm, selectedSeverity, selectedKind, selectedStatus]);

  const openDrawer = async (risk: Risk) => {
    setDrawerRisk(risk);
    try {
      setLoadingActions(true);
      const plansRes = await api.getPlans(risk.farm_id);
      const allActions: Action[] = [];
      (plansRes.data || []).forEach((p) => {
        (p.actions || []).forEach((a) => {
          if (a.risk_id === risk.id) {
            allActions.push(a);
          }
        });
      });
      setLinkedActions(allActions);
    } catch (err) {
      console.error("Failed to load linked actions:", err);
    } finally {
      setLoadingActions(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-forest-950 tracking-tight flex items-center gap-2.5">
          <AlertTriangle className="w-7 h-7 text-amber-600" />
          <span>Agronomic Risk Ledger</span>
        </h1>
        <p className="text-sm text-forest-700 mt-1">
          Sensor and imagery risks identified by RiskDetectionAgent with deterministic agronomic rules.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-2xl border border-wheat-400 shadow-sm flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2 text-xs font-extrabold uppercase text-forest-800 tracking-wider">
          <Filter className="w-4 h-4 text-forest-600" />
          <span>Filters:</span>
        </div>

        {/* Farm Filter */}
        <select
          value={selectedFarm}
          onChange={(e) => setSelectedFarm(e.target.value)}
          className="touch-target bg-wheat-100 border border-wheat-400 rounded-xl px-3 py-1.5 text-xs font-bold text-forest-950"
        >
          <option value="">All Farms</option>
          {farms.map((f) => (
            <option key={f.id} value={f.id}>
              {f.name}
            </option>
          ))}
        </select>

        {/* Severity Filter */}
        <select
          value={selectedSeverity}
          onChange={(e) => setSelectedSeverity(e.target.value)}
          className="touch-target bg-wheat-100 border border-wheat-400 rounded-xl px-3 py-1.5 text-xs font-bold text-forest-950"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        {/* Kind Filter */}
        <select
          value={selectedKind}
          onChange={(e) => setSelectedKind(e.target.value)}
          className="touch-target bg-wheat-100 border border-wheat-400 rounded-xl px-3 py-1.5 text-xs font-bold text-forest-950"
        >
          <option value="">All Risk Kinds</option>
          <option value="water_stress">Water Stress</option>
          <option value="nutrient_deficiency">Nutrient Deficiency</option>
          <option value="fungal_disease">Fungal Disease</option>
          <option value="vegetation_decline">Vegetation Decline</option>
        </select>

        {/* Status Filter */}
        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="touch-target bg-wheat-100 border border-wheat-400 rounded-xl px-3 py-1.5 text-xs font-bold text-forest-950"
        >
          <option value="">All Statuses</option>
          <option value="open">Open Only</option>
          <option value="resolved">Resolved</option>
        </select>

        {(selectedFarm || selectedSeverity || selectedKind || selectedStatus !== "open") && (
          <button
            onClick={() => {
              setSelectedFarm("");
              setSelectedSeverity("");
              setSelectedKind("");
              setSelectedStatus("open");
            }}
            className="touch-target px-3 py-1 text-xs font-bold text-forest-700 hover:text-red-700 flex items-center gap-1"
          >
            <X className="w-3.5 h-3.5" />
            <span>Reset Filters</span>
          </button>
        )}
      </div>

      {/* Risks Table / List */}
      <div className="bg-white rounded-2xl border border-wheat-400 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-forest-600 font-bold text-sm">
            Loading agronomic risks...
          </div>
        ) : risks.length === 0 ? (
          <div className="p-12 text-center text-forest-700">
            <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto mb-2" />
            <p className="font-bold text-base">No matching risks found</p>
            <p className="text-xs text-forest-500 mt-1">Try adjusting the filter criteria above.</p>
          </div>
        ) : (
          <div className="divide-y divide-wheat-300">
            {risks.map((risk) => (
              <div
                key={risk.id}
                className="p-5 hover:bg-wheat-100/50 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <SeverityBadge severity={risk.severity} />
                    <span className="text-xs font-black uppercase text-forest-900 bg-forest-100 px-2.5 py-0.5 rounded border border-forest-200">
                      {risk.kind.replace("_", " ")}
                    </span>
                    <span className="text-xs font-bold text-forest-600">
                      Plot: <strong>{risk.plot_id}</strong> | Farm: <strong>{risk.farm_id}</strong>
                    </span>
                    <span className="text-xs font-mono font-bold text-forest-700">
                      Score: {risk.score}
                    </span>
                  </div>

                  <p className="text-base font-extrabold text-forest-950">{risk.summary}</p>

                  {/* Evidence Pills */}
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    {Object.entries(risk.evidence || {}).map(([k, v]) => (
                      <span
                        key={k}
                        className="text-[11px] font-mono bg-wheat-200 text-forest-800 px-2 py-0.5 rounded border border-wheat-400"
                      >
                        {k}: <strong>{String(v)}</strong>
                      </span>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => openDrawer(risk)}
                  className="touch-target px-4 py-2 rounded-xl bg-forest-900 hover:bg-forest-800 text-white text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-sm shrink-0"
                >
                  <Sparkles className="w-4 h-4 text-leaf" />
                  <span>Explain Reasoning</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Slide-over Explain Reasoning Drawer */}
      {drawerRisk && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div
            className="absolute inset-0 bg-forest-950/60 backdrop-blur-sm transition-opacity"
            onClick={() => setDrawerRisk(null)}
          />

          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
            <div className="w-screen max-w-md bg-white border-l border-wheat-400 shadow-2xl p-6 overflow-y-auto space-y-6">
              {/* Drawer Header */}
              <div className="flex items-center justify-between border-b border-wheat-300 pb-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-forest-700" />
                  <h3 className="font-black text-lg text-forest-950">Agronomic Reasoning</h3>
                </div>
                <button
                  onClick={() => setDrawerRisk(null)}
                  className="touch-target p-2 rounded-lg text-forest-500 hover:bg-wheat-200 hover:text-forest-900"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Risk Summary */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={drawerRisk.severity} />
                  <span className="text-xs font-extrabold uppercase text-forest-700">
                    Status: {drawerRisk.status}
                  </span>
                </div>
                <h4 className="text-base font-extrabold text-forest-950">{drawerRisk.summary}</h4>
                <p className="text-xs text-forest-600 font-mono">ID: {drawerRisk.id}</p>
              </div>

              {/* Evidence & Threshold Breakdown */}
              <div className="space-y-3 bg-wheat-100 p-4 rounded-xl border border-wheat-400">
                <h5 className="text-xs font-black uppercase tracking-wider text-forest-900 flex items-center gap-1.5">
                  <Info className="w-4 h-4 text-forest-700" />
                  <span>Telemetry Evidence & Thresholds</span>
                </h5>
                <div className="space-y-2 text-xs">
                  {Object.entries(drawerRisk.evidence || {}).map(([key, val]) => (
                    <div key={key} className="flex items-center justify-between border-b border-wheat-300 pb-1">
                      <span className="font-mono text-forest-700">{key}</span>
                      <span className="font-bold text-forest-950">{String(val)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Linked Actions */}
              <div className="space-y-3">
                <h5 className="text-xs font-black uppercase tracking-wider text-forest-900 flex items-center gap-1.5">
                  <CalendarCheck className="w-4 h-4 text-forest-700" />
                  <span>Linked Orchestrated Actions</span>
                </h5>

                {loadingActions ? (
                  <p className="text-xs text-forest-600 font-bold">Loading linked actions...</p>
                ) : linkedActions.length === 0 ? (
                  <p className="text-xs text-forest-600 italic">No specific action planned yet.</p>
                ) : (
                  <div className="space-y-2.5">
                    {linkedActions.map((act) => (
                      <div key={act.id} className="p-3 bg-wheat-50 rounded-xl border border-wheat-300 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-extrabold uppercase text-forest-800">{act.kind}</span>
                          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-forest-200 text-forest-900">
                            {act.status}
                          </span>
                        </div>
                        <p className="text-sm font-bold text-forest-950">{act.title}</p>
                        <p className="text-xs text-forest-700 leading-relaxed">{act.what}</p>
                        {act.requires_expert_approval && (
                          <span className="text-[10px] font-bold text-red-700 bg-red-100 px-1.5 py-0.5 rounded border border-red-200 inline-block mt-1">
                            Requires Agronomist Sign-Off
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
