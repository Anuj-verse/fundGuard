import { useParams } from "react-router-dom";
import { ReactFlow, MiniMap, Controls, Background, useNodesState, useEdgesState } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes = [
  { id: '1', position: { x: 250, y: 150 }, data: { label: 'Account-X (Safe)' }, style: { backgroundColor: '#00ff88', color: '#000', fontWeight: 'bold' } },
  { id: '2', position: { x: 450, y: 50 }, data: { label: 'Mule-1 (High Risk)' }, style: { backgroundColor: '#ff4444', color: '#fff', fontWeight: 'bold' } },
  { id: '3', position: { x: 450, y: 250 }, data: { label: 'Mule-2 (High Risk)' }, style: { backgroundColor: '#ff4444', color: '#fff', fontWeight: 'bold' } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#ff4444', strokeWidth: 4 } },
  { id: 'e1-3', source: '1', target: '3', animated: true, style: { stroke: '#ff4444', strokeWidth: 2 } },
];

export default function GraphView() {
  const { account_id } = useParams();
  const [nodes, _, onNodesChange] = useNodesState(initialNodes);
  const [edges, __, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="flex h-full gap-6">
      <div className="flex-1 bg-dark-surface border border-gray-800 rounded-xl overflow-hidden relative">
        <div className="absolute top-4 left-4 z-10 bg-dark-bg/80 backdrop-blur px-4 py-2 rounded-lg border border-gray-800 font-mono text-sm">
          Network for: {account_id || 'Global Structure'}
        </div>
        <ReactFlow 
          nodes={nodes} 
          edges={edges} 
          onNodesChange={onNodesChange} 
          onEdgesChange={onEdgesChange} 
          fitView
          colorMode="dark"
        >
          <Controls />
          <MiniMap />
          <Background gap={12} size={1} />
        </ReactFlow>
      </div>
      <div className="w-96 bg-dark-surface border border-gray-800 rounded-xl flex flex-col">
        <div className="p-4 border-b border-gray-800 font-semibold">Entity Intelligence</div>
        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          <div className="bg-gray-800/40 p-4 rounded-lg border border-gray-700">
             <div className="text-gray-400 text-xs">SELECTED NODE</div>
             <div className="text-lg font-bold font-mono">Account-X</div>
             <div className="text-sm mt-1 text-gray-300">Velocity: High (8 tx/hr)</div>
             <div className="text-sm text-gray-300">Known Risk: 0.12</div>
          </div>
          <div className="bg-gray-800/40 p-4 rounded-lg border border-gray-700">
             <div className="text-gray-400 text-xs">LLM RATIONALE</div>
             <div className="text-sm mt-1 text-gray-300">
               Transfers exhibiting "smurfing" attributes leading up to multi-directional fan-out. Correlates heavily with typologies cited by FC-1001.
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}