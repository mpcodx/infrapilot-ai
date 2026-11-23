"use client";

import { useEffect, useState } from "react";
import { Server, Cpu, HardDrive, Network, Clock, ShieldCheck, Terminal } from "lucide-react";

export default function InfrastructurePage() {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    fetch("/api/v1/system/metrics")
      .then((r) => r.json())
      .then((d) => setMetrics(d))
      .catch((e) => console.error(e));
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight">Host Infrastructure</h1>
        <p className="text-sm text-slate-400">Detailed hardware specs and Linux kernel telemetry</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* System & OS Info */}
        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4 text-cyan-400 font-bold text-base">
            <Server className="w-5 h-5" />
            <span>Host & Operating System</span>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-piops-800">
              <span className="text-slate-400">Hostname</span>
              <span className="font-mono text-white font-semibold">{metrics?.hostname || "..."}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-piops-800">
              <span className="text-slate-400">Distribution</span>
              <span className="text-white">{metrics?.os_name || "Linux"}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-piops-800">
              <span className="text-slate-400">Kernel Version</span>
              <span className="font-mono text-cyan-300">{metrics?.kernel_version || "..."}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-piops-800">
              <span className="text-slate-400">System Uptime</span>
              <span className="text-white">
                {metrics ? `${(metrics.uptime_seconds / 3600).toFixed(1)} hours` : "..."}
              </span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-400">Load Average (1, 5, 15m)</span>
              <span className="font-mono text-slate-300">
                {metrics?.load_avg ? metrics.load_avg.join(", ") : "0.0, 0.0, 0.0"}
              </span>
            </div>
          </div>
        </div>

        {/* CPU Telemetry */}
        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4 text-indigo-400 font-bold text-base">
            <Cpu className="w-5 h-5" />
            <span>Processor Configuration</span>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-piops-800">
              <span className="text-slate-400">Logical Cores</span>
              <span className="text-white font-bold">{metrics?.cpu_count || 1}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-piops-800">
              <span className="text-slate-400">CPU Frequency</span>
              <span className="text-white">
                {metrics?.cpu_freq_current ? `${Math.round(metrics.cpu_freq_current)} MHz` : "Standard"}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-piops-800">
              <span className="text-slate-400">Total Utilization</span>
              <span className="font-bold text-cyan-400">{metrics?.cpu_percent ?? 0}%</span>
            </div>
            <div className="pt-2">
              <div className="text-xs text-slate-400 mb-2">Per-Core Activity</div>
              <div className="grid grid-cols-4 gap-2">
                {metrics?.per_cpu_percent?.slice(0, 8).map((p: number, idx: number) => (
                  <div key={idx} className="bg-piops-850 p-2 rounded border border-piops-800 text-center">
                    <div className="text-[10px] text-slate-500 font-mono">Core {idx}</div>
                    <div className="text-xs font-bold text-cyan-300">{p}%</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Disk Partitions */}
      <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4 text-cyan-400 font-bold text-base">
          <HardDrive className="w-5 h-5" />
          <span>Mounted Storage Partitions</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-piops-850 text-slate-400 uppercase font-mono">
              <tr>
                <th className="py-3 px-4">Device</th>
                <th className="py-3 px-4">Mountpoint</th>
                <th className="py-3 px-4">FSType</th>
                <th className="py-3 px-4">Capacity</th>
                <th className="py-3 px-4">Used</th>
                <th className="py-3 px-4">Utilization</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-piops-800 font-mono">
              {metrics?.partitions?.map((p: any, idx: number) => (
                <tr key={idx} className="hover:bg-piops-850/50">
                  <td className="py-3 px-4 text-slate-300 font-semibold">{p.device}</td>
                  <td className="py-3 px-4 text-cyan-400">{p.mountpoint}</td>
                  <td className="py-3 px-4 text-slate-400">{p.fstype}</td>
                  <td className="py-3 px-4 text-slate-300">
                    {Math.round(p.total / (1024 * 1024 * 1024))} GB
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    {Math.round(p.used / (1024 * 1024 * 1024))} GB
                  </td>
                  <td className="py-3 px-4 font-bold text-white">{p.percent}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
