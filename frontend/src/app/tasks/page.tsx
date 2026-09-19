"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckSquare,
  Clock,
  PlayCircle,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
  ArrowRight,
  Filter,
  RefreshCw,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Farm, Task, TaskStatus } from "@/lib/types";

export default function TasksPage() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedFarm, setSelectedFarm] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [gateNotice, setGateNotice] = useState<string | null>(null);
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);

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

  const loadTasks = async () => {
    try {
      setLoading(true);
      const res = await api.getTasks(selectedFarm || undefined);
      setTasks(res.data);
    } catch (err) {
      console.error("Failed to load tasks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, [selectedFarm]);

  const updateStatus = async (task: Task, newStatus: TaskStatus) => {
    setGateNotice(null);
    setUpdatingTaskId(task.id);

    // Optimistic local update
    const previousTasks = [...tasks];
    setTasks((prev) =>
      prev.map((t) => (t.id === task.id ? { ...t, status: newStatus } : t))
    );

    try {
      await api.patchTask(task.id, newStatus);
    } catch (err: any) {
      // Rollback optimistic update
      setTasks(previousTasks);
      if (err instanceof ApiError && err.status === 409) {
        setGateNotice(
          "Waiting for agronomist approval: This chemical spray action requires expert review in the Escalations console before it can be completed."
        );
      } else {
        setGateNotice(err.message || "Failed to update task status.");
      }
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const columns: Array<{ id: TaskStatus; title: string; icon: React.ElementType; color: string; border: string }> = [
    { id: "pending", title: "Pending", icon: Clock, color: "text-blue-800 bg-blue-50", border: "border-blue-200" },
    { id: "in_progress", title: "In Progress", icon: PlayCircle, color: "text-amber-800 bg-amber-50", border: "border-amber-200" },
    { id: "done", title: "Done", icon: CheckCircle2, color: "text-emerald-800 bg-emerald-50", border: "border-emerald-200" },
    { id: "overdue", title: "Overdue", icon: AlertCircle, color: "text-red-800 bg-red-50", border: "border-red-200" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-forest-950 tracking-tight flex items-center gap-2.5">
            <CheckSquare className="w-7 h-7 text-forest-800" />
            <span>Field Tasks Kanban</span>
          </h1>
          <p className="text-sm text-forest-700 mt-1">
            Track and advance field tasks. Chemical actions remain safety-gated until expert approval.
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

      {/* Safety Gate Error Notice Banner */}
      {gateNotice && (
        <div className="p-4 bg-red-50 border-2 border-red-300 text-red-900 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm animate-fadeIn">
          <div className="flex items-start gap-3">
            <ShieldAlert className="w-6 h-6 text-red-700 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-extrabold text-sm">Chemical Spray Safety Gate Activated</h4>
              <p className="text-xs text-red-800 mt-0.5 leading-relaxed">{gateNotice}</p>
            </div>
          </div>
          <Link
            href="/escalations"
            className="touch-target px-4 py-2 bg-red-800 hover:bg-red-900 text-white rounded-xl text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 shrink-0 shadow-sm"
          >
            <span>Open Escalations</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Kanban Board */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {columns.map((col) => {
          const colTasks = tasks.filter((t) => t.status === col.id);
          const Icon = col.icon;

          return (
            <div
              key={col.id}
              className="bg-white rounded-2xl border border-wheat-400 shadow-sm p-4 flex flex-col min-h-[500px]"
            >
              {/* Column Header */}
              <div className={`p-3 rounded-xl ${col.color} ${col.border} border mb-4 flex items-center justify-between`}>
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4" />
                  <span className="text-xs font-black uppercase tracking-wider">{col.title}</span>
                </div>
                <span className="text-xs font-mono font-bold bg-white px-2 py-0.5 rounded shadow-sm">
                  {colTasks.length}
                </span>
              </div>

              {/* Tasks List */}
              <div className="space-y-3 flex-1 overflow-y-auto">
                {colTasks.length === 0 ? (
                  <div className="h-40 flex items-center justify-center text-center p-4 border border-dashed border-wheat-300 rounded-xl">
                    <span className="text-xs text-forest-400 font-medium">No {col.title.toLowerCase()} tasks</span>
                  </div>
                ) : (
                  colTasks.map((task) => (
                    <div
                      key={task.id}
                      className="p-4 rounded-xl border border-wheat-400 bg-wheat-100/50 hover:bg-wheat-100 transition-all shadow-sm space-y-3"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-[11px] font-black uppercase text-forest-800 bg-forest-200/70 px-2 py-0.5 rounded">
                            {task.kind}
                          </span>
                          {task.requires_expert_approval && (
                            <span className="text-[10px] font-extrabold uppercase text-red-800 bg-red-100 px-1.5 py-0.5 rounded border border-red-200">
                              Gated
                            </span>
                          )}
                        </div>
                        <h3 className="font-extrabold text-sm text-forest-950 leading-snug">{task.title}</h3>
                        <p className="text-xs text-forest-600">
                          Plot: <strong>{task.plot_id}</strong> | Farm: <strong>{task.farm_id}</strong>
                        </p>
                        <p className="text-[11px] text-forest-500 font-mono">
                          Due: {new Date(task.due).toLocaleDateString()} {new Date(task.due).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </p>
                      </div>

                      {/* State Transitions with 48px touch targets */}
                      <div className="pt-2 border-t border-wheat-300 flex flex-wrap gap-1.5">
                        {col.id !== "pending" && (
                          <button
                            onClick={() => updateStatus(task, "pending")}
                            disabled={updatingTaskId === task.id}
                            className="touch-target px-2.5 py-1 text-[11px] font-bold rounded-lg bg-wheat-200 hover:bg-wheat-300 text-forest-800 border border-wheat-400"
                          >
                            To Pending
                          </button>
                        )}
                        {col.id !== "in_progress" && col.id !== "done" && (
                          <button
                            onClick={() => updateStatus(task, "in_progress")}
                            disabled={updatingTaskId === task.id}
                            className="touch-target px-2.5 py-1 text-[11px] font-bold rounded-lg bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300"
                          >
                            Start
                          </button>
                        )}
                        {col.id !== "done" && (
                          <button
                            onClick={() => updateStatus(task, "done")}
                            disabled={updatingTaskId === task.id}
                            className="touch-target px-2.5 py-1 text-[11px] font-bold rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white shadow-sm"
                          >
                            {updatingTaskId === task.id ? "..." : "Complete ✓"}
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
