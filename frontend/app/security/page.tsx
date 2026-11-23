"use client";

import { useEffect, useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Info,
  RefreshCw,
  Loader2,
  CheckCircle,
} from "lucide-react";

export default function SecurityPage() {
  const [findings, setFindings] = useState<any[]>([]);
  const [scanning, setScanning] = useState(false);
  const [filter, setFilter] = useState("all");

  const fetchFindings = async () => {
    try {
      const res = await fetch("/api/v1/security/findings");
      if (res.ok) setFindings(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const triggerScan = async () => {
    setScanning(true);
    try {
      const res = await fetch("/api/v1/security/scan", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setFindings(data.findings || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setScanning(false);
    }
  };

  useEffect(() => {
    fetchFindings();
  }, []);

  const filtered = findings.filter((f) => {
    if (filter === "all") return true;
    return f.severity.toLowerCase() === filter.toLowerCase();
  });

  const criticalCount = findings.filter((f) => f.severity === "Critical").length;
  const highCount = findings.filter((f) => f.severity === "High").length;
  const mediumCount = findings.filter((f) => f.severity === "Medium").length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Defensive Security Center</h1>
          <p className="text-sm text-slate-400">
            Automated host configuration audit, exposed listening ports & container isolation checks
          </p>
        </div>
        <button
          onClick={triggerScan}
          disabled={scanning}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-black font-bold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition disabled:opacity-50"
        >
          {scanning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
          <span>Run Security Audit</span>
        </button>
      </div>

      {/* Severity Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div
          onClick={() => setFilter("all")}
          className={`cursor-pointer bg-piops-900 border p-4 rounded-xl transition ${
            filter === "all" ? "border-cyan-500 bg-cyan-500/5" : "border-piops-800 hover:border-piops-700"
          }`}
        >
          <div className="text-xs text-slate-400 mb-1">Total Findings</div>
          <div className="text-2xl font-bold text-white">{findings.length}</div>
        </div>

        <div
          onClick={() => setFilter("critical")}
          className={`cursor-pointer bg-piops-900 border p-4 rounded-xl transition ${
            filter === "critical" ? "border-rose-500 bg-rose-500/5" : "border-piops-800 hover:border-piops-700"
          }`}
        >
          <div className="text-xs text-rose-400 font-semibold mb-1">Critical</div>
          <div className="text-2xl font-bold text-rose-400">{criticalCount}</div>
        </div>

        <div
          onClick={() => setFilter("high")}
          className={`cursor-pointer bg-piops-900 border p-4 rounded-xl transition ${
            filter === "high" ? "border-amber-500 bg-amber-500/5" : "border-piops-800 hover:border-piops-700"
          }`}
        >
          <div className="text-xs text-amber-400 font-semibold mb-1">High</div>
          <div className="text-2xl font-bold text-amber-400">{highCount}</div>
        </div>

        <div
          onClick={() => setFilter("medium")}
          className={`cursor-pointer bg-piops-900 border p-4 rounded-xl transition ${
            filter === "medium" ? "border-indigo-500 bg-indigo-500/5" : "border-piops-800 hover:border-piops-700"
          }`}
        >
          <div className="text-xs text-indigo-400 font-semibold mb-1">Medium</div>
          <div className="text-2xl font-bold text-indigo-400">{mediumCount}</div>
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-4">
        {filtered.map((f) => (
          <div
            key={f.finding_id}
            className="bg-piops-900 border border-piops-800 rounded-2xl p-6 shadow-sm hover:border-piops-700 transition"
          >
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                      f.severity === "Critical"
                        ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                        : f.severity === "High"
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                        : f.severity === "Medium"
                        ? "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30"
                        : "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                    }`}
                  >
                    {f.severity}
                  </span>
                  <span className="font-mono text-xs text-slate-500">{f.finding_id}</span>
                  <span className="text-xs text-slate-400">• {f.category}</span>
                </div>
                <h3 className="text-base font-bold text-white">{f.title}</h3>
                <p className="text-xs text-slate-300 mt-1">{f.description}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t border-piops-800 text-xs">
              <div className="bg-piops-850 p-3 rounded-xl border border-piops-800">
                <span className="text-slate-500 text-[10px] uppercase font-mono block mb-1">
                  Evidence Detected
                </span>
                <span className="font-mono text-cyan-300">{f.evidence || "—"}</span>
                <div className="text-slate-400 text-[11px] mt-2">
                  Component: <span className="font-mono text-slate-200">{f.affected_component}</span>
                </div>
              </div>

              <div className="bg-piops-850 p-3 rounded-xl border border-piops-800">
                <span className="text-slate-500 text-[10px] uppercase font-mono block mb-1">
                  Recommended Remediation
                </span>
                <span className="text-emerald-400 font-medium">{f.recommended_fix || "—"}</span>
                <div className="text-slate-400 text-[11px] mt-2 leading-relaxed">
                  {f.explanation}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
