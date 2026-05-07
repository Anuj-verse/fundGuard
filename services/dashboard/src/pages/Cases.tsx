export default function Cases() {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Case Management</h2>
      <div className="bg-dark-surface border border-gray-800 rounded-xl overflow-hidden">
         <div className="p-6 border-b border-gray-800 flex justify-between items-center">
            <h3 className="font-semibold text-lg">Active Investigations</h3>
            <button className="bg-gray-800 text-gray-200 px-4 py-2 rounded-lg hover:bg-gray-700 transition">Filter</button>
         </div>
         <div className="p-8 flex items-center justify-center text-gray-500">
            [TanStack Table placeholder]
         </div>
      </div>
    </div>
  );
}