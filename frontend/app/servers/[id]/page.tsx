"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Server,
  ArrowLeft,
  RefreshCw,
  Terminal,
  ShieldCheck,
  ShieldAlert,
  Activity,
  Layers,
  Cpu,
  Box,
  HardDrive,
  Clock,
  Play,
  RotateCw,
  Square,
  AlertTriangle,
  Lock,
  CheckCircle2,
  AlertCircle,
  FileText,
} from "lucide-react";

export default function ServerDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const serverId = params.id as string;

  const [server, setServer] = useState<any>(null);
  const [discoveryData, setDiscoveryData] = useState<any>(null);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "overview" | "processes" | "services" | "ports" | "containers" | "security" | "actions"
  >("overview");
  const [actionInProgress, setActionInProgress] = useState(false);

  // Action Preview & Approve State
  const [actionModal, setActionModal] = useState<{
    open: boolean;
    actionType: string;
    target: string;
    previewToken?: string;
    commandPreview?: string;
    result?: any;
    error?: string;
    loading: boolean;
  }>({
    open: false,
    actionType: "restart_service",
    target: "",
    loading: false,
  });

  const fetchServerDetails = async () => {
    try {
      setLoading(true);
      const [srvRes, metRes] = await Promise.all([
        fetch(`http://127.0.0.1:8000/api/v1/servers/${serverId}`),
        fetch(`http://127.0.0.1:8000/api/v1/servers/${serverId}/metrics?limit=10`),
      ]);

      if (srvRes.ok) {
        const srv = await srvRes.json();
        setServer(srv);
      }
      if (metRes.ok) {
        const met = await metRes.json();
        setMetrics(met);
      }
    } catch (err) {
      console.error("Failed to load server details", err);
    } finally {
      setLoading(false);
    }
  };

  const runDiscovery = async () => {
    try {
      setActionInProgress(true);
      const res = await fetch(`http://127.0.0.1:8000/api/v1/servers/${serverId}/discover`, {
        method: "POST",
      });
      if (res.ok) {
        const result = await res.json();
        setDiscoveryData(result.data);
        fetchServerDetails();
      } else {
        const err = await res.json();
        alert(`Discovery error: ${err.detail}`);
      }
    } finally {
      setActionInProgress(false);
    }
  };

  const handleTrustKey = async () => {
    if (!server?.host_key_fingerprint) return;
    try {
      setActionInProgress(true);
      const res = await fetch(`http://127.0.0.1:8000/api/v1/servers/${serverId}/trust-host-key`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fingerprint: server.host_key_fingerprint }),
      });
      if (res.ok) {
        alert("Host key trusted! Server is now authorized.");
        fetchServerDetails();
      }
    } finally {
      setActionInProgress(false);
    }
  };

  // Safe Action Workflow: Preview -> Confirm -> Execute
  const openActionPreview = async (actionType: string, target: string) => {
    setActionModal({
      open: true,
      actionType,
      target,
      loading: true,
    });
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/servers/${serverId}/action/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_type: actionType, target }),
      });
      if (res.ok) {
        const data = await res.json();
        setActionModal((prev) => ({
          ...prev,
          previewToken: data.action_id,
          commandPreview: data.command_preview,
          loading: false,
        }));
      } else {
        const err = await res.json();
        setActionModal((prev) => ({
          ...prev,
          error: err.detail || "Action validation failed",
          loading: false,
        }));
      }
    } catch (e: any) {
      setActionModal((prev) => ({
        ...prev,
        error: e.message,
        loading: false,
      }));
    }
  };

  const executeApprovedAction = async () => {
    if (!actionModal.previewToken) return;
    setActionModal((prev) => ({ ...prev, loading: true }));
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/servers/${serverId}/action/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action_id: actionModal.previewToken,
          confirmed: true,
        }),
      });
      if (res.ok) {
        const result = await res.json();
        setActionModal((prev) => ({
          ...prev,
          result,
          loading: false,
        }));
        // Refresh discovery
        runDiscovery();
      } else {
        const err = await res.json();
        setActionModal((prev) => ({
          ...prev,
          error: err.detail,
          loading: false,
        }));
      }
    } catch (e: any) {
      setActionModal((prev) => ({
        ...prev,
        error: e.message,
        loading: false,
      }));
    }
  };

  useEffect(() => {
    fetchServerDetails();
  }, [serverId]);

  if (loading && !server) {
    return (
      <div className="p-12 text-center text-slate-400 font-mono text-sm">
        Loading server telemetry...
      </div>
    );
  }

  if (!server) {
    return (
      <div className="p-12 text-center text-rose-400">
        Server not found or removed.
      </div>
    );
  }

  const isOnline = server.status === "online";
  const isUntrusted = server.status === "untrusted_host_key";
  const latestMetric = metrics[0] || null;

  return (
    <div className="space-y-6">
      {/* Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-piops-900 border border-piops-800 p-6 rounded-xl shadow-lg">
        <div>
          <Link
            href="/servers"
            className="text-xs text-slate-400 hover:text-cyan-400 inline-flex items-center gap-1.5 mb-2 font-mono transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Server Fleet
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Server className="w-6 h-6 text-cyan-400" />
              {server.name}
            </h1>
            <span
              className={`px-2.5 py-0.5 rounded text-xs font-semibold uppercase tracking-wider ${
                server.environment === "production"
                  ? "bg-purple-500/10 text-purple-400 border border-purple-500/30"
                  : "bg-blue-500/10 text-blue-400 border border-blue-500/30"
              }`}
            >
              {server.environment}
            </span>
          </div>
          <div className="text-xs text-slate-400 font-mono mt-1 flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-slate-500" />
            {server.username}@{server.hostname}:{server.ssh_port}
            <span className="text-slate-600">•</span>
            <Lock className="w-3.5 h-3.5 text-slate-500" />
            Auth: {server.auth_method}
          </div>
        </div>

        {/* Status & Action Buttons */}
        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider border ${
              isOnline
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : isUntrusted
                ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                : "bg-rose-500/10 text-rose-400 border-rose-500/30"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isOnline ? "bg-emerald-400 animate-pulse" : isUntrusted ? "bg-amber-400" : "bg-rose-400"
              }`}
            ></span>
            {server.status.replace("_", " ")}
          </span>

          {isUntrusted && (
            <button
              onClick={handleTrustKey}
              disabled={actionInProgress}
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-500 text-white flex items-center gap-1.5 shadow-lg shadow-amber-600/30"
            >
              <ShieldCheck className="w-4 h-4" />
              Trust Host Key
            </button>
          )}

          <button
            onClick={runDiscovery}
            disabled={actionInProgress}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-600/30 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${actionInProgress ? "animate-spin" : ""}`} />
            Run Discovery
          </button>
        </div>
      </div>

      {/* Host Key Verification Alert Banner */}
      {server.host_key_fingerprint && (
        <div className="bg-piops-950/80 border border-piops-800 p-3.5 rounded-xl flex items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className={`w-4 h-4 ${server.is_host_key_trusted ? "text-emerald-400" : "text-amber-400"}`} />
            <div>
              <span className="text-slate-300 font-semibold">
                SSH Host Key ({server.host_key_type || "ed25519"}):{" "}
              </span>
              <span className="font-mono text-slate-400">{server.host_key_fingerprint}</span>
            </div>
          </div>
          <span
            className={`text-[11px] font-mono px-2 py-0.5 rounded ${
              server.is_host_key_trusted
                ? "bg-emerald-500/10 text-emerald-400"
                : "bg-amber-500/10 text-amber-400"
            }`}
          >
            {server.is_host_key_trusted ? "TRUSTED & VERIFIED" : "UNTRUSTED"}
          </span>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-piops-800 text-xs gap-2">
        {[
          { id: "overview", label: "Overview & Specs", icon: Activity },
          { id: "processes", label: "Processes", icon: Cpu },
          { id: "services", label: "Systemd Services", icon: Layers },
          { id: "ports", label: "Listening Ports", icon: Terminal },
          { id: "containers", label: "Docker Containers", icon: Box },
          { id: "security", label: "Security Findings", icon: ShieldAlert },
          { id: "actions", label: "Safe Operations", icon: Play },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 border-b-2 font-medium transition ${
                isActive
                  ? "border-cyan-400 text-cyan-400 bg-cyan-500/5"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview & Specs */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-piops-900 border border-piops-800 p-4 rounded-xl">
              <div className="text-xs text-slate-400 font-medium">CPU Utilization</div>
              <div className="text-2xl font-bold text-white mt-1">
                {discoveryData?.cpu_percent ?? latestMetric?.cpu_percent ?? "--"}%
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-1">
                {discoveryData?.cpu_count || server.system_info?.cpu_count || 1} Cores Active
              </div>
            </div>

            <div className="bg-piops-900 border border-piops-800 p-4 rounded-xl">
              <div className="text-xs text-slate-400 font-medium">RAM Utilization</div>
              <div className="text-2xl font-bold text-white mt-1">
                {discoveryData?.ram_percent ?? latestMetric?.ram_percent ?? "--"}%
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-1">
                {discoveryData ? `${(discoveryData.ram_used / 1e9).toFixed(1)} GB used` : "--"}
              </div>
            </div>

            <div className="bg-piops-900 border border-piops-800 p-4 rounded-xl">
              <div className="text-xs text-slate-400 font-medium">Primary Storage</div>
              <div className="text-2xl font-bold text-white mt-1">
                {discoveryData?.disk_percent ?? latestMetric?.disk_percent ?? "--"}%
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-1">
                {discoveryData ? `${(discoveryData.disk_free / 1e9).toFixed(1)} GB free` : "--"}
              </div>
            </div>

            <div className="bg-piops-900 border border-piops-800 p-4 rounded-xl">
              <div className="text-xs text-slate-400 font-medium">System Uptime</div>
              <div className="text-2xl font-bold text-white mt-1">
                {discoveryData?.uptime_seconds
                  ? `${Math.floor(discoveryData.uptime_seconds / 86400)}d ${Math.floor(
                      (discoveryData.uptime_seconds % 86400) / 3600
                    )}h`
                  : "--"}
              </div>
              <div className="text-[11px] text-slate-500 font-mono mt-1">
                Load: {discoveryData?.load_avg?.join(", ") || "--"}
              </div>
            </div>
          </div>

          {/* System Hardware Specifications */}
          <div className="bg-piops-900 border border-piops-800 p-6 rounded-xl space-y-4">
            <h3 className="font-bold text-white text-sm flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-cyan-400" />
              Remote Hardware & OS Profile
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3 bg-piops-950/60 rounded-lg border border-piops-800 space-y-1.5">
                <div className="text-slate-500">Operating System Distribution</div>
                <div className="text-white font-semibold">
                  {discoveryData?.os_name || server.system_info?.os_name || "Linux"}
                </div>
              </div>
              <div className="p-3 bg-piops-950/60 rounded-lg border border-piops-800 space-y-1.5">
                <div className="text-slate-500">Kernel Version & Architecture</div>
                <div className="text-white font-semibold">
                  {discoveryData?.kernel_version || server.system_info?.kernel_version || "--"}{" "}
                  ({discoveryData?.architecture || server.system_info?.architecture || "x86_64"})
                </div>
              </div>
              <div className="p-3 bg-piops-950/60 rounded-lg border border-piops-800 space-y-1.5">
                <div className="text-slate-500">Processor Model</div>
                <div className="text-white font-semibold">
                  {discoveryData?.cpu_model || server.system_info?.cpu_model || "Generic"}
                </div>
              </div>
              <div className="p-3 bg-piops-950/60 rounded-lg border border-piops-800 space-y-1.5">
                <div className="text-slate-500">Network Interfaces</div>
                <div className="text-white font-semibold">
                  {discoveryData?.interfaces?.map((i: any) => i.interface).join(", ") || "eth0"}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Processes */}
      {activeTab === "processes" && (
        <div className="bg-piops-900 border border-piops-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-piops-800 flex justify-between items-center text-xs">
            <span className="font-semibold text-white">Running Remote Processes (Top CPU/Memory)</span>
            <button
              onClick={runDiscovery}
              className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh List
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-piops-950 text-slate-400 font-mono uppercase text-[10px]">
                <tr>
                  <th className="px-4 py-3">PID</th>
                  <th className="px-4 py-3">Command</th>
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">CPU %</th>
                  <th className="px-4 py-3">RAM %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-piops-800 text-slate-300 font-mono">
                {discoveryData?.processes?.length > 0 ? (
                  discoveryData.processes.map((p: any) => (
                    <tr key={p.pid} className="hover:bg-piops-850">
                      <td className="px-4 py-2.5 text-cyan-400">{p.pid}</td>
                      <td className="px-4 py-2.5 font-semibold text-white">{p.name}</td>
                      <td className="px-4 py-2.5 text-slate-400">{p.username}</td>
                      <td className="px-4 py-2.5">{p.cpu_percent}%</td>
                      <td className="px-4 py-2.5">{p.memory_percent}%</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-slate-500">
                      Click "Run Discovery" to fetch remote process table.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Systemd Services */}
      {activeTab === "services" && (
        <div className="bg-piops-900 border border-piops-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-piops-800 flex justify-between items-center text-xs">
            <span className="font-semibold text-white">Discovered Systemd Service Units</span>
            <button
              onClick={runDiscovery}
              className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh Units
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-piops-950 text-slate-400 font-mono uppercase text-[10px]">
                <tr>
                  <th className="px-4 py-3">Unit Name</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Sub-State</th>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-piops-800 text-slate-300">
                {discoveryData?.services?.length > 0 ? (
                  discoveryData.services.map((s: any) => (
                    <tr key={s.name} className="hover:bg-piops-850">
                      <td className="px-4 py-2.5 font-mono text-cyan-400">{s.name}</td>
                      <td className="px-4 py-2.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
                            s.is_active
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                              : "bg-slate-500/10 text-slate-400 border border-slate-500/30"
                          }`}
                        >
                          {s.active_state}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 font-mono text-slate-400">{s.sub_state}</td>
                      <td className="px-4 py-2.5 text-slate-400 max-w-xs truncate">{s.description}</td>
                      <td className="px-4 py-2.5 text-right space-x-2">
                        <button
                          onClick={() =>
                            openActionPreview("restart_service", s.name.replace(".service", ""))
                          }
                          className="px-2 py-1 bg-piops-800 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-400 rounded text-[11px] font-mono transition"
                        >
                          Restart
                        </button>
                        <button
                          onClick={() =>
                            openActionPreview("stop_service", s.name.replace(".service", ""))
                          }
                          className="px-2 py-1 bg-piops-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 rounded text-[11px] font-mono transition"
                        >
                          Stop
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-slate-500">
                      Click "Run Discovery" to inspect remote systemd units.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Listening Ports */}
      {activeTab === "ports" && (
        <div className="bg-piops-900 border border-piops-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-piops-800 flex justify-between items-center text-xs">
            <span className="font-semibold text-white">Listening TCP/UDP Sockets</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-piops-950 text-slate-400 font-mono uppercase text-[10px]">
                <tr>
                  <th className="px-4 py-3">Protocol</th>
                  <th className="px-4 py-3">Bind IP</th>
                  <th className="px-4 py-3">Port</th>
                  <th className="px-4 py-3">Exposure</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-piops-800 text-slate-300 font-mono">
                {discoveryData?.ports?.length > 0 ? (
                  discoveryData.ports.map((p: any, idx: number) => {
                    const isPublic = ["0.0.0.0", "::", "*"].includes(p.ip);
                    return (
                      <tr key={idx} className="hover:bg-piops-850">
                        <td className="px-4 py-2.5 text-cyan-400 uppercase">{p.proto}</td>
                        <td className="px-4 py-2.5">{p.ip}</td>
                        <td className="px-4 py-2.5 text-white font-bold">{p.port}</td>
                        <td className="px-4 py-2.5">
                          {isPublic ? (
                            <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[10px]">
                              PUBLIC (0.0.0.0)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded bg-slate-500/10 text-slate-400 border border-slate-500/30 text-[10px]">
                              Localhost
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={4} className="p-6 text-center text-slate-500">
                      No listening sockets collected.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 5: Containers */}
      {activeTab === "containers" && (
        <div className="bg-piops-900 border border-piops-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-piops-800 flex justify-between items-center text-xs">
            <span className="font-semibold text-white">Docker Containers</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-piops-950 text-slate-400 font-mono uppercase text-[10px]">
                <tr>
                  <th className="px-4 py-3">Container ID</th>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Image</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-piops-800 text-slate-300 font-mono">
                {discoveryData?.containers?.length > 0 ? (
                  discoveryData.containers.map((c: any) => (
                    <tr key={c.container_id} className="hover:bg-piops-850">
                      <td className="px-4 py-2.5 text-cyan-400">{c.container_id.slice(0, 12)}</td>
                      <td className="px-4 py-2.5 text-white font-semibold">{c.name}</td>
                      <td className="px-4 py-2.5 text-slate-400">{c.image}</td>
                      <td className="px-4 py-2.5">{c.status}</td>
                      <td className="px-4 py-2.5 text-right space-x-2">
                        <button
                          onClick={() => openActionPreview("restart_container", c.name)}
                          className="px-2 py-1 bg-piops-800 hover:bg-cyan-500/20 text-cyan-400 rounded text-[11px]"
                        >
                          Restart
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-slate-500">
                      No active Docker containers discovered on remote server.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 6: Security Findings */}
      {activeTab === "security" && (
        <div className="space-y-4">
          {discoveryData?.security_findings?.length > 0 ? (
            discoveryData.security_findings.map((f: any) => (
              <div
                key={f.finding_id}
                className="bg-piops-900 border border-piops-800 p-5 rounded-xl space-y-2 shadow-lg"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        f.severity === "high" || f.severity === "critical"
                          ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                      }`}
                    >
                      {f.severity}
                    </span>
                    <h3 className="font-bold text-white text-sm">{f.title}</h3>
                  </div>
                  <span className="text-[11px] font-mono text-slate-500">{f.category}</span>
                </div>
                <p className="text-xs text-slate-400">{f.description}</p>
                {f.evidence && (
                  <div className="p-2.5 bg-piops-950 rounded border border-piops-800 text-[11px] font-mono text-slate-300">
                    <span className="text-slate-500">Evidence: </span>
                    {f.evidence}
                  </div>
                )}
                {f.recommended_fix && (
                  <div className="text-xs text-cyan-400 font-mono">
                    <span className="text-slate-400 font-sans">Fix: </span>
                    {f.recommended_fix}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="p-12 text-center bg-piops-900 border border-piops-800 rounded-xl text-slate-400 text-xs">
              <ShieldCheck className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
              No open defensive security vulnerabilities discovered on this server.
            </div>
          )}
        </div>
      )}

      {/* Tab 7: Safe Operations */}
      {activeTab === "actions" && (
        <div className="bg-piops-900 border border-piops-800 p-6 rounded-xl space-y-6">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Lock className="w-4 h-4 text-cyan-400" />
              Predefined Safe Remote Actions
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Actions are strictly validated against target whitelists and require operator confirmation.
              Arbitrary shell execution is completely prevented.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-piops-950 rounded-xl border border-piops-800 space-y-3">
              <div className="font-semibold text-white text-xs flex items-center gap-1.5">
                <RotateCw className="w-3.5 h-3.5 text-cyan-400" /> Restart Systemd Service
              </div>
              <p className="text-[11px] text-slate-400">
                Trigger graceful restart of an active service unit over SSH.
              </p>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. nginx, ssh, cron"
                  id="restart-target"
                  className="flex-1 bg-piops-900 border border-piops-800 rounded px-2.5 py-1.5 text-xs text-white font-mono"
                />
                <button
                  onClick={() => {
                    const el = document.getElementById("restart-target") as HTMLInputElement;
                    if (el?.value) openActionPreview("restart_service", el.value.trim());
                  }}
                  className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-semibold"
                >
                  Preview
                </button>
              </div>
            </div>

            <div className="p-4 bg-piops-950 rounded-xl border border-piops-800 space-y-3">
              <div className="font-semibold text-white text-xs flex items-center gap-1.5">
                <Box className="w-3.5 h-3.5 text-cyan-400" /> Prune Unused Docker Images
              </div>
              <p className="text-[11px] text-slate-400">
                Safely reclaim disk space by purging dangling container images.
              </p>
              <button
                onClick={() => openActionPreview("clean_docker_images", "system")}
                className="px-3 py-1.5 bg-piops-800 hover:bg-cyan-600 text-white rounded text-xs font-semibold"
              >
                Preview Prune Action
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Two-Phase Action Confirmation Modal */}
      {actionModal.open && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-piops-900 border border-piops-800 rounded-xl max-w-lg w-full p-6 shadow-2xl relative">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Confirm Remote Action Execution
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Verify the exact pre-compiled command before authorizing remote execution.
            </p>

            {actionModal.loading && (
              <div className="p-8 text-center text-xs text-slate-400 font-mono">
                Executing action over verified SSH session...
              </div>
            )}

            {actionModal.error && (
              <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs">
                {actionModal.error}
              </div>
            )}

            {actionModal.commandPreview && !actionModal.result && (
              <div className="mt-4 space-y-3 text-xs">
                <div>
                  <div className="text-slate-400 text-[11px] font-medium mb-1">Target Server</div>
                  <div className="font-mono text-white p-2 bg-piops-950 rounded border border-piops-800">
                    {server.name} ({server.hostname})
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 text-[11px] font-medium mb-1">Verified Command Preview</div>
                  <div className="font-mono text-cyan-400 p-2 bg-piops-950 rounded border border-piops-800 break-all">
                    {actionModal.commandPreview}
                  </div>
                </div>
                <div className="text-[11px] text-amber-400">
                  Approval token valid for 5 minutes. Token will be locked after execution.
                </div>
              </div>
            )}

            {actionModal.result && (
              <div className="mt-4 space-y-2 text-xs">
                <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                  <CheckCircle2 className="w-4 h-4" /> Execution Completed
                </div>
                <div className="p-3 bg-piops-950 rounded border border-piops-800 font-mono text-[11px] text-slate-300 max-h-48 overflow-y-auto">
                  {actionModal.result.output || "Command completed with exit status 0."}
                </div>
              </div>
            )}

            <div className="mt-6 flex justify-end gap-3 pt-3 border-t border-piops-800">
              <button
                onClick={() => setActionModal({ open: false, actionType: "", target: "", loading: false })}
                className="px-4 py-2 rounded-lg bg-piops-800 text-slate-300 hover:text-white text-xs"
              >
                Close
              </button>
              {actionModal.commandPreview && !actionModal.result && !actionModal.error && (
                <button
                  onClick={executeApprovedAction}
                  disabled={actionModal.loading}
                  className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs shadow-lg shadow-rose-600/30"
                >
                  Authorize & Run
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
