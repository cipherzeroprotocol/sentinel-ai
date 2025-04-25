"use client";

import React, { useEffect, useRef, useState } from 'react';
import ReactFlow, { 
  Node, 
  Edge, 
  Position, 
  Background,
  Controls,
  MiniMap,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';
import { AlertTriangle, Activity, CornerRightDown } from 'lucide-react';

interface Transaction {
  id: string;
  source: string;
  target: string;
  amount: number;
  timestamp: string;
  type?: string;
  isSuspicious?: boolean;
}

interface Address {
  address: string;
  label?: string;
  type?: string; 
  isSuspicious?: boolean;
  risk?: number;
}

interface TransactionFlowProps {
  transactions: Transaction[];
  addresses: {[key: string]: Address};
  height?: number;
  width?: string;
  fitView?: boolean;
  interactive?: boolean;
  title?: string;
}

// Custom node types
const nodeTypes = {
  // Custom node types could be defined here
};

const TransactionFlow: React.FC<TransactionFlowProps> = ({ 
  transactions, 
  addresses, 
  height = 400, 
  width = '100%', 
  fitView = true, 
  interactive = false,
  title
}) => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<string | null>(null);

  // Format addresses for display
  const formatAddress = (address: string): string => {
    if (!address) return 'Unknown';
    if (address.length <= 12) return address;
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  // Process transactions into graph data
  useEffect(() => {
    if (!transactions.length) return;

    // Create a set of unique addresses to avoid duplicates
    const uniqueAddresses = new Set<string>();
    transactions.forEach(tx => {
      uniqueAddresses.add(tx.source);
      uniqueAddresses.add(tx.target);
    });

    // Create nodes for each unique address
    const graphNodes: Node[] = Array.from(uniqueAddresses).map((address, index) => {
      const addressInfo = addresses[address] || { address };
      const isSuspicious = addressInfo.isSuspicious || false;
      const nodeType = addressInfo.type || 'address';
      const label = addressInfo.label || formatAddress(address);
      
      // Position nodes in a circle layout by default
      const angle = (index / uniqueAddresses.size) * 2 * Math.PI;
      const radius = 250;
      const x = radius * Math.cos(angle);
      const y = radius * Math.sin(angle);
      
      // Determine node style based on type and risk
      let nodeStyle = {};
      let nodeClass = 'border-2';
      
      if (isSuspicious) {
        nodeClass += ' border-red-500 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300';
      } else if (nodeType === 'exchange') {
        nodeClass += ' border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300';
      } else if (nodeType === 'contract') {
        nodeClass += ' border-purple-500 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300';
      } else if (nodeType === 'mixer') {
        nodeClass += ' border-orange-500 bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-300';
      } else {
        nodeClass += ' border-green-500 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300';
      }
      
      return {
        id: address,
        data: { 
          label,
          address,
          type: nodeType,
          isSuspicious,
          risk: addressInfo.risk || 0
        },
        position: { x, y },
        type: 'default',
        className: nodeClass,
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      };
    });

    // Create edges for each transaction
    const graphEdges: Edge[] = transactions.map(tx => {
      const isHighValue = tx.amount > 100; // Example threshold, adjust as needed
      const isSuspicious = tx.isSuspicious || false;
      
      // Determine edge style
      let edgeClass = 'transition-all';
      let animated = false;
      let style = {};
      
      if (isSuspicious) {
        edgeClass += ' text-red-500';
        style = { stroke: '#ef4444', strokeWidth: 2 };
        animated = true;
      } else if (isHighValue) {
        edgeClass += ' text-blue-500';
        style = { stroke: '#3b82f6', strokeWidth: Math.min(1 + Math.log10(tx.amount) * 0.5, 5) };
      } else {
        edgeClass += ' text-gray-400';
        style = { stroke: '#9ca3af', strokeWidth: 1 };
      }

      return {
        id: tx.id,
        source: tx.source,
        target: tx.target,
        animated,
        style,
        className: edgeClass,
        data: {
          amount: tx.amount,
          timestamp: tx.timestamp,
          type: tx.type || 'transfer',
          isSuspicious
        },
        label: `${tx.amount.toFixed(2)} SOL`,
        labelStyle: { fill: isSuspicious ? '#ef4444' : '#6b7280', fontSize: 10 },
        labelBgStyle: { fill: 'rgba(255, 255, 255, 0.8)', fillOpacity: 0.8 }
      };
    });

    setNodes(graphNodes);
    setEdges(graphEdges);
  }, [transactions, addresses]);

  const handleNodeClick = (event: React.MouseEvent, node: Node) => {
    if (!interactive) return;
    setSelectedNode(node.id === selectedNode ? null : node.id);
    setSelectedEdge(null);
  };

  const handleEdgeClick = (event: React.MouseEvent, edge: Edge) => {
    if (!interactive) return;
    setSelectedEdge(edge.id === selectedEdge ? null : edge.id);
    setSelectedNode(null);
  };

  if (!transactions.length) {
    return (
      <div className="flex items-center justify-center border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50 p-6" style={{ height }}>
        <div className="text-center">
          <Activity className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">No transaction data available</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ height, width }} className="rounded-lg border border-gray-200 dark:border-gray-700">
      {title && <h4 className="px-4 pt-3 text-base font-medium">{title}</h4>}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={handleNodeClick}
        onEdgeClick={handleEdgeClick}
        fitView={fitView}
        nodesDraggable={interactive}
        nodesConnectable={false}
        nodesFocusable={interactive}
        edgesFocusable={interactive}
        nodeTypes={nodeTypes}
        zoomOnScroll={interactive}
        panOnScroll={interactive}
      >
        <Background />
        <Controls showInteractive={interactive} />
        {interactive && <MiniMap zoomable pannable />}
        
        {/* Information panel */}
        {interactive && (
          <Panel position="top-right" className="bg-white dark:bg-gray-800 p-2 rounded shadow-md border border-gray-200 dark:border-gray-700 text-xs">
            <div className="flex flex-col space-y-1">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                <span>Regular Address</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                <span>Exchange</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-purple-500 rounded-full mr-2"></div>
                <span>Contract</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                <span>Suspicious</span>
              </div>
            </div>
          </Panel>
        )}
        
        {/* Selected node/edge details */}
        {interactive && selectedNode && (
          <Panel position="bottom-center" className="bg-white dark:bg-gray-800 p-3 rounded shadow-md border border-gray-200 dark:border-gray-700">
            <div className="text-sm">
              <h4 className="font-medium">{addresses[selectedNode]?.label || formatAddress(selectedNode)}</h4>
              <div className="text-xs font-mono mt-1">{selectedNode}</div>
              <div className="mt-1 flex items-center">
                <span className="text-gray-500 mr-2">Type:</span>
                <span>{addresses[selectedNode]?.type || 'Regular Address'}</span>
              </div>
              {addresses[selectedNode]?.isSuspicious && (
                <div className="mt-1 flex items-center text-red-500">
                  <AlertTriangle size={14} className="mr-1" />
                  <span>Suspicious Activity Detected</span>
                </div>
              )}
              <button 
                className="mt-2 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={() => window.open(`https://solscan.io/account/${selectedNode}`, '_blank')}
              >
                View on Explorer
              </button>
            </div>
          </Panel>
        )}
        
        {interactive && selectedEdge && (
          <Panel position="bottom-center" className="bg-white dark:bg-gray-800 p-3 rounded shadow-md border border-gray-200 dark:border-gray-700">
            <div className="text-sm">
              <h4 className="font-medium flex items-center">
                <span>{formatAddress(edges.find(e => e.id === selectedEdge)?.source || '')}</span>
                <CornerRightDown size={14} className="mx-1" />
                <span>{formatAddress(edges.find(e => e.id === selectedEdge)?.target || '')}</span>
              </h4>
              <div className="mt-1">
                <span className="text-gray-500 mr-2">Amount:</span>
                <span className="font-medium">{edges.find(e => e.id === selectedEdge)?.data?.amount.toFixed(4) || '0'} SOL</span>
              </div>
              <div className="mt-1">
                <span className="text-gray-500 mr-2">Transaction:</span>
                <span className="font-mono text-xs">{selectedEdge}</span>
              </div>
              <div className="mt-1">
                <span className="text-gray-500 mr-2">Type:</span>
                <span>{edges.find(e => e.id === selectedEdge)?.data?.type || 'Transfer'}</span>
              </div>
              {edges.find(e => e.id === selectedEdge)?.data?.isSuspicious && (
                <div className="mt-1 flex items-center text-red-500">
                  <AlertTriangle size={14} className="mr-1" />
                  <span>Suspicious Transaction</span>
                </div>
              )}
              <button 
                className="mt-2 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={() => window.open(`https://solscan.io/tx/${selectedEdge}`, '_blank')}
              >
                View on Explorer
              </button>
            </div>
          </Panel>
        )}
      </ReactFlow>
    </div>
  );
};

export default TransactionFlow;
