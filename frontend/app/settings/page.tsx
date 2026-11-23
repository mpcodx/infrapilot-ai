"use client";

import { useState } from "react";
import { Settings, Save, CheckCircle, ShieldCheck } from "lucide-react";

export default function SettingsPage() {
  const [ollamaUrl, setOllamaUrl] = useState("http://127.0.0.1:11434");
  const [modelName, setModelName] = useState("qwen3:4b");
  const [interval, setInterval] = useState("5");
  const [retention, setRetention] = useState("72");
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight">System & AI Settings</h1>
        <p className="text-sm text-slate-400">
          Configure telemetry frequency, local Ollama endpoints and SoloHost parameters
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Ollama Configuration */}
        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <span>Ollama AI Runtime Configuration</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">
                Ollama Base URL
              </label>
              <input
                type="text"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-piops-850 border border-piops-800 rounded-xl text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">
                Model Name
              </label>
              <input
                type="text"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-piops-850 border border-piops-800 rounded-xl text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>
        </div>

        {/* Telemetry & Retention */}
        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-base font-bold text-white">Telemetry & Data Retention</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">
                Sampling Interval (Seconds)
              </label>
              <input
                type="number"
                value={interval}
                onChange={(e) => setInterval(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-piops-850 border border-piops-800 rounded-xl text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">
                Metric History Retention (Hours)
              </label>
              <input
                type="number"
                value={retention}
                onChange={(e) => setRetention(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-piops-850 border border-piops-800 rounded-xl text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>
        </div>

        {/* SoloHost & Pi Network Settings */}
        <div className="bg-piops-900 border border-piops-800 rounded-2xl p-6 space-y-3">
          <h2 className="text-base font-bold text-white">Pi Network & SoloHost Architecture</h2>
          <div className="text-xs text-slate-400 space-y-2 leading-relaxed">
            <p>
              Deployment Mode: <span className="text-cyan-400 font-mono font-bold">SoloHost Control Center</span>
            </p>
            <p>
              In accordance with the SoloHost publishing contract, host isolation is strictly preserved.
              Containers cannot access arbitrary host files or run privileged root exploits.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <button
            type="submit"
            className="px-6 py-2.5 bg-cyan-500 hover:bg-cyan-600 text-black font-bold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            <span>Save Configuration</span>
          </button>
          {saved && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold">
              <CheckCircle className="w-4 h-4" />
              <span>Preferences saved successfully</span>
            </div>
          )}
        </div>
      </form>
    </div>
  );
}
