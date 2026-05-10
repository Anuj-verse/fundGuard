import { useEffect, useRef, useState } from "react";

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
    // Load historical data on mount
    fetch("http://localhost:8005/api/stats")
      .then(r => r.json())
      .then(data => {
        setStats(prev => ({...prev, ...data}));
      })
      .catch(console.error);

    fetch("http://localhost:8005/api/recent-alerts?limit=10")
      .then(r => r.json())
      .then(data => {
        setAlerts(data);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8005/ws");

    ws.onopen = () => {
      streamStartedAt.current = Date.now();
      setWsConnected(true);
      console.log("Connected to Risk Engine WS");
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

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Live Overview</h2>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <MetricCard label="Live Events" value={stats.liveEvents.toString()} alert={stats.liveEvents > 0} />
        <MetricCard label="Active Alerts" value={stats.activeAlerts.toString()} alert={stats.activeAlerts > 0} />
        <MetricCard label="Reject Rate" value={stats.fraudRate} />
        <MetricCard label="Trans/Min" value={stats.transMin} />
        <MetricCard label="High Risk Nodes" value={stats.highRisk.toString()} alert={stats.highRisk > 0} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-96">
        <div className="bg-dark-surface border border-gray-800 rounded-xl p-6 flex flex-col overflow-hidden">
          <h3 className="text-xl font-semibold mb-4 text-gray-200">Recent Signals</h3>
          <div className="flex-1 overflow-y-auto space-y-3">
             {alerts.length === 0 ? <p className="text-gray-500 italic">Listening for live alerts...</p> : alerts.map((a, i) => (
               <div key={i} className={`p-3 rounded-lg border-l-4 ${a.decision === 'REJECT' ? 'border-red-500 bg-red-950/20' : 'border-yellow-500 bg-yellow-950/20'}`}>
                 <div className="flex justify-between items-center mb-1">
                   <strong className="text-sm font-mono text-gray-300">{a.transaction_id}</strong>
                   <span className="text-xs font-bold px-2 py-1 rounded bg-black/40">{a.decision}</span>
                 </div>
                 <div className="text-xs text-gray-400">Score: {a.unified_score?.toFixed(2)}</div>
               </div>
             ))}
          </div>
        </div>
        <div className="bg-dark-surface border border-gray-800 rounded-xl p-6 flex flex-col justify-center items-center gap-4">
          <h3 className="text-gray-400">Risk Engine Real-time Analysis</h3>
          <div className="text-sm px-4 py-2 rounded-full border border-gray-700 text-gray-300">
            Stream status: {wsConnected ? "CONNECTED" : "DISCONNECTED"}
          </div>
          {latestEvent ? (
            <div className="w-full max-w-md p-4 rounded-lg border border-gray-700 bg-black/20 text-sm space-y-2">
              <div className="text-gray-400">Latest Event</div>
              <div className="font-mono text-gray-200 break-all">{latestEvent.transaction_id}</div>
              <div className="text-gray-300">Decision: {latestEvent.decision}</div>
              <div className="text-gray-400">Unified score: {latestEvent.unified_score?.toFixed(2) ?? "0.00"}</div>
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center px-8">
              Waiting for live transactions. This panel updates for every event, including APPROVE decisions.
            </p>
          )}
          <p className="text-xs text-gray-600 text-center px-8">Kafka -&gt; Dashboard API -&gt; WebSocket stream</p>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, alert }: { label: string; value: string; alert?: boolean }) {
  return (
    <div className="bg-dark-surface border border-gray-800 p-6 rounded-xl">
      <div className="text-gray-400 text-sm font-medium uppercase tracking-wider">{label}</div>
      <div className={`text-4xl font-mono mt-2 font-bold ${alert ? 'text-alert' : 'text-gray-100'}`}>
        {value}
      </div>
    </div>
  );
}
