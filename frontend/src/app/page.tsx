"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sprout,
  ShieldCheck,
  CalendarCheck,
  Radio,
  Cpu,
  ArrowRight,
  Database,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Sparkles,
  Smartphone,
} from "lucide-react";
import { api } from "@/lib/api";
import { StatsData } from "@/lib/types";

export default function LandingPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [seedDone, setSeedDone] = useState(false);

  const fetchStats = async () => {
    try {
      const res = await api.getStats();
      setStats(res.data);
    } catch (err) {
      console.debug("Failed to fetch stats:", err);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSeed = async () => {
    try {
      setSeeding(true);
      await api.seedDemo();
      setSeedDone(true);
      await fetchStats();
      setTimeout(() => setSeedDone(false), 3000);
    } catch (err) {
      console.error("Failed to seed demo data:", err);
    } finally {
      setSeeding(false);
    }
  };

  const agentCards = [
    {
      num: "01",
      name: "RiskDetectionAgent",
      role: "Deterministic Agronomic Sensing",
      desc: "Evaluates multi-sensor telemetry (soil moisture, nitrogen, Open-Meteo weather, and drone multispectral NDVI) to detect water stress, nitrogen deficiency, and fungal risks.",
      icon: Radio,
      badge: "Rule-Based",
      color: "border-blue-500/30 bg-blue-500/5",
    },
    {
      num: "02",
      name: "PlannerAgent",
      role: "Constraint-Aware Action Planner",
      desc: "Constructs cost-, weather-, and safety-constrained schedules. Skips irrigation on rain >12mm, defers fertilizer on rain ≥20mm, splits urea doses over 14 days, and gates chemical sprays.",
      icon: CalendarCheck,
      badge: "Weather & Cost Gated",
      color: "border-amber-500/30 bg-amber-500/5",
    },
    {
      num: "03",
      name: "ExecutorAgent",
      role: "Safety Enforcement & Dispatcher",
      desc: "Creates farm tasks and dispatches SMS alerts (≤160 chars). Enforces non-negotiable chemical gating: zero spray tasks or alerts are allowed until an agronomist approves the escalation.",
      icon: ShieldCheck,
      badge: "Chemical Gating",
      color: "border-emerald-500/30 bg-emerald-500/5",
    },
    {
      num: "04",
      name: "LLMAdvisor",
      role: "Actionable Plain Advice",
      desc: "Translates complex agro-climatic conditions into plain-language farmer priorities under 120 words. Features 100% offline fallback to deterministic agronomic templates.",
      icon: Cpu,
      badge: "Zero-LLM Fallback",
      color: "border-purple-500/30 bg-purple-500/5",
    },
  ];

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-forest-900 via-forest-800 to-forest-950 text-white rounded-2xl p-8 sm:p-12 shadow-xl border border-forest-700 relative overflow-hidden">
        <div className="max-w-3xl space-y-6 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-leaf/20 text-leaf border border-leaf/30 text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" /> Hackathon Problem Statement PS-6
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            Autonomous Farm Advisory & Multi-Agent Orchestration
          </h1>
          <p className="text-forest-200 text-lg sm:text-xl font-normal leading-relaxed">
            Built for smallholder farmers in rural, low-connectivity regions. Monitors soil, weather,
            and drone multispectral data, detects agronomic risks, enforces strict chemical safety
            gating, and coordinates field tasks and rural SMS alerts.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link
              href="/dashboard"
              className="touch-target px-6 py-3.5 rounded-xl bg-leaf hover:bg-leaf-light text-forest-950 font-bold text-base transition-all shadow-md flex items-center gap-2"
            >
              <span>Explore Dashboard</span>
              <ArrowRight className="w-5 h-5" />
            </Link>

            <button
              onClick={handleSeed}
              disabled={seeding}
              className="touch-target px-6 py-3.5 rounded-xl bg-forest-800/80 hover:bg-forest-700 text-white font-bold text-base transition-all border border-forest-600 shadow-sm flex items-center gap-2"
            >
              <Database className="w-5 h-5 text-leaf" />
              <span>{seeding ? "Seeding Database..." : seedDone ? "Seeded Successfully ✓" : "Load Demo Data"}</span>
            </button>
          </div>
        </div>

        {/* Decorative background glow */}
        <div className="absolute right-0 bottom-0 w-96 h-96 bg-leaf/10 rounded-full blur-3xl pointer-events-none" />
      </section>

      {/* Live Insights Counters */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-extrabold text-forest-900 tracking-tight flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-forest-700" />
            <span>Live System Metrics</span>
          </h2>
          <span className="text-xs text-forest-700 font-semibold uppercase tracking-wider">
            Auto-refreshes every 15s
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl p-5 border border-wheat-400 shadow-sm">
            <span className="text-xs font-bold uppercase text-forest-600 block">Monitored Farms</span>
            <span className="text-3xl font-black text-forest-950 mt-1 block">
              {loadingStats ? "..." : stats?.farms ?? 0}
            </span>
            <span className="text-xs text-forest-500 mt-1 block">Active field plots</span>
          </div>

          <div className="bg-white rounded-xl p-5 border border-wheat-400 shadow-sm">
            <span className="text-xs font-bold uppercase text-amber-700 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" /> Open Risks
            </span>
            <span className="text-3xl font-black text-amber-900 mt-1 block">
              {loadingStats ? "..." : stats?.open_risks ?? 0}
            </span>
            <span className="text-xs text-amber-700 mt-1 block">
              {stats?.critical_risks ? `${stats.critical_risks} critical severity` : "No critical risks"}
            </span>
          </div>

          <div className="bg-white rounded-xl p-5 border border-wheat-400 shadow-sm">
            <span className="text-xs font-bold uppercase text-forest-600 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-forest-600" /> Active Tasks
            </span>
            <span className="text-3xl font-black text-forest-950 mt-1 block">
              {loadingStats ? "..." : stats?.tasks ?? 0}
            </span>
            <span className="text-xs text-forest-600 mt-1 block">
              {stats?.tasks_done ?? 0} completed
            </span>
          </div>

          <div className="bg-white rounded-xl p-5 border border-wheat-400 shadow-sm">
            <span className="text-xs font-bold uppercase text-purple-700 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> Pending Reviews
            </span>
            <span className="text-3xl font-black text-purple-950 mt-1 block">
              {loadingStats ? "..." : stats?.pending_escalations ?? 0}
            </span>
            <span className="text-xs text-purple-700 mt-1 block">Agronomist sign-offs</span>
          </div>
        </div>
      </section>

      {/* 4-Agent Pipeline Overview */}
      <section className="space-y-6">
        <div>
          <h2 className="text-2xl font-black text-forest-950 tracking-tight">
            Autonomous 4-Agent Architecture
          </h2>
          <p className="text-forest-700 text-sm mt-1">
            Deterministic rules guarantee safety and agronomic correctness, while autonomous agents coordinate end-to-end execution.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {agentCards.map((agent) => {
            const Icon = agent.icon;
            return (
              <div
                key={agent.name}
                className={`rounded-xl p-6 bg-white border border-wheat-400 shadow-sm transition-all hover:shadow-md flex flex-col justify-between`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="text-xs font-mono font-bold text-forest-400">
                      {agent.num}
                    </span>
                    <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-forest-100 text-forest-800 border border-forest-200">
                      {agent.badge}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-9 h-9 rounded-lg bg-forest-900 text-leaf flex items-center justify-center shrink-0">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-lg font-extrabold text-forest-950">{agent.name}</h3>
                      <p className="text-xs font-semibold text-forest-700">{agent.role}</p>
                    </div>
                  </div>

                  <p className="text-forest-800 text-sm leading-relaxed mt-3">{agent.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Feature Highlights & Core Invariants */}
      <section className="bg-white rounded-2xl p-8 border border-wheat-400 shadow-sm space-y-6">
        <h2 className="text-xl font-extrabold text-forest-950 tracking-tight">
          Engineering Invariants & Resilience Principles
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 font-bold text-forest-900">
              <ShieldCheck className="w-5 h-5 text-red-600" />
              <span>1. Strict Spray Gating</span>
            </div>
            <p className="text-xs text-forest-700 leading-relaxed">
              Chemical sprays can never reach <code>notified</code> or <code>done</code> without an approved
              Escalation record. Premature completion returns HTTP 409 and blocks notification dispatch.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 font-bold text-forest-900">
              <Smartphone className="w-5 h-5 text-emerald-600" />
              <span>2. Zero-LLM & Offline Resilient</span>
            </div>
            <p className="text-xs text-forest-700 leading-relaxed">
              100% functional without an Anthropic API key. Agronomic decisions are entirely rule-based,
              and offline templates guarantee 24/7 reliability in remote rural belts.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 font-bold text-forest-900">
              <Clock className="w-5 h-5 text-blue-600" />
              <span>3. Weather-Window Dynamic Resumption</span>
            </div>
            <p className="text-xs text-forest-700 leading-relaxed">
              Rain &gt;12mm automatically skips irrigation; heavy rain ≥20mm defers fertilizer 48h to prevent leaching.
              When weather clears, actions auto-resume without plan duplication.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
