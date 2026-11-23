"use client";

import { useEffect, useState } from "react";
import { Gauge, AlertTriangle, CheckCircle, Zap, RefreshCw } from "lucide-react";
import MetricCard from "@/components/MetricCard";

export default function PerformancePage() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchPerformance = async () => {
    try {
      const res = await fetch("/api/v1/performance/report");
      if (res.ok) setReport(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPerformance();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            Performance & Capacity Engine
          </h1>
          <p className="text-sm text-slate-400">
            Automated bottleneck detection and estimated infrastructure headroom
          </p>
        </div>
        <button
          onClick={fetchPerformance}
          className="flex items-center gap-2 px-3 py-1.5 bg-piops-850 hover:bg-piops-800 border border-piops-800 text-xs text-slate-300 rounded-lg transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Recalculate Headroom</span>
        </button>
      </div>

      {/* Headroom Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            CPU Headroom Available
          </div>
          <div className="text-3xl font-black text-cyan-400 mb-1">
            {report?.cpu_headroom_percent ?? 0}%
          </div>
          <p className="text-xs text-slate-400">Unused processor capacity before saturation</p>
          <div className="w-full bg-piops-800 h-1.5 rounded-full mt-4 overflow-hidden">
            <div
              className="h-full bg-cyan-500"
              style={{ width: `${report?.cpu_headroom_percent ?? 0}%` }}
            />
          </div>
        </div>

        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            RAM Headroom Available
          </div>
          <div className="text-3xl font-black text-emerald-400 mb-1">
            {report?.ram_headroom_percent ?? 0}%
          </div>
          <p className="text-xs text-slate-400">
            {report
              ? `${Math.round(report.ram_headroom_bytes / (1024 * 1024 * 1024))} GB available RAM`
              : "..."}
          </p>
          <div className="w-full bg-piops-800 h-1.5 rounded-full mt-4 overflow-hidden">
            <div
              className="h-full bg-emerald-500"
              style={{ width: `${report?.ram_headroom_percent ?? 0}%` }}
            />
          </div>
        </div>

        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Storage Headroom Available
          </div>
          <div className="text-3xl font-black text-indigo-400 mb-1">
            {report?.disk_headroom_percent ?? 0}%
          </div>
          <p className="text-xs text-slate-400">
            {report
              ? `${Math.round(report.disk_headroom_bytes / (1024 * 1024 * 1024))} GB free on root`
              : "..."}
          </p>
          <div className="w-full bg-piops-800 h-1.5 rounded-full mt-4 overflow-hidden">
            <div
              className="h-full bg-indigo-500"
              style={{ width: `${report?.disk_headroom_percent ?? 0}%` }}
            />
          </div>
        </div>
      </div>

      {/* Bottlenecks and Recommendations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4 text-amber-400 font-bold text-base">
            <AlertTriangle className="w-5 h-5" />
            <span>Identified Bottlenecks & Pressure Points</span>
          </div>
          <ul className="space-y-3">
            {report?.bottlenecks?.map((b: string, idx: number) => (
              <li
                key={idx}
                className="text-xs text-slate-300 bg-piops-850 p-3 rounded-xl border border-piops-800 flex items-start gap-2.5"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1 shrink-0" />
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4 text-emerald-400 font-bold text-base">
            <Zap className="w-5 h-5" />
            <span>Capacity Recommendations</span>
          </div>
          <ul className="space-y-3">
            {report?.recommendations?.map((r: string, idx: number) => (
              <li
                key={idx}
                className="text-xs text-slate-300 bg-piops-850 p-3 rounded-xl border border-piops-800 flex items-start gap-2.5"
              >
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Assumptions & Limitations Note */}
      <div className="bg-piops-900/50 border border-piops-800 p-4 rounded-xl text-xs text-slate-400">
        <span className="text-slate-300 font-semibold">Engine Scope & Constraints: </span>
        {report?.assumptions}
      </div>
    </div>
  );
}
