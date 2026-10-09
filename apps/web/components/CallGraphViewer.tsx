import ReactFlow, { MiniMap, Controls, Background, Handle, Position } from 'reactflow';
import type { Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';
import { RiskBadge } from './RiskBadge';
import type { RiskTier } from './RiskBadge';
import { Activity, GitBranch, Zap } from 'lucide-react';

interface GraphNodeData {
  label: string;
  tier: RiskTier;
  fanOut: number;
}

const CustomNode = ({ data }: { data: GraphNodeData }) => (
  <div className="custom-node">
    <Handle type="target" position={Position.Top} style={{ background: 'var(--accent-primary)', border: 'none' }} />
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
      <div style={{ padding: 6, borderRadius: 6, background: 'var(--bg-primary)', border: '1px solid var(--border-color)' }}>
        <Activity size={14} color="var(--accent-primary)" />
      </div>
      <div style={{ fontWeight: '600', fontSize: 13, color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {data.label}
      </div>
    </div>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
      <RiskBadge tier={data.tier} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--text-tertiary)' }}>
        <GitBranch size={12} />
        <span>{data.fanOut}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} style={{ background: 'var(--accent-primary)', border: 'none' }} />
  </div>
);

const nodeTypes = {
  custom: CustomNode,
};

interface CallGraphViewerProps {
  nodes: Node<GraphNodeData>[];
  edges: Edge[];
}

export const CallGraphViewer = ({ nodes, edges }: CallGraphViewerProps) => {
  return (
    <div style={{ height: '600px', width: '100%', position: 'relative' }} className="glass-panel">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: true,
          style: { stroke: 'var(--border-color)', strokeWidth: 2 },
        }}
      >
        <Background color="var(--border-color)" gap={20} size={1} />
        <Controls 
          style={{ 
            display: 'flex', 
            flexDirection: 'row', 
            bottom: 20, 
            left: 20, 
            background: 'var(--bg-tertiary)', 
            border: '1px solid var(--border-color)',
            borderRadius: 8,
            padding: 4
          }} 
        />
        <MiniMap 
          nodeColor={(n: any) => {
            if (n.data?.tier === 'CRITICAL') return '#ff4d4f';
            if (n.data?.tier === 'HIGH') return '#faad14';
            return '#0c0c0c';
          }} 
          maskColor="rgba(0,0,0,0.7)"
          style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', borderRadius: 12 }}
        />
      </ReactFlow>
      <div style={{ position: 'absolute', top: 20, right: 20, zIndex: 10, display: 'flex', gap: 12 }}>
        <div className="glass-panel" style={{ padding: '8px 12px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Zap size={14} color="var(--tier-critical)" className="animate-pulse-slow" />
          <span style={{ fontWeight: 600 }}>Impact Map Active</span>
        </div>
      </div>
    </div>
  );
};
