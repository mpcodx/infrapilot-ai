"use client";

import { useEffect, useState } from "react";
import { Activity, Bell, ShieldCheck, Terminal } from "lucide-react";

export default function Header() {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    const fetchQuickMetrics = async () => {
      try {
        const res = await fetch("/api/v1/system/metrics");
        if (res.ok) {
          const data = await res.json();
          setMetrics(data);
        }
      } catch (e) {
        // Handled silently
      }
    };
    fetchQuickMetrics();
    const interval = setInterval(fetchQuickMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-piops-900/80 backdrop-blur border-b border-piops-800 px-8 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-4">
        <div className="text-sm font-medium text-slate-300 flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span>Host:</span>
          <span className="font-mono text-cyan-300 font-semibold">
            {metrics?.hostname || "local-node"}
          </span>
        </div>
        <div className="hidden md:flex items-center gap-2 text-xs text-slate-400 bg-piops-850 px-3 py-1 rounded-full border border-piops-800">
          <span>OS:</span>
          <span className="text-slate-200">{metrics?.os_name || "Linux"}</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Quick Indicators */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-md border border-emerald-500/20">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Defensive Audit: Ready</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs bg-cyan-500/10 text-cyan-400 px-3 py-1 rounded-md border border-cyan-500/20">
            <Activity className="w-3.5 h-3.5" />
            <span>Live Stream</span>
          </div>
        </div>
      </div>
    </header>
  );
}
