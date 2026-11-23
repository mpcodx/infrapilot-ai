"use client";

import { useEffect, useState } from "react";
import { FileText, Download, Loader2, Sparkles, CheckCircle } from "lucide-react";

export default function ReportsPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [generating, setGenerating] = useState(false);
  const [format, setFormat] = useState<"pdf" | "json">("pdf");

  const fetchReports = async () => {
    try {
      const res = await fetch("/api/v1/reports");
      if (res.ok) setReports(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const generateReport = async () => {
    setGenerating(true);
    try {
      const res = await fetch("/api/v1/reports/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format }),
      });
      if (res.ok) {
        await fetchReports();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Diagnostics Reports</h1>
          <p className="text-sm text-slate-400">
            Export comprehensive PDF and JSON infrastructure snapshots with real telemetry
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={format}
            onChange={(e: any) => setFormat(e.target.value)}
            className="bg-piops-900 border border-piops-800 text-xs text-white px-3 py-2 rounded-xl focus:outline-none focus:border-cyan-500"
          >
            <option value="pdf">PDF Format</option>
            <option value="json">JSON Format</option>
          </select>
          <button
            onClick={generateReport}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-black font-bold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition disabled:opacity-50"
          >
            {generating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span>Generate Report</span>
          </button>
        </div>
      </div>

      <div className="bg-piops-900 border border-piops-800 rounded-2xl overflow-hidden shadow-sm">
        {reports.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-base font-bold text-white mb-1">No Reports Generated Yet</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Click &quot;Generate Report&quot; above to capture real-time host metrics, security findings, and
              capacity headroom into an exportable document.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-piops-850 text-slate-400 uppercase font-mono">
                <tr>
                  <th className="py-3 px-4">Filename</th>
                  <th className="py-3 px-4">Format</th>
                  <th className="py-3 px-4">Size</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-piops-800 font-mono">
                {reports.map((r, idx) => (
                  <tr key={idx} className="hover:bg-piops-850/50">
                    <td className="py-3 px-4 text-slate-200 font-semibold flex items-center gap-2">
                      <FileText className="w-4 h-4 text-cyan-400" />
                      <span>{r.filename}</span>
                    </td>
                    <td className="py-3 px-4 uppercase text-slate-400">{r.format}</td>
                    <td className="py-3 px-4 text-slate-400">{Math.round(r.size_bytes / 1024)} KB</td>
                    <td className="py-3 px-4 text-right">
                      <a
                        href={`/api/v1/reports/download/${r.filename}`}
                        download
                        className="inline-flex items-center gap-1.5 px-3 py-1 bg-piops-850 hover:bg-piops-800 text-cyan-400 border border-piops-800 rounded-lg text-xs font-semibold transition"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download</span>
                      </a>
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
