import React from "react";
import { AlertTriangle, AlertCircle, Info, CheckCircle2 } from "lucide-react";
import { Severity } from "@/lib/types";

interface Props {
  severity: Severity;
  showIcon?: boolean;
  className?: string;
}

export function SeverityBadge({ severity, showIcon = true, className = "" }: Props) {
  const configs: Record<Severity, { bg: string; text: string; border: string; icon: React.ElementType; label: string }> = {
    critical: {
      bg: "bg-red-100",
      text: "text-red-800",
      border: "border-red-300",
      icon: AlertTriangle,
      label: "Critical",
    },
    high: {
      bg: "bg-orange-100",
      text: "text-orange-800",
      border: "border-orange-300",
      icon: AlertCircle,
      label: "High",
    },
    medium: {
      bg: "bg-amber-100",
      text: "text-amber-800",
      border: "border-amber-300",
      icon: Info,
      label: "Medium",
    },
    low: {
      bg: "bg-green-100",
      text: "text-green-800",
      border: "border-green-300",
      icon: CheckCircle2,
      label: "Low",
    },
  };

  const conf = configs[severity] || configs.low;
  const Icon = conf.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${conf.bg} ${conf.text} ${conf.border} ${className}`}
    >
      {showIcon && <Icon className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />}
      <span>{conf.label}</span>
    </span>
  );
}
