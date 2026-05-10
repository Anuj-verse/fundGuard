import { useEffect, useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper
} from '@tanstack/react-table';
import { API_BASE_URL } from '../config/endpoints';

type CaseData = {
  id: string;
  transaction_id: string;
  sender_account_id: string;
  unified_score: number;
  status: string;
  created_at: string;
}

const columnHelper = createColumnHelper<CaseData>()

export default function Cases() {
  const [data, setData] = useState<CaseData[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchCases = () => {
    setLoading(true);
    fetch(`${API_BASE_URL}/api/cases`)
      .then(r => r.json())
      .then(res => {
        setData(res);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const updateCaseStatus = (id: string, newStatus: string) => {
    fetch(`${API_BASE_URL}/api/cases/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    })
    .then(r => {
      if (!r.ok) {
        throw new Error('Failed to update case');
      }
      return r.json();
    })
    .then(() => {
       fetchCases();
    })
    .catch(console.error);
  };

  const columns = useMemo(() => [
    columnHelper.accessor('id', {
      header: 'Case ID',
      cell: info => <span className="font-mono text-gray-300">{info.getValue()}</span>,
    }),
    columnHelper.accessor('sender_account_id', {
      header: 'Account ID',
      cell: info => (
        <a href={`/graph/${info.getValue()}`} className="font-mono text-emerald-400 hover:underline">
           {info.getValue()}
        </a>
      ),
    }),
    columnHelper.accessor('unified_score', {
      header: 'Risk Score',
      cell: info => {
        const score = info.getValue()
        const normalized = Math.round(score * 100)
        const color = normalized > 80 ? 'text-red-500' : normalized > 50 ? 'text-yellow-500' : 'text-green-500'
        return <span className={`font-bold ${color}`}>{normalized}</span>
      },
    }),
    columnHelper.accessor('status', {
      header: 'Status',
      cell: info => {
        const status = info.getValue()
        return (
          <span className={`px-2 py-1 rounded text-xs font-bold ${
            status === 'OPEN' ? 'bg-red-950 text-red-500' : 
            status === 'INVESTIGATING' ? 'bg-blue-950 text-blue-400' : 'bg-gray-800 text-gray-400'
          }`}>
            {status}
          </span>
        )
      },
    }),
    columnHelper.accessor('created_at', {
      header: 'Date Time',
      cell: info => new Date(info.getValue()).toLocaleString()
    }),
    columnHelper.display({
      id: 'actions',
      header: 'Actions',
      cell: info => (
        <div className="flex gap-2">
           {info.row.original.status === 'OPEN' && (
             <button 
               onClick={() => updateCaseStatus(info.row.original.id, 'INVESTIGATING')}
               className="px-2 py-1 text-xs rounded border border-blue-500 text-blue-400 hover:bg-blue-900/30"
             >
               Investigate
             </button>
           )}
           {(info.row.original.status === 'OPEN' || info.row.original.status === 'INVESTIGATING') && (
             <>
               <button 
                 onClick={() => updateCaseStatus(info.row.original.id, 'CLOSED')}
                 className="px-2 py-1 text-xs rounded border border-green-500 text-green-400 hover:bg-green-900/30"
               >
                 Approve
               </button>
               <button 
                 onClick={() => updateCaseStatus(info.row.original.id, 'PENDING_STR')}
                 className="px-2 py-1 text-xs rounded border border-red-500 text-red-400 hover:bg-red-900/30"
               >
                 Escalate
               </button>
             </>
           )}
        </div>
      )
    })
  ], []);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold">Case Management</h2>
        <button 
          onClick={fetchCases}
          disabled={loading}
          className="bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-500 transition text-sm disabled:opacity-50"
        >
          {loading ? "Refreshing..." : "Refresh Cases"}
        </button>
      </div>

      <div className="bg-dark-surface border border-gray-800 rounded-xl overflow-hidden">
         <div className="p-6 border-b border-gray-800 flex justify-between items-center">
            <h3 className="font-semibold text-lg">Active Investigations</h3>
         </div>
         <div className="p-6 overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                {table.getHeaderGroups().map(headerGroup => (
                  <tr key={headerGroup.id} className="border-b border-gray-800">
                    {headerGroup.headers.map(header => (
                      <th key={header.id} className="p-4 text-sm font-semibold text-gray-400 uppercase tracking-wider">
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody className="divide-y divide-gray-800/50">
                {data.length === 0 ? (
                   <tr>
                      <td colSpan={6} className="p-8 text-center text-gray-500 italic">
                        No suspicious cases reported in history. Run integration tests to stream events.
                      </td>
                   </tr>
                ) : table.getRowModel().rows.map(row => (
                  <tr key={row.id} className="hover:bg-gray-800/20 transition">
                    {row.getVisibleCells().map(cell => (
                      <td key={cell.id} className="p-4">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
         </div>
      </div>
    </div>
  );
}
