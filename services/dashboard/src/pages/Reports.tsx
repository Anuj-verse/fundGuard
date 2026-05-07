import { FileText } from "lucide-react";

export default function Reports() {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold flex items-center gap-3">
        <FileText className="w-8 h-8 text-safe" />
        Reports & Export
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
         <div className="bg-dark-surface border border-gray-800 p-6 rounded-xl space-y-4">
            <h3 className="text-xl font-bold">Generate STR (XML)</h3>
            <p className="text-gray-400 text-sm">Select a finalized case to generate FIU-IND compliant XML output.</p>
            <input type="text" placeholder="Enter Case ID" className="w-full bg-dark-bg border border-gray-800 rounded p-3 text-gray-200 outline-none focus:border-safe" />
            <button className="bg-safe text-dark-bg font-bold px-4 py-3 rounded-lg w-full">Generate XML</button>
         </div>
         <div className="bg-dark-surface border border-gray-800 p-6 rounded-xl space-y-4">
            <h3 className="text-xl font-bold">Explainability PDFs</h3>
            <p className="text-gray-400 text-sm">Download localized human-readable LLM reports for investigations.</p>
            <input type="text" placeholder="Enter Case ID" className="w-full bg-dark-bg border border-gray-800 rounded p-3 text-gray-200 outline-none focus:border-safe" />
            <button className="bg-gray-800 text-gray-100 hover:bg-gray-700 font-bold px-4 py-3 rounded-lg w-full transition">Download PDF</button>
         </div>
      </div>
    </div>
  );
}