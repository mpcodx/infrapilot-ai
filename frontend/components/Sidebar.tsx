"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Server,
  Layers,
  Cpu,
  Box,
  ShieldAlert,
  Gauge,
  Bot,
  AlertTriangle,
  FileText,
  Radio,
  Network,
  Settings,
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Infrastructure", href: "/infrastructure", icon: Server },
  { name: "Remote Servers", href: "/servers", icon: Network },
  { name: "Services", href: "/services", icon: Layers },
  { name: "Processes", href: "/processes", icon: Cpu },
  { name: "Containers", href: "/containers", icon: Box },
  { name: "Security Center", href: "/security", icon: ShieldAlert },
  { name: "Performance", href: "/performance", icon: Gauge },
  { name: "AI Assistant", href: "/ai", icon: Bot },
  { name: "Incidents", href: "/incidents", icon: AlertTriangle },
  { name: "Reports", href: "/reports", icon: FileText },
  { name: "Registered Agents", href: "/agents", icon: Radio },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-piops-900 border-r border-piops-800 flex flex-col h-screen fixed left-0 top-0 z-30">
      {/* Brand & Logo */}
      <div className="h-16 flex items-center px-6 border-b border-piops-800 gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-black text-white text-base tracking-wider shadow-lg shadow-cyan-500/20">
          IP
        </div>
        <div>
          <div className="font-bold text-white tracking-wide text-base flex items-center gap-1.5">
            InfraPilot <span className="text-cyan-400">AI</span>
          </div>
          <div className="text-[10px] text-slate-400 tracking-wider uppercase font-medium">
            Command Center
          </div>
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-piops-850"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-cyan-400" : "text-slate-400"}`} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* System Status Footer */}
      <div className="p-4 border-t border-piops-800 text-xs">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span>Engine Status</span>
          <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            ACTIVE
          </span>
        </div>
        <div className="text-[11px] text-slate-500 font-mono">v1.0.0 • Ubuntu Linux</div>
      </div>
    </aside>
  );
}
