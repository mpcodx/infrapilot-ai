import React from "react";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  icon: LucideIcon;
  color?: "cyan" | "emerald" | "amber" | "rose";
  progress?: number;
}

export default function MetricCard({
  title,
  value,
  subValue,
  icon: Icon,
  color = "cyan",
  progress,
}: MetricCardProps) {
  const colorMap = {
    cyan: {
      text: "text-cyan-400",
      bg: "bg-cyan-500/10",
      border: "border-cyan-500/30",
      bar: "bg-cyan-500",
    },
    emerald: {
      text: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/30",
      bar: "bg-emerald-500",
    },
    amber: {
      text: "text-amber-400",
      bg: "bg-amber-500/10",
      border: "border-amber-500/30",
      bar: "bg-amber-500",
    },
    rose: {
      text: "text-rose-400",
      bg: "bg-rose-500/10",
      border: "border-rose-500/30",
      bar: "bg-rose-500",
    },
  };

  const scheme = colorMap[color] || colorMap.cyan;

  return (
    <div className="bg-piops-900 border border-piops-800 rounded-xl p-5 shadow-sm hover:border-piops-700 transition">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          {title}
        </span>
        <div className={`p-2 rounded-lg ${scheme.bg} ${scheme.text} border ${scheme.border}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="text-2xl font-bold text-white tracking-tight mb-1">{value}</div>
      {subValue && <div className="text-xs text-slate-400">{subValue}</div>}
      {progress !== undefined && (
        <div className="w-full bg-piops-800 h-1.5 rounded-full mt-3 overflow-hidden">
          <div
            className={`h-full ${scheme.bar} transition-all duration-500`}
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      )}
    </div>
  );
}
