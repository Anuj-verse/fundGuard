import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Activity, AlertTriangle, ShieldAlert, Zap, Layers } from "lucide-react";
import { API_BASE_URL, WS_URL } from "../config/endpoints";
import { useDashboardAnchor, useThemeMode } from "../layout/MainLayout";

type RiskEvent = {
  transaction_id?: string;
  unified_score?: number;
  decision?: "APPROVE" | "REVIEW" | "REJECT" | string;
  components?: {
    edge_score?: number;
    graph_score?: number;
    rule_score?: number;
  };
};

export default function Dashboard() {
  const { registerDashboardAnchor } = useDashboardAnchor();
  const { isDarkMode } = useThemeMode();
  const [alerts, setAlerts] = useState<RiskEvent[]>([]);
  const [latestEvent, setLatestEvent] = useState<RiskEvent | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const streamStartedAt = useRef(Date.now());
  const [stats, setStats] = useState({
    fraudRate: "0.00%",
    activeAlerts: 0,
    transMin: "0.0",
    highRisk: 0,
    liveEvents: 0,
    rejectedEvents: 0,
  });

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/stats`)
      .then((r) => r.json())
      .then((data) => setStats((prev) => ({ ...prev, ...data })))
      .catch(console.error);

    fetch(`${API_BASE_URL}/api/recent-alerts?limit=10`)
      .then((r) => r.json())
      .then((data) => setAlerts(data))
      .catch(console.error);
  }, []);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      streamStartedAt.current = Date.now();
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as RiskEvent;
      setLatestEvent(data);
      setStats((prev) => {
        const liveEvents = prev.liveEvents + 1;
        const rejectedEvents = prev.rejectedEvents + (data.decision === "REJECT" ? 1 : 0);
        const elapsedMinutes = Math.max((Date.now() - streamStartedAt.current) / 60000, 1 / 60);

        return {
          ...prev,
          liveEvents,
          rejectedEvents,
          transMin: (liveEvents / elapsedMinutes).toFixed(1),
          fraudRate: `${((rejectedEvents / liveEvents) * 100).toFixed(2)}%`,
          activeAlerts: prev.activeAlerts + (data.decision !== "APPROVE" ? 1 : 0),
          highRisk: prev.highRisk + (data.decision === "REJECT" ? 1 : 0),
        };
      });

      if (data.decision !== "APPROVE") {
        setAlerts((prev) => [data, ...prev].slice(0, 10));
      }
    };

    ws.onerror = () => setWsConnected(false);
    ws.onclose = () => setWsConnected(false);

    return () => {
      setWsConnected(false);
      ws.close();
    };
  }, []);

  const surface = isDarkMode
    ? "bg-[#1E293B] border-slate-700 text-slate-100"
    : "bg-[#F8FAFC] border-slate-200 text-slate-950";
  const panelSurface = isDarkMode
    ? "bg-[#112131] border-slate-700 text-slate-100"
    : "bg-white border-slate-200 text-slate-950";

  return (
    <div ref={registerDashboardAnchor} className="space-y-6 font-sans">
      <div className="space-y-2">
        <p className="text-sm uppercase tracking-widest font-bold text-emerald-300">LIVE OVERVIEW</p>
        <h1 className="text-5xl font-black tracking-tight leading-none text-slate-100">Operational Risk Insights</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
        <MetricCard
          icon={<Activity size={25} className="text-emerald-300" />}
          label="LIVE INGESTED EVENTS"
          value={stats.liveEvents.toString()}
          isDarkMode={isDarkMode}
          themeSurface={surface}
        />
        <MetricCard
          icon={<AlertTriangle size={25} className="text-red-400" />}
          label="ACTIVE RISK ALERTS"
          value={stats.activeAlerts.toString()}
          highlight={stats.activeAlerts > 0}
          isDarkMode={isDarkMode}
          themeSurface={surface}
        />
        <MetricCard
          icon={<ShieldAlert size={25} className="text-sky-300" />}
          label="CORE REJECT RATE"
          value={stats.fraudRate}
          isDarkMode={isDarkMode}
          themeSurface={surface}
        />
        <MetricCard
          icon={<Zap size={25} className="text-cyan-300" />}
          label="TRANS / MIN (RPM)"
          value={stats.transMin}
          isDarkMode={isDarkMode}
          themeSurface={surface}
        />
        <MetricCard
          icon={<Layers size={25} className="text-violet-300" />}
          label="HIGH RISK NODES"
          value={stats.highRisk.toString()}
          isDarkMode={isDarkMode}
          themeSurface={surface}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <motion.section
          whileHover={{ y: -2 }}
          transition={{ duration: 0.2 }}
          className={`${panelSurface} rounded-[2rem] border p-6 ${isDarkMode ? "shadow-xl shadow-slate-950/20" : "shadow-lg shadow-gray-300/60"}`}
        >
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold tracking-tight">📡 Real-Time Fraud Telemetry Stream</h2>
          </div>
          <div className={`mt-6 min-h-[280px] rounded-3xl border ${isDarkMode ? "border-slate-700/60 bg-slate-950/25 text-slate-300" : "border-slate-200/80 bg-slate-50 text-slate-600"} p-6`}>
            <p className={isDarkMode ? "text-base leading-7 text-slate-400" : "text-base leading-7 text-slate-600"}>
              System standing by... Listening for active fraud risk vectors and transaction telemetry data lines.
            </p>
          </div>
        </motion.section>

        <motion.section
          whileHover={{ y: -2 }}
          transition={{ duration: 0.2 }}
          className={`${panelSurface} rounded-[2rem] border p-6 ${isDarkMode ? "shadow-xl shadow-slate-950/20" : "shadow-lg shadow-gray-300/60"}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold tracking-tight">🧠 Risk Engine Live AI Assessment</h2>
              <p className={`mt-2 text-sm font-medium tracking-wide ${isDarkMode ? "text-slate-400" : "text-slate-500"}`}>
                Kafka ➔ Dashboard API ➔ WebSocket Stream
              </p>
            </div>
          </div>
          <div className={`mt-8 rounded-3xl border ${isDarkMode ? "border-slate-700/60 bg-slate-950/25 text-slate-200" : "border-slate-200/80 bg-slate-50 text-slate-700"} p-6`}>
            <div className="flex flex-col gap-3 text-base leading-7">
              <p className={isDarkMode ? "text-slate-300" : "text-slate-600"}>
                The assessment engine monitors ingest throughput, anomaly spikes, and risk correlation across the operational pipeline.
              </p>
              <p className={isDarkMode ? "text-slate-300" : "text-slate-600"}>
                When active connections reopen, the stream badge will reflect live status and connection latency in real time.
              </p>
            </div>
          </div>
          <div className="mt-8 flex items-center justify-between rounded-3xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-700">
            <span className="inline-flex items-center gap-2 font-semibold">
              <span className="h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse shadow-red-500/50"></span>
              🔴 Operational Stream:
            </span>
            <span className="font-medium">DISCONNECTED</span>
          </div>
        </motion.section>
      </div>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
  highlight,
  isDarkMode,
  themeSurface,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  highlight?: boolean;
  isDarkMode: boolean;
  themeSurface: string;
}) {
  const liveBadge = highlight
    ? "inline-flex items-center gap-2 rounded-full bg-red-500/10 text-red-400 px-2.5 py-1 text-[10px] font-extrabold"
    : "inline-flex items-center gap-2 rounded-full bg-emerald-500/10 text-emerald-400 px-2.5 py-1 text-[10px] font-extrabold";

  return (
    <motion.div
      whileHover={{ translateY: -4 }}
      transition={{ duration: 0.18 }}
      className={`${themeSurface} rounded-2xl border border-white/5 p-5 ${isDarkMode ? "shadow-lg shadow-slate-950/20" : "shadow-md shadow-gray-300/40"} hover:border-emerald-500/20 hover:bg-[#243041]`}
    >
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <div className="text-slate-400 text-xs uppercase font-bold flex items-center gap-2">
            {icon}
            <span className="leading-none">{label}</span>
          </div>
        </div>
        {/* <span className={liveBadge}>
          {highlight && <span className="w-3 h-2 rounded-full bg-red-500 animate-pulse" />}
          <span>{highlight ? "LIVE" : "Live"}</span>
        </span> */}
      </div>
<div className="flex items-center justify-between">
      <div className={`text-5xl font-black tracking-tight leading-none ${highlight ? "text-red-400" : "text-[#10B981]"}`}>
        {value}
      </div>
      <span className="justify-end self-end">

       <span className={liveBadge}>
          {highlight && <span className="w-3 h-2 rounded-full bg-red-500 animate-pulse" />}
          <span>{highlight ? "LIVE" : "Live"}</span>
        </span>
      </span>
      </div>
    </motion.div>
  );
}
