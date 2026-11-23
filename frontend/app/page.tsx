"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Cpu,
  HardDrive,
  MemoryStick,
  Network,
  ShieldAlert,
  Server,
  Box,
  Bot,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import MetricCard from "@/components/MetricCard";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

export default function OverviewPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [services, setServices] = useState<any[]>([]);
  const [containers, setContainers] = useState<any[]>([]);
  const [findings, setFindings] = useState<any[]>([]);
  const [aiSummary, setAiSummary] = useState<string>("Analyzing infrastructure state...");
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [mRes, hRes, sRes, cRes, fRes] = await Promise.all([
        fetch("/api/v1/system/metrics"),
        fetch("/api/v1/system/metrics/history?limit=20"),
        fetch("/api/v1/services"),
        fetch("/api/v1/containers"),
        fetch("/api/v1/security/findings"),
      ]);

      if (mRes.ok) {
        const mData = await mRes.json();
        setMetrics(mData);
      }
      if (hRes.ok) {
        const hData = await hRes.json();
        setHistory(hData);
      }
      if (sRes.ok) {
        const sData = await sRes.json();
        setServices(sData);
      }
      if (cRes.ok) {
        const cData = await cRes.json();
        setContainers(cData);
      }
      if (fRes.ok) {
        const fData = await fRes.json();
        setFindings(fData);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, []);

  const activeServices = services.filter((s) => s.is_active).length;
  const runningContainers = containers.filter((c) => c.status === "running").length;
  const criticalFindings = findings.filter(
    (f) => f.severity === "Critical" || f.severity === "High"
  ).length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title & Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Overview Dashboard</h1>
          <p className="text-sm text-slate-400">
            Real-time telemetry and infrastructure health directly from Linux host
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-3 py-1.5 bg-piops-850 hover:bg-piops-800 border border-piops-800 text-xs text-slate-300 rounded-lg transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="CPU Utilization"
          value={`${metrics?.cpu_percent ?? 0}%`}
          subValue={`${metrics?.cpu_count ?? 1} Cores @ ${metrics?.cpu_freq_current ? `${Math.round(metrics.cpu_freq_current)} MHz` : "active"}`}
          icon={Cpu}
          color={
            (metrics?.cpu_percent ?? 0) > 80
              ? "rose"
              : (metrics?.cpu_percent ?? 0) > 60
              ? "amber"
              : "cyan"
          }
          progress={metrics?.cpu_percent ?? 0}
        />
        <MetricCard
          title="Memory (RAM)"
          value={`${metrics?.ram_percent ?? 0}%`}
          subValue={`${Math.round((metrics?.ram_used ?? 0) / (1024 * 1024 * 1024))} GB / ${Math.round((metrics?.ram_total ?? 0) / (1024 * 1024 * 1024))} GB`}
          icon={MemoryStick}
          color={(metrics?.ram_percent ?? 0) > 85 ? "rose" : "emerald"}
          progress={metrics?.ram_percent ?? 0}
        />
        <MetricCard
          title="Primary Storage"
          value={`${metrics?.disk_percent ?? 0}%`}
          subValue={`${Math.round((metrics?.disk_used ?? 0) / (1024 * 1024 * 1024))} GB / ${Math.round((metrics?.disk_total ?? 0) / (1024 * 1024 * 1024))} GB`}
          icon={HardDrive}
          color={(metrics?.disk_percent ?? 0) > 90 ? "rose" : "cyan"}
          progress={metrics?.disk_percent ?? 0}
        />
        <MetricCard
          title="Network I/O Rate"
          value={`↑ ${Math.round(((metrics?.upload_rate_bps ?? 0) * 8) / 1024)} Kbps`}
          subValue={`↓ ${Math.round(((metrics?.download_rate_bps ?? 0) * 8) / 1024)} Kbps`}
          icon={Network}
          color="emerald"
        />
      </div>

      {/* Operational Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-piops-900 border border-piops-800 rounded-xl p-4 flex items-center gap-4">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-xl">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">
              {activeServices} <span className="text-xs text-slate-400 font-normal">/ {services.length} active</span>
            </div>
            <div className="text-xs text-slate-400">Systemd Services</div>
          </div>
        </div>

        <div className="bg-piops-900 border border-piops-800 rounded-xl p-4 flex items-center gap-4">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
            <Box className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">
              {runningContainers} <span className="text-xs text-slate-400 font-normal">/ {containers.length} online</span>
            </div>
            <div className="text-xs text-slate-400">Docker Containers</div>
          </div>
        </div>

        <div className="bg-piops-900 border border-piops-800 rounded-xl p-4 flex items-center gap-4">
          <div className={`p-3 rounded-xl border ${criticalFindings > 0 ? "bg-rose-500/10 border-rose-500/20 text-rose-400" : "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"}`}>
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-white">
              {findings.length}{" "}
              <span className={`text-xs font-semibold ${criticalFindings > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                ({criticalFindings} high/critical)
              </span>
            </div>
            <div className="text-xs text-slate-400">Security Audit Findings</div>
          </div>
        </div>
      </div>

      {/* Main Charts & Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-piops-900 border border-piops-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                Live CPU & Memory Pressure Trends
              </h2>
              <p className="text-xs text-slate-400">
                Synchronized historical utilization sampled directly from system kernel
              </p>
            </div>
            <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded">
              LIVE
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history.length ? history : [{ timestamp: "now", cpu_percent: metrics?.cpu_percent || 0, ram_percent: metrics?.ram_percent || 0 }]}>
                <defs>
                  <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="ramGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#182440" />
                <XAxis dataKey="timestamp" stroke="#64748b" tick={false} />
                <YAxis stroke="#64748b" domain={[0, 100]} unit="%" />
                <Tooltip contentStyle={{ backgroundColor: "#0c1322", borderColor: "#24365d", borderRadius: "8px" }} />
                <Area type="monotone" dataKey="cpu_percent" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#cpuGradient)" name="CPU %" />
                <Area type="monotone" dataKey="ram_percent" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#ramGradient)" name="RAM %" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AI Health Summary Card */}
        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-lg">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">AI Health Assessment</h3>
                <span className="text-[11px] text-slate-400">Powered by Ollama (qwen3:4b)</span>
              </div>
            </div>
            <div className="text-xs text-slate-300 leading-relaxed bg-piops-850 p-4 rounded-xl border border-piops-800">
              {metrics ? (
                <div>
                  <p className="mb-2">
                    Host <span className="font-mono text-cyan-400 font-semibold">{metrics.hostname}</span> is running{" "}
                    <span className="text-slate-200 font-medium">{metrics.os_name}</span> with status{" "}
                    <span className="text-emerald-400 font-bold uppercase">{metrics.status}</span>.
                  </p>
                  <p>
                    Current CPU pressure is {metrics.cpu_percent}%, RAM usage is {metrics.ram_percent}%, and root disk allocation is{" "}
                    {metrics.disk_percent}%.
                  </p>
                </div>
              ) : (
                "Collecting initial telemetry..."
              )}
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-piops-800 flex items-center justify-between text-xs text-slate-400">
            <span>Uptime: {metrics ? `${Math.round(metrics.uptime_seconds / 3600)} hrs` : "..."}</span>
            <span className="text-cyan-400 font-medium">Safe Mode: Read-Only</span>
          </div>
        </div>
      </div>
    </div>
  );
}
