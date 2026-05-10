import { useEffect, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper
} from '@tanstack/react-table';

type CaseData = {
  id: string;
  transaction_id: string;
  riskScore: number;
  status: string;
  created: string;
}

const columnHelper = createColumnHelper<CaseData>()

const columns = [
  columnHelper.accessor('id', {
    header: 'Case ID',
    cell: info => <span className="font-mono text-gray-300">{info.getValue()}</span>,
  }),
  columnHelper.accessor('transaction_id', {
    header: 'Transaction ID',
    cell: info => <span className="font-mono text-gray-400">{info.getValue()}</span>,
  }),
  columnHelper.accessor('riskScore', {
    header: 'Risk Score',
    cell: info => {
      const score = info.getValue()
      const color = score > 80 ? 'text-red-500' : score > 50 ? 'text-yellow-500' : 'text-green-500'
      return <span className={`font-bold ${color}`}>{score}</span>
    },
  }),
  columnHelper.accessor('status', {
    header: 'Status',
    cell: info => {
      const status = info.getValue()
      return (
        <span className={`px-2 py-1 rounded text-xs font-bold ${
          status === 'Open' ? 'bg-red-950 text-red-500' : 'bg-gray-800 text-gray-400'
        }`}>
          {status}
        </span>
      )
    },
  }),
  columnHelper.accessor('created', {
    header: 'Created At',
  }),
]

export default function Cases() {
  const [data, setData] = useState<CaseData[]>([])

  useEffect(() => {
    void (async () => {
      try {
        const resp = await fetch("http://localhost:8005/api/cases?limit=200");
        if (!resp.ok) {
          return;
        }
        const rows = await resp.json();
        setData(
          rows.map((row: { id: string; transaction_id: string; risk_score: number; status: string; created_at: string }) => ({
            id: row.id,
            transaction_id: row.transaction_id,
            riskScore: row.risk_score,
            status: row.status,
            created: row.created_at,
          }))
        );
      } catch {
        // fallback to empty state
      }
    })();
  }, [])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Case Management</h2>
      <div className="bg-dark-surface border border-gray-800 rounded-xl overflow-hidden">
         <div className="p-6 border-b border-gray-800 flex justify-between items-center">
            <h3 className="font-semibold text-lg">Active Investigations</h3>
            <button className="bg-gray-800 text-gray-200 px-4 py-2 rounded-lg hover:bg-gray-700 transition">Filter</button>
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
                {table.getRowModel().rows.map(row => (
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
