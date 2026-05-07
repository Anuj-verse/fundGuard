import { useEffect, useState } from "react";

export default function Dashboard() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [stats, setStats] = useState({ fraudRate: '0.00%', activeAlerts: 0, transMin: '0', highRisk: 0 });

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8005/ws");
    
    ws.onopen = () => console.log("Connected to Risk Engine WS");
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.decision !== "APPROVE") {
        setAlerts((prev) => [data, ...prev].slice(0, 10)); // Keep last 10
        setStats((prev) => ({
          ...prev, 
          activeAlerts: prev.activeAlerts + 1,
          highRisk: data.decision === "REJECT" ? prev.highRisk + 1 : prev.highRisk
        }));
      }
    };
    
    return () => ws.close();
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Live Overview</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard label="Active Alerts" value={stats.activeAlerts.toString()} alert={stats.activeAlerts > 0} />
        <MetricCard label="Fraud Rate" value={stats.fraudRate} />
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
        <div className="bg-dark-surface border border-gray-800 rounded-xl p-6 flex flex-col justify-center items-center">
          <h3 className="text-gray-400 mb-4">Risk Engine Real-time Analysis</h3>
          <p className="text-sm text-gray-500 text-center px-8">Fully unified event-driven pipeline. Edge scores, Graph patterns, and Rule spikes stream live to this dashboard through Kafka {'->'} WebSocket.</p>
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
