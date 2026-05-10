import { useEffect, useState, useRef } from "react";
import { ShieldAlert } from "lucide-react";

type AlertRow = {
  time: string;
  transaction_id: string;
  details: string;
  score: number;
  decision: string;
};

export default function Alerts() {
  const [alerts, setAlerts] = useState<AlertRow[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new alerts arrive
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [alerts]);

  useEffect(() => {
    void (async () => {
      try {
        const resp = await fetch("http://localhost:8005/api/recent-alerts?limit=100");
        if (!resp.ok) {
          return;
        }
        const data = await resp.json();
        setAlerts(
          data
            .slice()
            .reverse()
            .map((row: { transaction_id?: string; unified_score?: number; decision?: string; created_at?: string }) => ({
              time: row.created_at ? new Date(row.created_at).toLocaleTimeString() : new Date().toLocaleTimeString(),
              transaction_id: row.transaction_id || `TXN-${Math.floor(Math.random() * 1000000)}`,
              details: "Historical anomaly from risk stream",
              score: row.unified_score || 0.0,
              decision: row.decision || "REVIEW",
            }))
        );
      } catch {
        // fallback to live websocket-only mode
      }
    })();

    const ws = new WebSocket("ws://localhost:8005/ws");
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.decision !== "APPROVE") {
        setAlerts((prev) => {
          const newAlert: AlertRow = {
            time: new Date().toLocaleTimeString(),
            transaction_id: data.transaction_id || `TXN-${Math.floor(Math.random() * 1000000)}`,
            details: data.reason || `Anomalous pattern identified by Risk Engine`,
            score: data.unified_score || 0.0,
            decision: data.decision
          };
          return [...prev, newAlert].slice(-100); // Keep last 100 alerts
        });
      }
    };
    
    return () => ws.close();
  }, []);

  return (
    <div className="space-y-6 flex flex-col h-full">
      <h2 className="text-3xl font-bold flex items-center gap-3">
        <ShieldAlert className="w-8 h-8 text-red-500" />
        Live Alerts Feed
      </h2>
      <div className="flex-1 bg-dark-bg border border-gray-800 rounded-xl overflow-hidden font-mono text-sm relative">
        <div className="absolute top-0 w-full bg-dark-surface border-b border-gray-800 p-2 flex text-gray-400 z-10">
           <div className="w-32 px-4">TIME</div>
           <div className="w-48">TXN_ID</div>
           <div className="flex-1">DETAILS</div>
           <div className="w-24">SCORE</div>
           <div className="w-32">SEVERITY</div>
        </div>
        <div ref={containerRef} className="mt-10 p-4 space-y-2 h-[calc(100vh-14rem)] overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="text-gray-500 italic p-4 text-center">Listening to Kafka WebSocket stream... Awaiting anomalies.</div>
          ) : (
            alerts.map((alert, idx) => (
              <div key={idx} className={`flex items-center p-2 rounded border-l-4 ${alert.decision === 'REJECT' ? 'border-red-500 bg-red-950/10' : 'border-yellow-500 bg-yellow-950/10'}`}>
                <div className="w-32 px-2 text-gray-500">{alert.time}</div>
                <div className="w-48 text-gray-300">{alert.transaction_id}</div>
                <div className="flex-1 text-gray-400 truncate pr-4">{alert.details}</div>
                <div className={`w-24 font-bold ${alert.score > 0.8 ? 'text-red-500' : 'text-yellow-500'}`}>
                  {alert.score.toFixed(2)}
                </div>
                <div className="w-32">
                  <span className={`px-2 py-1 rounded text-xs font-bold ${alert.decision === 'REJECT' ? 'bg-red-500/20 text-red-500' : 'bg-yellow-500/20 text-yellow-500'}`}>
                    {alert.decision}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
