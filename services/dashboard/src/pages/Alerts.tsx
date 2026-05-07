import { ShieldAlert } from "lucide-react";

export default function Alerts() {
  return (
    <div className="space-y-6 flex flex-col h-full">
      <h2 className="text-3xl font-bold flex items-center gap-3">
        <ShieldAlert className="w-8 h-8 text-alert" />
        Live Alerts Feed
      </h2>
      <div className="flex-1 bg-dark-bg border border-gray-800 rounded-xl overflow-hidden font-mono text-sm relative">
        <div className="absolute top-0 w-full bg-dark-surface border-b border-gray-800 p-2 flex text-gray-400">
           <div className="w-32">TIME</div>
           <div className="w-48">TXN_ID</div>
           <div className="flex-1">DETAILS</div>
           <div className="w-24">SCORE</div>
        </div>
        <div className="mt-10 p-4 space-y-2 h-full overflow-y-auto">
          {/* Example alert row */}
          <div className="flex border-b border-gray-800/50 pb-2">
            <div className="w-32 text-gray-500">14:02:45</div>
            <div className="w-48 text-gray-300">TXN-948271</div>
            <div className="flex-1 text-gray-400">Velocity spike detected from Account-X</div>
            <div className="w-24 text-warn font-bold">0.82</div>
          </div>
          <div className="flex border-b border-gray-800/50 pb-2">
            <div className="w-32 text-gray-500">14:02:41</div>
            <div className="w-48 text-gray-300">TXN-948268</div>
            <div className="flex-1 text-gray-400">Structuring threshold crossed</div>
            <div className="w-24 text-alert font-bold">0.96</div>
          </div>
        </div>
      </div>
    </div>
  );
}