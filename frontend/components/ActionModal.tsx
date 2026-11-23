"use client";

import { useState } from "react";
import { AlertCircle, CheckCircle, Loader2, ShieldAlert, X } from "lucide-react";

interface ActionModalProps {
  actionType: string;
  target: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function ActionModal({
  actionType,
  target,
  isOpen,
  onClose,
}: ActionModalProps) {
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchPreview = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/v1/actions/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_type: actionType, target }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to generate action preview.");
      setPreview(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!preview?.action_id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/actions/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: preview.action_id, confirmed: true }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Execution failed.");
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-piops-900 border border-piops-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Safe DevOps Action Engine</h3>
            <p className="text-xs text-slate-400">
              Verified command preview with explicit operator approval
            </p>
          </div>
        </div>

        {!preview && !result && (
          <div className="py-4 space-y-4">
            <div className="bg-piops-850 p-4 rounded-xl border border-piops-800 text-sm">
              <div className="text-slate-400 text-xs mb-1">Target Resource:</div>
              <div className="font-mono text-cyan-300 font-semibold">{target}</div>
              <div className="text-slate-400 text-xs mt-3 mb-1">Operation:</div>
              <div className="font-mono text-slate-200 capitalize">{actionType.replace("_", " ")}</div>
            </div>
            <button
              onClick={fetchPreview}
              disabled={loading}
              className="w-full py-2.5 px-4 bg-cyan-500 hover:bg-cyan-600 text-black font-semibold rounded-xl text-sm transition flex items-center justify-center gap-2"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Generate Action Preview
            </button>
          </div>
        )}

        {preview && !result && (
          <div className="py-3 space-y-4">
            <div className="bg-piops-950 p-4 rounded-xl border border-piops-800 font-mono text-xs">
              <div className="text-slate-500 text-[10px] uppercase mb-1">Command Template:</div>
              <div className="text-emerald-400 font-bold">$ {preview.command_preview}</div>
            </div>

            <div className="flex items-center justify-between text-xs px-1">
              <span className="text-slate-400">Risk Assessment:</span>
              <span
                className={`px-2.5 py-0.5 rounded-full font-bold ${
                  preview.risk_level === "High"
                    ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                    : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                }`}
              >
                {preview.risk_level} Risk
              </span>
            </div>

            <div className="text-xs text-slate-400 bg-amber-500/10 border border-amber-500/20 p-3 rounded-lg flex gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <span>
                This operation directly modifies container/service runtime state on the host. Please
                confirm your authorization.
              </span>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={onClose}
                className="flex-1 py-2.5 bg-piops-850 hover:bg-piops-800 text-slate-300 rounded-xl text-sm font-medium border border-piops-800 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={loading}
                className="flex-1 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-sm font-semibold transition flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Approve & Execute
              </button>
            </div>
          </div>
        )}

        {result && (
          <div className="py-3 space-y-4">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
              <CheckCircle className="w-5 h-5" />
              <span>Operation Completed Successfully</span>
            </div>
            <div className="bg-piops-950 p-4 rounded-xl border border-piops-800 font-mono text-xs max-h-48 overflow-y-auto text-slate-300">
              <div className="text-slate-500 text-[10px] mb-1">Execution Output:</div>
              <pre className="whitespace-pre-wrap">{result.output || "Done with returncode 0"}</pre>
            </div>
            <button
              onClick={onClose}
              className="w-full py-2.5 bg-piops-850 hover:bg-piops-800 text-white font-medium rounded-xl text-sm transition"
            >
              Close
            </button>
          </div>
        )}

        {error && (
          <div className="mt-3 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  );
}
