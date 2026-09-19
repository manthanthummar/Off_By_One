"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sprout,
  LayoutDashboard,
  AlertTriangle,
  CalendarDays,
  CheckSquare,
  ShieldCheck,
  Activity,
  MessageSquare,
  Menu,
  X,
  Database,
} from "lucide-react";
import { api } from "@/lib/api";

export function Navigation() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [seedSuccess, setSeedSuccess] = useState(false);

  const navItems = [
    { href: "/", label: "Home", icon: Sprout },
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/risks", label: "Risks", icon: AlertTriangle },
    { href: "/plans", label: "Plans", icon: CalendarDays },
    { href: "/tasks", label: "Tasks", icon: CheckSquare },
    { href: "/escalations", label: "Escalations", icon: ShieldCheck },
    { href: "/trace", label: "Pipeline Trace", icon: Activity },
    { href: "/alerts", label: "SMS Alerts", icon: MessageSquare },
  ];

  const handleSeed = async () => {
    try {
      setSeeding(true);
      await api.seedDemo();
      setSeedSuccess(true);
      setTimeout(() => setSeedSuccess(false), 3000);
      if (typeof window !== "undefined") {
        window.location.reload();
      }
    } catch (err) {
      console.error("Seed failed:", err);
    } finally {
      setSeeding(false);
    }
  };

  return (
    <header className="bg-forest-900 text-white shadow-lg sticky top-0 z-40 border-b border-forest-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 touch-target">
            <div className="w-10 h-10 rounded-lg bg-leaf flex items-center justify-center text-forest-950 font-bold shadow">
              <Sprout className="w-6 h-6" />
            </div>
            <div>
              <span className="font-extrabold text-xl tracking-tight text-white block">
                Farm<span className="text-leaf">Sense</span>
              </span>
              <span className="text-xs text-forest-200 block -mt-1 font-medium">
                Farm-to-Field Multi-Agent
              </span>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`touch-target px-3.5 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                    active
                      ? "bg-forest-800 text-leaf shadow-sm border border-forest-700"
                      : "text-forest-100 hover:bg-forest-800/60 hover:text-white"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? "text-leaf" : "text-forest-300"}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Quick Actions */}
          <div className="hidden sm:flex items-center gap-3">
            <button
              onClick={handleSeed}
              disabled={seeding}
              className="touch-target px-3.5 py-2 rounded-lg text-xs font-bold uppercase tracking-wider bg-forest-800 hover:bg-forest-700 text-leaf border border-forest-700 flex items-center gap-2 transition-all shadow-sm"
              title="Loads deterministic 2-farm dataset with 48h telemetry"
            >
              <Database className="w-4 h-4" />
              <span>{seeding ? "Seeding..." : seedSuccess ? "Seeded ✓" : "Load Demo"}</span>
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="flex lg:hidden items-center gap-2">
            <button
              onClick={handleSeed}
              disabled={seeding}
              className="touch-target px-2.5 py-1.5 rounded-lg text-xs font-bold bg-forest-800 text-leaf border border-forest-700"
            >
              <Database className="w-4 h-4" />
            </button>
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="touch-target p-2 rounded-lg text-forest-200 hover:text-white hover:bg-forest-800"
              aria-label="Toggle navigation menu"
            >
              {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="lg:hidden bg-forest-950 border-b border-forest-800 px-4 pt-2 pb-6 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`touch-target w-full px-4 py-3 rounded-lg text-base font-semibold flex items-center gap-3 ${
                  active
                    ? "bg-forest-800 text-leaf"
                    : "text-forest-100 hover:bg-forest-900"
                }`}
              >
                <Icon className={`w-5 h-5 ${active ? "text-leaf" : "text-forest-300"}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      )}
    </header>
  );
}
