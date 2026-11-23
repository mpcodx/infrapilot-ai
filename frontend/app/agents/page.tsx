"use client";

import { useEffect, useState } from "react";
import { Radio, Terminal, Copy, Check, CheckCircle, Clock } from "lucide-react";

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [copied, setCopied] = useState(false);

  const fetchAgents = async () => {
    try {
      const res = await fetch("/api/v1/agents");
      if (res.ok) setAgents(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, []);

  const installCommand =
    "python3 -m venv .infrapilot && .infrapilot/bin/pip install psutil requests && python3 -m agent.piops_agent.client --url http://127.0.0.1:8000 --secret dev-agent-secret-key-change-for-production";

  const copyInstall = () => {
    navigator.clipboard.writeText(installCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight">Registered Linux Agents</h1>
        <p className="text-sm text-slate-400">
          Decoupled monitoring agents deployed on external hosts reporting via authenticated HTTPS
        </p>
      </div>

      {/* Standalone Agent Installation Box */}
      <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-2">
          <Terminal className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-bold text-white">Deploy External Host Agent (Mode B)</h2>
        </div>
        <p className="text-xs text-slate-400 mb-4 max-w-2xl leading-relaxed">
          SoloHost runs in a secure, sandboxed container without unrestricted host access. To
          monitor remote physical Linux servers, run this lightweight restricted agent:
        </p>
        <div className="bg-piops-950 p-4 rounded-xl border border-piops-800 flex items-center justify-between font-mono text-xs text-emerald-400">
          <span className="truncate mr-4">$ {installCommand}</span>
          <button
            onClick={copyInstall}
            className="px-3 py-1.5 bg-piops-850 hover:bg-piops-800 text-slate-300 rounded-lg text-xs font-sans font-medium transition flex items-center gap-1.5 shrink-0"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
        </div>
      </div>

      {/* Agents Table */}
      <div className="bg-piops-900 border border-piops-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-piops-800 flex items-center justify-between">
          <span className="text-xs font-bold text-white uppercase tracking-wider">
            Connected Nodes ({agents.length})
          </span>
          <span className="text-xs text-slate-400">Auto-refreshing every 5s</span>
        </div>

        {agents.length === 0 ? (
          <div className="p-12 text-center">
            <Radio className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-base font-bold text-white mb-1">No External Agents Registered</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Run the agent command on any Linux node with Python to securely stream telemetry to this
              dashboard.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-piops-850 text-slate-400 uppercase font-mono">
                <tr>
                  <th className="py-3 px-4">Agent ID</th>
                  <th className="py-3 px-4">Hostname</th>
                  <th className="py-3 px-4">OS Info</th>
                  <th className="py-3 px-4">IP Address</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Last Heartbeat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-piops-800 font-mono">
                {agents.map((a, idx) => (
                  <tr key={idx} className="hover:bg-piops-850/50">
                    <td className="py-3 px-4 text-cyan-400 font-bold">{a.agent_id}</td>
                    <td className="py-3 px-4 text-white font-semibold">{a.hostname}</td>
                    <td className="py-3 px-4 text-slate-300">{a.os_info || "Linux"}</td>
                    <td className="py-3 px-4 text-slate-400">{a.ip_address || "127.0.0.1"}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle className="w-3 h-3" />
                        ONLINE
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {a.last_heartbeat ? new Date(a.last_heartbeat).toLocaleTimeString() : "—"}
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
