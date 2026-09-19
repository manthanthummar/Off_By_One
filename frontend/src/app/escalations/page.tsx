"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  User,
  History,
  Clock,
  Filter,
} from "lucide-react";
import { api } from "@/lib/api";
import { Farm, Escalation } from "@/lib/types";

export default function EscalationsPage() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [selectedFarm, setSelectedFarm] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"pending" | "history">("pending");
  const [loading, setLoading] = useState(true);

  // Form states per escalation
  const [adviceMap, setAdviceMap] = useState<Record<string, string>>({});
  const [resolverMap, setResolverMap] = useState<Record<string, string>>({});
  const [submittingId, setSubmittingId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ id: string; msg: string; type: "success" | "error" } | null>(null);

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

  const loadEscalations = async () => {
    try {
      setLoading(true);
      const res = await api.getEscalations(selectedFarm || undefined);
      setEscalations(res.data);
    } catch (err) {
      console.error("Failed to load escalations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEscalations();
  }, [selectedFarm]);

  const handleResolve = async (esc: Escalation, approved: boolean) => {
    try {
      setSubmittingId(esc.id);
      setFeedback(null);
      const advice = adviceMap[esc.id] || (approved ? "Approved: Follow standard dosage." : "Rejected: Adverse weather conditions.");
      const resolvedBy = resolverMap[esc.id] || "Dr. Agronomist";

      await api.resolveEscalation(esc.id, approved, advice, resolvedBy);
      setFeedback({
        id: esc.id,
        msg: `Escalation successfully ${approved ? "APPROVED" : "REJECTED"}. Farmer SMS notified.`,
        type: "success",
      });
      await loadEscalations();
    } catch (err: any) {
      setFeedback({
        id: esc.id,
        msg: err.message || "Failed to resolve escalation.",
        type: "error",
      });
    } finally {
      setSubmittingId(null);
    }
  };

  const pendingList = escalations.filter((e) => e.status === "pending");
  const historyList = escalations.filter((e) => e.status !== "pending");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-forest-950 tracking-tight flex items-center gap-2.5">
            <ShieldCheck className="w-7 h-7 text-forest-800" />
            <span>Agronomist Expert Console</span>
          </h1>
          <p className="text-sm text-forest-700 mt-1">
            Safety verification console for chemical sprays and high-risk agronomic interventions.
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

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-wheat-400 pb-2">
        <button
          onClick={() => setActiveTab("pending")}
          className={`touch-target px-5 py-2.5 rounded-xl font-extrabold text-sm flex items-center gap-2 transition-all ${
            activeTab === "pending"
              ? "bg-forest-900 text-leaf shadow-sm"
              : "bg-white text-forest-700 hover:bg-wheat-100 border border-wheat-400"
          }`}
        >
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span>Pending Reviews</span>
          <span className="ml-1 px-2 py-0.5 text-xs rounded-full bg-forest-800 text-white font-mono">
            {pendingList.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("history")}
          className={`touch-target px-5 py-2.5 rounded-xl font-extrabold text-sm flex items-center gap-2 transition-all ${
            activeTab === "history"
              ? "bg-forest-900 text-leaf shadow-sm"
              : "bg-white text-forest-700 hover:bg-wheat-100 border border-wheat-400"
          }`}
        >
          <History className="w-4 h-4" />
          <span>Resolution History</span>
          <span className="ml-1 px-2 py-0.5 text-xs rounded-full bg-forest-800 text-white font-mono">
            {historyList.length}
          </span>
        </button>
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="bg-white rounded-2xl p-12 text-center text-forest-600 font-bold text-sm border border-wheat-400">
          Loading escalations...
        </div>
      ) : activeTab === "pending" ? (
        /* Pending Escalations */
        pendingList.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-wheat-400">
            <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto mb-2" />
            <p className="font-bold text-base text-forest-950">No pending chemical reviews</p>
            <p className="text-xs text-forest-600 mt-1">
              All chemical actions are verified or no spray actions currently planned.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {pendingList.map((esc) => (
              <div
                key={esc.id}
                className="bg-white rounded-2xl border-2 border-purple-200 shadow-md p-6 sm:p-8 space-y-6"
              >
                {/* Escalation Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-wheat-300 pb-4">
                  <div>
                    <span className="text-xs font-black uppercase text-purple-900 bg-purple-100 px-3 py-1 rounded-full border border-purple-300">
                      Pending Agronomist Verification
                    </span>
                    <h3 className="text-lg font-black text-forest-950 mt-2">{esc.reason}</h3>
                  </div>
                  <div className="text-xs font-mono text-forest-600">
                    Farm: <strong>{esc.farm_id}</strong> | Action: <strong>{esc.action_id}</strong>
                  </div>
                </div>

                {feedback && feedback.id === esc.id && (
                  <div
                    className={`p-3 rounded-xl text-xs font-bold ${
                      feedback.type === "success"
                        ? "bg-emerald-100 text-emerald-900 border border-emerald-300"
                        : "bg-red-100 text-red-900 border border-red-300"
                    }`}
                  >
                    {feedback.msg}
                  </div>
                )}

                {/* Form Controls */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-wheat-50 p-5 rounded-xl border border-wheat-300">
                  <div>
                    <label className="text-xs font-extrabold uppercase tracking-wider text-forest-900 block mb-1">
                      Specific Agronomic Advice & Dosage
                    </label>
                    <textarea
                      rows={3}
                      value={adviceMap[esc.id] || ""}
                      onChange={(e) => setAdviceMap({ ...adviceMap, [esc.id]: e.target.value })}
                      placeholder="e.g. Mancozeb 2g/L. Spray morning only with PPE; pre-harvest interval 14 days."
                      className="w-full text-xs font-medium p-3 bg-white border border-wheat-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-forest-800 text-forest-950"
                    />
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="text-xs font-extrabold uppercase tracking-wider text-forest-900 block mb-1">
                        Agronomist Name / Registration
                      </label>
                      <input
                        type="text"
                        value={resolverMap[esc.id] || ""}
                        onChange={(e) => setResolverMap({ ...resolverMap, [esc.id]: e.target.value })}
                        placeholder="Dr. Agronomist (Plant Pathologist)"
                        className="w-full text-xs font-medium p-3 bg-white border border-wheat-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-forest-800 text-forest-950"
                      />
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-3 pt-1">
                      <button
                        onClick={() => handleResolve(esc, true)}
                        disabled={submittingId === esc.id}
                        className="touch-target flex-1 px-4 py-3 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 shadow transition-all"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        <span>{submittingId === esc.id ? "Processing..." : "Approve Spray"}</span>
                      </button>

                      <button
                        onClick={() => handleResolve(esc, false)}
                        disabled={submittingId === esc.id}
                        className="touch-target flex-1 px-4 py-3 rounded-xl bg-red-700 hover:bg-red-800 text-white text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 shadow transition-all"
                      >
                        <XCircle className="w-4 h-4" />
                        <span>{submittingId === esc.id ? "Processing..." : "Reject Action"}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      ) : (
        /* Resolution History */
        historyList.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-wheat-400">
            <p className="font-bold text-base text-forest-950">No resolution history recorded</p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-wheat-400 shadow-sm divide-y divide-wheat-300 overflow-hidden">
            {historyList.map((esc) => (
              <div key={esc.id} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-black uppercase px-2.5 py-0.5 rounded-full ${
                        esc.status === "approved"
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          : "bg-red-100 text-red-800 border border-red-300"
                      }`}
                    >
                      {esc.status}
                    </span>
                    <span className="text-xs font-bold text-forest-700">Farm: {esc.farm_id}</span>
                    <span className="text-xs text-forest-500 font-mono">
                      Resolved: {esc.resolved_at ? new Date(esc.resolved_at).toLocaleString() : "--"}
                    </span>
                  </div>
                  <h4 className="font-bold text-sm text-forest-950">{esc.reason}</h4>
                  <p className="text-xs text-forest-800 font-medium">
                    Advice: <em>&ldquo;{esc.advice}&rdquo;</em> — by <strong>{esc.resolved_by || "Agronomist"}</strong>
                  </p>
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  );
}
