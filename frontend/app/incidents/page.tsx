"use client";

import { AlertTriangle, CheckCircle, Clock } from "lucide-react";

export default function IncidentsPage() {
  const incidents = [
    {
      id: "INC-2026-001",
      title: "Host Memory Utilization Approaching 85% Threshold",
      severity: "Medium",
      status: "Resolved",
      time: "20 minutes ago",
      desc: "Automatic system snapshot registered elevated resident memory allocation across browser sub-processes.",
    },
    {
      id: "INC-2026-002",
      title: "Wildcard Bound Port Detection on Interface",
      severity: "Low",
      status: "Monitored",
      time: "1 hour ago",
      desc: "Listening socket on 0.0.0.0 audited during routine security cycle.",
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight">System Incidents</h1>
        <p className="text-sm text-slate-400">
          Automated event logs, anomalies and historical resolution timelines
        </p>
      </div>

      <div className="space-y-4">
        {incidents.map((inc) => (
          <div
            key={inc.id}
            className="bg-piops-900 border border-piops-800 rounded-2xl p-6 shadow-sm hover:border-piops-700 transition"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-cyan-400 font-semibold">{inc.id}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  {inc.severity}
                </span>
              </div>
              <span className="text-xs text-slate-500 flex items-center gap-1 font-mono">
                <Clock className="w-3.5 h-3.5" />
                {inc.time}
              </span>
            </div>

            <h3 className="text-base font-bold text-white mb-1">{inc.title}</h3>
            <p className="text-xs text-slate-400 mb-4">{inc.desc}</p>

            <div className="flex items-center justify-between pt-3 border-t border-piops-800 text-xs">
              <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                <CheckCircle className="w-3.5 h-3.5" />
                Status: {inc.status}
              </span>
              <span className="text-slate-500 font-mono">Logged by InfraPilot Watcher</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
