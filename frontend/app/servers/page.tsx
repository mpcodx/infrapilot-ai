"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Server,
  Plus,
  ShieldCheck,
  ShieldAlert,
  RefreshCw,
  Trash2,
  Key,
  Terminal,
  Activity,
  HardDrive,
  Cpu,
  Clock,
  ExternalLink,
  Lock,
  CheckCircle2,
  AlertCircle,
  X,
  Layers,
} from "lucide-react";

interface ManagedServer {
  server_id: string;
  name: string;
  connection_type: string;
  hostname: string;
  ssh_port: number;
  username: string;
  auth_method: string;
  has_credential: boolean;
  has_passphrase: boolean;
  timeout_seconds: number;
  environment: string;
  organization: string;
  tags: string[];
  host_key_fingerprint: string | null;
  host_key_type: string | null;
  is_host_key_trusted: boolean;
  status: string;
  last_connected_at: string | null;
  last_error: string | null;
  polling_interval: number;
  system_info?: {
    hostname?: string;
    os_name?: string;
    kernel_version?: string;
    cpu_model?: string;
    cpu_count?: number;
  };
}

export default function ServersPage() {
  const [servers, setServers] = useState<ManagedServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState("all");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    connection_type: "ssh",
    hostname: "",
    ssh_port: 22,
    username: "root",
    auth_method: "password",
    credential: "",
    passphrase: "",
    timeout_seconds: 10,
    environment: "production",
    organization: "default",
    tags: "",
    auto_trust_host_key: true,
  });

  const [testResult, setTestResult] = useState<{
    tested: boolean;
    success: boolean;
    message: string;
    fingerprint?: string;
    latency?: number;
  } | null>(null);
  const [testingConnection, setTestingConnection] = useState(false);

  const fetchServers = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://127.0.0.1:8000/api/v1/servers");
      if (res.ok) {
        const data = await res.json();
        setServers(data);
      }
    } catch (err) {
      console.error("Failed to fetch servers", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServers();
    const interval = setInterval(fetchServers, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setTestResult(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/servers/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hostname: formData.hostname,
          ssh_port: Number(formData.ssh_port),
          username: formData.username,
          auth_method: formData.auth_method,
          credential: formData.credential,
          passphrase: formData.passphrase || undefined,
          timeout_seconds: Number(formData.timeout_seconds),
        }),
      });
      const data = await res.json();
      setTestResult({
        tested: true,
        success: data.success,
        message: data.message,
        fingerprint: data.host_key_fingerprint,
        latency: data.latency_ms,
      });
    } catch (err: any) {
      setTestResult({
        tested: true,
        success: false,
        message: err.message || "Failed to reach backend test service",
      });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleCreateServer = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const tagsArray = formData.tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);

      const res = await fetch("http://127.0.0.1:8000/api/v1/servers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          ssh_port: Number(formData.ssh_port),
          timeout_seconds: Number(formData.timeout_seconds),
          tags: tagsArray,
        }),
      });

      if (res.ok) {
        setIsModalOpen(false);
        setFormData({
          name: "",
          connection_type: "ssh",
          hostname: "",
          ssh_port: 22,
          username: "root",
          auth_method: "password",
          credential: "",
          passphrase: "",
          timeout_seconds: 10,
          environment: "production",
          organization: "default",
          tags: "",
          auto_trust_host_key: true,
        });
        setTestResult(null);
        fetchServers();
      } else {
        const err = await res.json();
        alert(`Error: ${err.detail || "Failed to register server"}`);
      }
    } catch (err: any) {
      alert(`Registration error: ${err.message}`);
    }
  };

  const handleDeleteServer = async (serverId: string, name: string) => {
    if (!confirm(`Are you sure you want to remove '${name}' and revoke its credentials?`)) {
      return;
    }
    try {
      setActionLoading(serverId);
      await fetch(`http://127.0.0.1:8000/api/v1/servers/${serverId}`, {
        method: "DELETE",
      });
      fetchServers();
    } finally {
      setActionLoading(null);
    }
  };

  const handleTriggerDiscovery = async (serverId: string) => {
    try {
      setActionLoading(serverId);
      const res = await fetch(`http://127.0.0.1:8000/api/v1/servers/${serverId}/discover`, {
        method: "POST",
      });
      if (res.ok) {
        alert("Discovery completed successfully! Refreshing telemetry.");
        fetchServers();
      } else {
        const err = await res.json();
        alert(`Discovery error: ${err.detail}`);
      }
    } finally {
      setActionLoading(null);
    }
  };

  const filteredServers = servers.filter((s) => {
    if (activeFilter === "all") return true;
    if (activeFilter === "online") return s.status === "online";
    if (activeFilter === "offline") return s.status === "offline";
    return s.environment.toLowerCase() === activeFilter.toLowerCase();
  });

  return (
    <div className="space-y-6">
      {/* Top Banner & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-piops-900 border border-piops-800 p-6 rounded-xl shadow-lg">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Server className="w-7 h-7 text-cyan-400" />
            Remote Server Fleet
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Monitor and manage multiple remote Linux servers directly via agentless SSH or Companion Agents.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchServers}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-piops-800 text-slate-300 hover:text-white border border-piops-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-600/30 transition"
          >
            <Plus className="w-4 h-4" />
            Add Server
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-piops-800 pb-3 text-xs">
        {["all", "production", "staging", "development", "online", "offline"].map((f) => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className={`px-3 py-1.5 rounded-lg capitalize font-medium transition ${
              activeFilter === f
                ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                : "text-slate-400 hover:text-slate-200 hover:bg-piops-850"
            }`}
          >
            {f}
          </button>
        ))}
        <span className="ml-auto text-slate-500 font-mono text-[11px]">
          {filteredServers.length} of {servers.length} Servers
        </span>
      </div>

      {/* Server Grid */}
      {loading && servers.length === 0 ? (
        <div className="p-12 text-center text-slate-400 font-mono text-sm bg-piops-900 border border-piops-800 rounded-xl">
          Scanning server registry...
        </div>
      ) : filteredServers.length === 0 ? (
        <div className="p-12 text-center bg-piops-900 border border-piops-800 rounded-xl">
          <Server className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-300">No servers found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Connect your first remote Linux server or Raspberry Pi using SSH direct connection or the companion agent.
          </p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="mt-4 px-4 py-2 text-xs font-semibold rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white inline-flex items-center gap-2"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Server Now
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredServers.map((server) => {
            const isOnline = server.status === "online";
            const isUntrusted = server.status === "untrusted_host_key";
            return (
              <div
                key={server.server_id}
                className="bg-piops-900 border border-piops-800 hover:border-piops-700 rounded-xl p-5 shadow-lg flex flex-col justify-between transition group"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-white text-base group-hover:text-cyan-400 transition">
                          {server.name}
                        </h3>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                            server.environment === "production"
                              ? "bg-purple-500/10 text-purple-400 border border-purple-500/30"
                              : server.environment === "staging"
                              ? "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                              : "bg-slate-500/10 text-slate-400 border border-slate-500/30"
                          }`}
                        >
                          {server.environment}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 font-mono mt-0.5 flex items-center gap-1.5">
                        <Terminal className="w-3 h-3 text-slate-500" />
                        {server.username}@{server.hostname}:{server.ssh_port}
                      </div>
                    </div>

                    {/* Status Pill */}
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold tracking-wider uppercase border ${
                        isOnline
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                          : isUntrusted
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                          : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          isOnline ? "bg-emerald-400 animate-pulse" : isUntrusted ? "bg-amber-400" : "bg-rose-400"
                        }`}
                      ></span>
                      {server.status.replace("_", " ")}
                    </span>
                  </div>

                  {/* Host Key Details */}
                  <div className="mt-4 p-2.5 bg-piops-950/60 rounded-lg border border-piops-800/80 text-[11px] space-y-1">
                    <div className="flex items-center justify-between text-slate-400">
                      <span className="flex items-center gap-1">
                        <Lock className="w-3 h-3 text-cyan-400" />
                        Auth: {server.auth_method}
                      </span>
                      <span className="text-slate-500 font-mono">
                        {server.connection_type === "ssh" ? "SSH Direct" : "Agent"}
                      </span>
                    </div>
                    {server.host_key_fingerprint && (
                      <div className="text-slate-500 font-mono truncate" title={server.host_key_fingerprint}>
                        Key: {server.host_key_fingerprint}
                      </div>
                    )}
                  </div>

                  {/* System Info snippet if discovered */}
                  {server.system_info && (
                    <div className="mt-3 text-xs text-slate-400 space-y-1">
                      <div className="truncate">
                        <span className="text-slate-500">OS:</span> {server.system_info.os_name || "Linux"}
                      </div>
                      <div className="truncate">
                        <span className="text-slate-500">CPU:</span> {server.system_info.cpu_model || "Generic"} (
                        {server.system_info.cpu_count || 1} Cores)
                      </div>
                    </div>
                  )}

                  {/* Tags */}
                  {server.tags && server.tags.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {server.tags.map((t) => (
                        <span
                          key={t}
                          className="px-2 py-0.5 bg-piops-800 text-slate-400 rounded text-[10px] font-mono"
                        >
                          #{t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Card Footer Actions */}
                <div className="mt-5 pt-3 border-t border-piops-800/80 flex items-center justify-between text-xs">
                  <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {server.last_connected_at
                      ? new Date(server.last_connected_at).toLocaleTimeString()
                      : "Never"}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleTriggerDiscovery(server.server_id)}
                      disabled={actionLoading === server.server_id}
                      className="p-1.5 rounded hover:bg-piops-800 text-slate-400 hover:text-cyan-400 transition"
                      title="Run SSH Discovery & Refresh"
                    >
                      <RefreshCw
                        className={`w-3.5 h-3.5 ${actionLoading === server.server_id ? "animate-spin" : ""}`}
                      />
                    </button>
                    <Link
                      href={`/servers/${server.server_id}`}
                      className="px-2.5 py-1 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded text-[11px] font-semibold flex items-center gap-1 transition"
                    >
                      Details
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                    <button
                      onClick={() => handleDeleteServer(server.server_id, server.name)}
                      disabled={actionLoading === server.server_id}
                      className="p-1.5 rounded hover:bg-rose-500/10 text-slate-500 hover:text-rose-400 transition"
                      title="Remove Server"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Server Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-piops-900 border border-piops-800 rounded-xl max-w-xl w-full p-6 shadow-2xl relative my-8">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2.5 mb-5">
              <div className="p-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400">
                <Plus className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Add Remote Linux Server</h2>
                <p className="text-xs text-slate-400">
                  Connect via SSH Direct (Agentless) or Companion Agent.
                </p>
              </div>
            </div>

            <form onSubmit={handleCreateServer} className="space-y-4 text-xs">
              {/* Connection Type Toggle */}
              <div>
                <label className="block text-slate-300 font-semibold mb-1.5">Connection Method</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, connection_type: "ssh" })}
                    className={`p-2.5 rounded-lg border text-left flex items-center gap-2.5 transition ${
                      formData.connection_type === "ssh"
                        ? "bg-cyan-500/10 border-cyan-500/40 text-cyan-400"
                        : "bg-piops-850 border-piops-800 text-slate-400"
                    }`}
                  >
                    <Terminal className="w-4 h-4" />
                    <div>
                      <div className="font-semibold text-white text-xs">SSH Direct (Agentless)</div>
                      <div className="text-[10px] text-slate-400">Port 22 authenticated SSH</div>
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, connection_type: "agent" })}
                    className={`p-2.5 rounded-lg border text-left flex items-center gap-2.5 transition ${
                      formData.connection_type === "agent"
                        ? "bg-cyan-500/10 border-cyan-500/40 text-cyan-400"
                        : "bg-piops-850 border-piops-800 text-slate-400"
                    }`}
                  >
                    <Layers className="w-4 h-4" />
                    <div>
                      <div className="font-semibold text-white text-xs">InfraPilot Agent</div>
                      <div className="text-[10px] text-slate-400">Lightweight node daemon</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Server Name & Hostname */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Server Display Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. EU-Prod-Database"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-piops-950 border border-piops-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Hostname or IP Address</label>
                  <input
                    type="text"
                    required
                    placeholder="192.168.1.100 or server.internal"
                    value={formData.hostname}
                    onChange={(e) => setFormData({ ...formData, hostname: e.target.value })}
                    className="w-full bg-piops-950 border border-piops-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              {/* SSH Port & Username */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">SSH Port</label>
                  <input
                    type="number"
                    required
                    value={formData.ssh_port}
                    onChange={(e) => setFormData({ ...formData, ssh_port: Number(e.target.value) })}
                    className="w-full bg-piops-950 border border-piops-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">SSH Username</label>
                  <input
                    type="text"
                    required
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full bg-piops-950 border border-piops-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              {/* Auth Method & Credentials */}
              <div>
                <label className="block text-slate-300 font-medium mb-1">Authentication Method</label>
                <div className="flex gap-4 mb-2">
                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="radio"
                      name="auth_method"
                      value="password"
                      checked={formData.auth_method === "password"}
                      onChange={() => setFormData({ ...formData, auth_method: "password" })}
                      className="text-cyan-500"
                    />
                    SSH Password
                  </label>
                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="radio"
                      name="auth_method"
                      value="private_key"
                      checked={formData.auth_method === "private_key"}
                      onChange={() => setFormData({ ...formData, auth_method: "private_key" })}
                      className="text-cyan-500"
                    />
                    SSH Private Key (OpenSSH / RSA / Ed25519)
                  </label>
                </div>

                {formData.auth_method === "password" ? (
                  <div>
                    <input
                      type="password"
                      required
                      placeholder="Enter remote user password (encrypted with Fernet)"
                      value={formData.credential}
                      onChange={(e) => setFormData({ ...formData, credential: e.target.value })}
                      className="w-full bg-piops-950 border border-piops-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500 font-mono"
                    />
                  </div>
                ) : (
                  <div className="space-y-2">
                    <textarea
                      rows={4}
                      required
                      placeholder="-----BEGIN OPENSSH PRIVATE KEY-----&#10;..."
                      value={formData.credential}
                      onChange={(e) => setFormData({ ...formData, credential: e.target.value })}
                      className="w-full bg-piops-950 border border-piops-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500 font-mono text-[11px]"
                    />
                    <input
                      type="password"
                      placeholder="Optional Private Key Passphrase"
                      value={formData.passphrase}
                      onChange={(e) => setFormData({ ...formData, passphrase: e.target.value })}
                      className="w-full bg-piops-950 border border-piops-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                )}
              </div>

              {/* Environment & Tags */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Environment</label>
                  <select
                    value={formData.environment}
                    onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                    className="w-full bg-piops-950 border border-piops-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="production">Production</option>
                    <option value="staging">Staging</option>
                    <option value="development">Development</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Tags (Comma-separated)</label>
                  <input
                    type="text"
                    placeholder="database, aws, node"
                    value={formData.tags}
                    onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                    className="w-full bg-piops-950 border border-piops-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              {/* Host Key Trust Checkbox */}
              <div className="p-3 bg-piops-950/80 rounded-lg border border-piops-800 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={formData.auto_trust_host_key}
                    onChange={(e) => setFormData({ ...formData, auto_trust_host_key: e.target.checked })}
                    className="rounded text-cyan-500"
                  />
                  <span>Verify and trust host key fingerprint automatically upon first connection</span>
                </label>
                <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                  Mismatched or changed host keys will always be strictly blocked to prevent MITM attacks.
                </div>
              </div>

              {/* Test Connection Button & Result */}
              <div className="pt-2">
                <div className="flex items-center justify-between">
                  <button
                    type="button"
                    onClick={handleTestConnection}
                    disabled={testingConnection || !formData.hostname || !formData.credential}
                    className="px-3 py-1.5 bg-piops-800 hover:bg-piops-700 disabled:opacity-50 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
                  >
                    <Activity className={`w-3.5 h-3.5 ${testingConnection ? "animate-spin" : ""}`} />
                    {testingConnection ? "Probing Host..." : "Test SSH Connection"}
                  </button>

                  {testResult && (
                    <div className="flex items-center gap-1.5 text-xs font-medium">
                      {testResult.success ? (
                        <span className="text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-4 h-4" /> Connected ({testResult.latency}ms)
                        </span>
                      ) : (
                        <span className="text-rose-400 flex items-center gap-1">
                          <AlertCircle className="w-4 h-4" /> {testResult.message}
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {testResult?.fingerprint && (
                  <div className="mt-2 p-2 bg-piops-950 rounded border border-piops-800 text-[11px] font-mono text-slate-400 break-all">
                    Observed Host Key: {testResult.fingerprint}
                  </div>
                )}
              </div>

              {/* Submit Buttons */}
              <div className="pt-3 border-t border-piops-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-piops-800 text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold shadow-lg shadow-cyan-600/30"
                >
                  Save & Connect Server
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
