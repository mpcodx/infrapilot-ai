"use client";

import { useState } from "react";
import { Bot, Send, Terminal, Copy, Check, ShieldAlert, Sparkles, Loader2 } from "lucide-react";

const SUGGESTED_PROMPTS = [
  "Analyze current CPU and memory pressure on this host",
  "Explain detected security findings and advise remediations",
  "Which processes are consuming the most resources right now?",
  "Recommend safe diagnostic commands for network socket inspection",
];

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<any[]>([
    {
      role: "assistant",
      content:
        "Hello! I am your local InfraPilot AI Infrastructure & DevOps Assistant powered by Ollama (qwen3:4b). I analyze real-time host metrics, containers, and defensive security findings to provide evidence-based guidance. How can I help you operate your infrastructure today?",
      evidence: [],
      commands: ["top -b -n 1 | head -n 15", "df -h", "ss -tulnp"],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  const sendMessage = async (queryText?: string) => {
    const text = queryText || input;
    if (!text.trim() || loading) return;

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/v1/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, include_system_context: true }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          evidence: data.evidence || [],
          commands: data.suggested_commands || [],
          is_fallback: data.is_fallback,
        },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error communicating with the local AI engine.",
          evidence: [],
          commands: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (cmd: string) => {
    navigator.clipboard.writeText(cmd);
    setCopiedCmd(cmd);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-black text-white tracking-tight">AI DevOps Assistant</h1>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            Local Ollama Engine
          </span>
        </div>
        <p className="text-sm text-slate-400">
          Deterministic context building, prompt injection protection & strictly safe diagnostics
        </p>
      </div>

      {/* Suggested Prompts */}
      <div className="flex flex-wrap gap-2">
        {SUGGESTED_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => sendMessage(prompt)}
            className="text-xs bg-piops-900 hover:bg-piops-850 border border-piops-800 text-slate-300 px-3 py-1.5 rounded-xl transition flex items-center gap-1.5"
          >
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span>{prompt}</span>
          </button>
        ))}
      </div>

      {/* Chat Messages */}
      <div className="flex-1 bg-piops-900 border border-piops-800 rounded-2xl p-6 overflow-y-auto space-y-4 shadow-sm">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed ${
                m.role === "user"
                  ? "bg-cyan-500 text-black font-medium"
                  : "bg-piops-850 border border-piops-800 text-slate-200"
              }`}
            >
              <div className="whitespace-pre-wrap">{m.content}</div>

              {/* Evidence chips */}
              {m.evidence && m.evidence.length > 0 && (
                <div className="mt-3 pt-3 border-t border-piops-800/80">
                  <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">
                    Verified Host Evidence:
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {m.evidence.map((ev: string, i: number) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded bg-piops-950 border border-piops-800 text-[10px] font-mono text-cyan-400"
                      >
                        {ev}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Copyable commands */}
              {m.commands && m.commands.length > 0 && (
                <div className="mt-3 pt-3 border-t border-piops-800/80">
                  <div className="text-[10px] uppercase font-bold text-slate-400 mb-1.5 flex items-center justify-between">
                    <span>Suggested Read-Only Diagnostic Commands:</span>
                    <span className="text-slate-500 text-[9px]">(Manual Execution Only)</span>
                  </div>
                  <div className="space-y-1.5">
                    {m.commands.map((cmd: string, i: number) => (
                      <div
                        key={i}
                        className="bg-piops-950 px-3 py-1.5 rounded-lg border border-piops-800 flex items-center justify-between font-mono text-[11px] text-emerald-400"
                      >
                        <span>$ {cmd}</span>
                        <button
                          onClick={() => copyToClipboard(cmd)}
                          className="text-slate-400 hover:text-white transition p-1"
                          title="Copy command"
                        >
                          {copiedCmd === cmd ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-slate-400 bg-piops-850 p-3 rounded-xl border border-piops-800 max-w-xs">
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
            <span>Consulting local Ollama model...</span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Ask infrastructure diagnostics questions (e.g. 'Explain container status')..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          className="flex-1 px-4 py-3 bg-piops-900 border border-piops-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
        />
        <button
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
          className="px-5 py-3 bg-cyan-500 hover:bg-cyan-600 text-black font-bold rounded-xl text-sm transition flex items-center gap-2 disabled:opacity-50"
        >
          <Send className="w-4 h-4" />
          <span>Send</span>
        </button>
      </div>
    </div>
  );
}
