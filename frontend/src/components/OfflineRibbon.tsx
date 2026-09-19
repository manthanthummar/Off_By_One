"use client";

import React, { useEffect, useState } from "react";
import { WifiOff, RefreshCw } from "lucide-react";

interface Props {
  lastUpdated?: string | null;
  onRefresh?: () => void;
}

export function OfflineRibbon({ lastUpdated, onRefresh }: Props) {
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    if (typeof window !== "undefined") {
      setIsOffline(!navigator.onLine);
      window.addEventListener("online", handleOnline);
      window.addEventListener("offline", handleOffline);
    }

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div
      role="alert"
      className="bg-amber-700 text-white px-4 py-2 text-sm font-medium flex items-center justify-between shadow-md transition-all sticky top-0 z-50"
    >
      <div className="flex items-center gap-2">
        <WifiOff className="w-5 h-5 text-amber-200 shrink-0" />
        <span>
          <strong>Offline Mode</strong> — Viewing cached data
          {lastUpdated ? ` (Last updated: ${new Date(lastUpdated).toLocaleTimeString()})` : ""}
        </span>
      </div>
      {onRefresh && (
        <button
          onClick={onRefresh}
          className="touch-target px-3 py-1.5 bg-amber-800 hover:bg-amber-900 rounded text-xs font-semibold flex items-center gap-1.5 transition-colors border border-amber-600"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
