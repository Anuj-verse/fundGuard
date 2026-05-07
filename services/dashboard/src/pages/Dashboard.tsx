export default function Dashboard() {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Live Overview</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard label="Active Alerts" value="12" alert />
        <MetricCard label="Fraud Rate" value="0.04%" />
        <MetricCard label="Trans/Min" value="3,450" />
        <MetricCard label="High Risk Nodes" value="8" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-96">
        <div className="bg-dark-surface border border-gray-800 rounded-xl p-6 flex items-center justify-center">
          [Chart Placeholder]
        </div>
        <div className="bg-dark-surface border border-gray-800 rounded-xl p-6 flex items-center justify-center">
          [Recent Alerts Placeholder]
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