import { useState } from "react";
import { FileText } from "lucide-react";

export default function Reports() {
  const [strCaseId, setStrCaseId] = useState("");
  const [pdfCaseId, setPdfCaseId] = useState("");

  const handleGenerateSTR = () => {
    if (!strCaseId) return;
    window.open(`http://localhost:8005/api/str/${strCaseId}`, "_blank");
  };

  const handleDownloadPDF = () => {
    if (!pdfCaseId) return;
    window.open(`http://localhost:8003/report/${pdfCaseId}`, "_blank");
  };

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
            <input 
              type="text" 
              placeholder="Enter Case ID" 
              value={strCaseId}
              onChange={(e) => setStrCaseId(e.target.value)}
              className="w-full bg-dark-bg border border-gray-800 rounded p-3 text-gray-200 outline-none focus:border-safe" 
            />
            <button 
              onClick={handleGenerateSTR}
              className="bg-safe text-dark-bg font-bold px-4 py-3 rounded-lg w-full disabled:opacity-50"
              disabled={!strCaseId}
            >
              Generate XML
            </button>
         </div>
         <div className="bg-dark-surface border border-gray-800 p-6 rounded-xl space-y-4">
            <h3 className="text-xl font-bold">Explainability PDFs</h3>
            <p className="text-gray-400 text-sm">Download localized human-readable LLM reports for investigations.</p>
            <input 
              type="text" 
              placeholder="Enter Case ID" 
              value={pdfCaseId}
              onChange={(e) => setPdfCaseId(e.target.value)}
              className="w-full bg-dark-bg border border-gray-800 rounded p-3 text-gray-200 outline-none focus:border-safe" 
            />
            <button 
              onClick={handleDownloadPDF}
              className="bg-gray-800 text-gray-100 hover:bg-gray-700 font-bold px-4 py-3 rounded-lg w-full transition disabled:opacity-50"
              disabled={!pdfCaseId}
            >
              Download PDF
            </button>
         </div>
      </div>
    </div>
  );
}