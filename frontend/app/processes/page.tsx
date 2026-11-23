"use client";

import { useEffect, useState } from "react";
import { Cpu, Search, RefreshCw } from "lucide-react";

export default function ProcessesPage() {
  const [processes, setProcesses] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchProcesses = async () => {
    try {
      const res = await fetch("/api/v1/processes?limit=60");
      if (res.ok) setProcesses(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProcesses();
    const interval = setInterval(fetchProcesses, 4000);
    return () => clearInterval(interval);
  }, []);

  const filtered = processes.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.pid.toString().includes(search) ||
      (p.username && p.username.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Active Processes</h1>
          <p className="text-sm text-slate-400">
            Real-time process telemetry ranked by CPU and resident memory usage
          </p>
        </div>
        <button
          onClick={fetchProcesses}
          className="flex items-center gap-2 px-3 py-1.5 bg-piops-850 hover:bg-piops-800 border border-piops-800 text-xs text-slate-300 rounded-lg transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        <input
          type="text"
          placeholder="Filter by name, PID, or user..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-piops-900 border border-piops-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
        />
      </div>

      <div className="bg-piops-900 border border-piops-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-piops-850 text-slate-400 uppercase font-mono">
              <tr>
                <th className="py-3 px-4">PID</th>
                <th className="py-3 px-4">Process Name</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">CPU %</th>
                <th className="py-3 px-4">Memory %</th>
                <th className="py-3 px-4">RSS (MB)</th>
                <th className="py-3 px-4">Command Preview</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-piops-800 font-mono">
              {filtered.map((p) => (
                <tr key={p.pid} className="hover:bg-piops-850/50">
                  <td className="py-3 px-4 text-cyan-400 font-bold">{p.pid}</td>
                  <td className="py-3 px-4 text-slate-200 font-semibold">{p.name}</td>
                  <td className="py-3 px-4 text-slate-400">{p.username}</td>
                  <td className="py-3 px-4 font-bold text-white">
                    <span
                      className={`px-2 py-0.5 rounded ${
                        p.cpu_percent > 30 ? "bg-rose-500/20 text-rose-400" : ""
                      }`}
                    >
                      {p.cpu_percent}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300">{p.memory_percent.toFixed(1)}%</td>
                  <td className="py-3 px-4 text-slate-300">
                    {Math.round((p.memory_rss || 0) / (1024 * 1024))} MB
                  </td>
                  <td className="py-3 px-4 text-slate-500 truncate max-w-xs">{p.cmdline || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
