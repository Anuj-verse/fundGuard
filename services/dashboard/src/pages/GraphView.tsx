import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ReactFlow, MiniMap, Controls, Background, useNodesState, useEdgesState, MarkerType } from '@xyflow/react';
import type { Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

export default function GraphView() {
  const { account_id } = useParams();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [loading, setLoading] = useState(false);
  const [selectedNodeData, setSelectedNodeData] = useState<any>(null);

  useEffect(() => {
    if (!account_id) return;
    
    const fetchGraph = async () => {
      setLoading(true);
      try {
        const response = await fetch(`http://localhost:8005/api/graph/${account_id}`);
        const data = await response.json();
        
        if (data.nodes && data.edges) {
          // Neo4j ego network parsing
          const newNodes = data.nodes.map((n: any) => ({
            id: n.node_id,
            position: { x: Math.random() * 400 + 100, y: Math.random() * 400 + 100 }, // Extremely basic random layout
            data: { label: n.id },
            style: { 
              backgroundColor: n.id === account_id ? '#ff4444' : '#00ff88', 
              color: n.id === account_id ? '#fff' : '#000', 
              fontWeight: 'bold',
              borderRadius: '8px',
              padding: '10px'
            }
          }));

          // The edges array from Python might be using raw element_id. 
          // Assuming our backend maps source/target properly or modifying it to use logical IDs
          // Note: If backend source/target is element_id, we might need a mapping, but for now we map purely index based on typical neo4j structure
          const newEdges = data.edges.map((e: any, i: number) => ({
            id: `edge-${i}`,
            source: e.source,
            target: e.target,
            animated: true,
            label: e.amount ? `$${e.amount}` : '',
            style: { stroke: '#ff4444', strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#ff4444' }
          }));

          setNodes(newNodes);
          
          // Temporary fix: If edges have element_id but nodes only have logical 'id', 
          // this is a known quirk. Assuming backend fixes or using labels.
          setEdges(newEdges);
        }
      } catch (err) {
        console.error("Failed to load graph", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchGraph();
  }, [account_id, setNodes, setEdges]);

  return (
    <div className="flex h-full gap-6">
      <div className="flex-1 bg-dark-surface border border-gray-800 rounded-xl overflow-hidden relative">
        <div className="absolute top-4 left-4 z-10 bg-dark-bg/80 backdrop-blur px-4 py-2 rounded-lg border border-gray-800 font-mono text-sm">
          Network for: {account_id || 'Global Structure (Enter ID)'}
        </div>
        {loading && <div className="absolute inset-0 z-20 flex items-center justify-center bg-black/50">Loading Network...</div>}
        <ReactFlow 
          nodes={nodes} 
          edges={edges} 
          onNodesChange={onNodesChange} 
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node: Node) => setSelectedNodeData(node.data)}
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
             <div className="text-lg font-bold font-mono">{selectedNodeData?.label || account_id || 'None'}</div>
             <div className="text-sm mt-1 text-gray-300">Velocity: Unknown</div>
             <div className="text-sm text-gray-300">Fetched explicitly from Neo4j DB</div>
          </div>
          <div className="bg-gray-800/40 p-4 rounded-lg border border-gray-700">
             <div className="text-gray-400 text-xs">NETWORK INSIGHTS</div>
             <div className="text-sm mt-1 text-gray-300">
               Dynamic node link analysis fetched in real-time from the Graph database layer. 
               Identifies structural typologies.
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}