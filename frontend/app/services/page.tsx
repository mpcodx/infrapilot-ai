"use client";

import { useEffect, useState } from "react";
import { Layers, Search, Radio, CheckCircle, AlertCircle } from "lucide-react";

export default function ServicesPage() {
  const [services, setServices] = useState<any[]>([]);
  const [ports, setPorts] = useState<any[]>([]);
  const [filter, setFilter] = useState("");
  const [tab, setTab] = useState<"services" | "ports">("services");

  useEffect(() => {
    Promise.all([fetch("/api/v1/services"), fetch("/api/v1/ports")])
      .then(async ([sRes, pRes]) => {
        if (sRes.ok) setServices(await sRes.json());
        if (pRes.ok) setPorts(await pRes.json());
      })
      .catch((e) => console.error(e));
  }, []);

  const filteredServices = services.filter((s) =>
    s.name.toLowerCase().includes(filter.toLowerCase())
  );
  const filteredPorts = ports.filter(
    (p) =>
      p.local_port.toString().includes(filter) ||
      (p.process_name && p.process_name.toLowerCase().includes(filter.toLowerCase()))
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Services & Ports</h1>
          <p className="text-sm text-slate-400">
            Systemd daemon status and active TCP/UDP listening sockets
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setTab("services")}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition ${
              tab === "services"
                ? "bg-cyan-500 text-black shadow-lg shadow-cyan-500/20"
                : "bg-piops-900 border border-piops-800 text-slate-300 hover:bg-piops-850"
            }`}
          >
            Services ({services.length})
          </button>
          <button
            onClick={() => setTab("ports")}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition ${
              tab === "ports"
                ? "bg-cyan-500 text-black shadow-lg shadow-cyan-500/20"
                : "bg-piops-900 border border-piops-800 text-slate-300 hover:bg-piops-850"
            }`}
          >
            Listening Ports ({ports.length})
          </button>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        <input
          type="text"
          placeholder={tab === "services" ? "Filter services by name..." : "Filter by port or process..."}
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-piops-900 border border-piops-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
        />
      </div>

      {/* Main Table */}
      <div className="bg-piops-900 border border-piops-800 rounded-2xl overflow-hidden shadow-sm">
        {tab === "services" ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-piops-850 text-slate-400 uppercase font-mono">
                <tr>
                  <th className="py-3 px-4">Service Name</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Load State</th>
                  <th className="py-3 px-4">Sub State</th>
                  <th className="py-3 px-4">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-piops-800 font-mono">
                {filteredServices.map((s, idx) => (
                  <tr key={idx} className="hover:bg-piops-850/50">
                    <td className="py-3 px-4 text-slate-200 font-semibold">{s.name}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                          s.is_active
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                        }`}
                      >
                        {s.is_active ? (
                          <CheckCircle className="w-3 h-3" />
                        ) : (
                          <AlertCircle className="w-3 h-3" />
                        )}
                        {s.active_state}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{s.load_state}</td>
                    <td className="py-3 px-4 text-cyan-400">{s.sub_state}</td>
                    <td className="py-3 px-4 text-slate-400 font-sans truncate max-w-xs">
                      {s.description || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-piops-850 text-slate-400 uppercase font-mono">
                <tr>
                  <th className="py-3 px-4">Protocol</th>
                  <th className="py-3 px-4">Local Port</th>
                  <th className="py-3 px-4">Bind Address</th>
                  <th className="py-3 px-4">State</th>
                  <th className="py-3 px-4">Associated Process</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-piops-800 font-mono">
                {filteredPorts.map((p, idx) => (
                  <tr key={idx} className="hover:bg-piops-850/50">
                    <td className="py-3 px-4 uppercase text-slate-400 font-semibold">{p.protocol}</td>
                    <td className="py-3 px-4 text-cyan-400 font-bold">{p.local_port}</td>
                    <td className="py-3 px-4 text-slate-300">{p.local_address}</td>
                    <td className="py-3 px-4 text-emerald-400">{p.status}</td>
                    <td className="py-3 px-4 text-slate-200">
                      {p.process_name || (p.pid ? `PID: ${p.pid}` : "—")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
