"use client";

import { useEffect, useState } from "react";
import { Box, Play, Square, RotateCw, Terminal, CheckCircle, AlertTriangle } from "lucide-react";
import ActionModal from "@/components/ActionModal";

export default function ContainersPage() {
  const [containers, setContainers] = useState<any[]>([]);
  const [selectedAction, setSelectedAction] = useState<{ type: string; target: string } | null>(
    null
  );

  const fetchContainers = async () => {
    try {
      const res = await fetch("/api/v1/containers");
      if (res.ok) setContainers(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchContainers();
    const interval = setInterval(fetchContainers, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Docker Containers</h1>
          <p className="text-sm text-slate-400">
            Container lifecycle telemetry and safe approval-based DevOps actions
          </p>
        </div>
      </div>

      {containers.length === 0 ? (
        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-12 text-center">
          <Box className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white mb-1">No Active Containers Found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Docker daemon is either operating without active containers or running in restricted
            SoloHost sandbox mode.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {containers.map((c) => (
            <div
              key={c.id}
              className="bg-piops-900 border border-piops-800 rounded-2xl p-5 shadow-sm hover:border-piops-700 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs text-cyan-400 font-semibold">{c.id}</span>
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                      c.status === "running"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                    }`}
                  >
                    {c.status === "running" ? (
                      <CheckCircle className="w-3 h-3" />
                    ) : (
                      <AlertTriangle className="w-3 h-3" />
                    )}
                    {c.status}
                  </span>
                </div>

                <div className="text-base font-bold text-white tracking-tight mb-1 truncate">
                  {c.name}
                </div>
                <div className="text-xs text-slate-400 font-mono truncate mb-4">{c.image}</div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-piops-850 p-3 rounded-xl border border-piops-800 mb-4">
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Restarts</span>
                    <span className="text-slate-200 font-bold">{c.restart_count}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase">Health</span>
                    <span className="text-cyan-400 capitalize">{c.health || "none"}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 border-t border-piops-800 flex items-center justify-between gap-2">
                <button
                  onClick={() => setSelectedAction({ type: "restart_container", target: c.name })}
                  className="flex-1 py-1.5 bg-piops-850 hover:bg-piops-800 border border-piops-800 text-xs text-slate-300 font-medium rounded-lg transition flex items-center justify-center gap-1.5"
                >
                  <RotateCw className="w-3 h-3 text-cyan-400" />
                  Restart
                </button>
                <button
                  onClick={() => setSelectedAction({ type: "docker_logs", target: c.name })}
                  className="flex-1 py-1.5 bg-piops-850 hover:bg-piops-800 border border-piops-800 text-xs text-slate-300 font-medium rounded-lg transition flex items-center justify-center gap-1.5"
                >
                  <Terminal className="w-3 h-3 text-emerald-400" />
                  Logs
                </button>
                <button
                  onClick={() => setSelectedAction({ type: "stop_container", target: c.name })}
                  className="py-1.5 px-3 bg-piops-850 hover:bg-rose-500/20 border border-piops-800 text-xs text-rose-400 font-medium rounded-lg transition"
                >
                  <Square className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedAction && (
        <ActionModal
          actionType={selectedAction.type}
          target={selectedAction.target}
          isOpen={true}
          onClose={() => setSelectedAction(null)}
        />
      )}
    </div>
  );
}
