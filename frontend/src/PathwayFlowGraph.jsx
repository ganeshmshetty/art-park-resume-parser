import React, { useMemo } from "react";
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    BackgroundVariant,
    Handle,
    Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { Map } from "lucide-react";

/* ---- Phase config ---- */
const PHASE_CONFIG = {
    Foundation: { color: "#3b82f6", badge: "Foundation" },
    Core: { color: "#a855f7", badge: "Core" },
    Advanced: { color: "#f87171", badge: "Advanced" },
};

/* ---- Custom Node ---- */
function PathwayNode({ id, data }) {
    const cfg = PHASE_CONFIG[data.phase] || PHASE_CONFIG.Foundation;
    return (
        <div
            className={`rf-node phase-${data.phase?.toLowerCase()}`}
            style={{ 
                border: "2px solid #1a1b24",
                padding: "16px",
                borderRadius: "12px",
                background: "#ffffff",
                boxShadow: "4px 4px 0px 0px #1a1b24",
                minWidth: "200px"
            }}
            onClick={() => data.onSelect && data.onSelect(data)}
        >
            <Handle type="target" position={Position.Left} style={{ background: cfg.color }} />
            <div style={{ 
                fontSize: "10px", 
                fontWeight: 700, 
                backgroundColor: cfg.color, 
                color: "#fff", 
                padding: "2px 8px", 
                borderRadius: "10px", 
                display: "inline-block" 
            }}>
                {cfg.badge}
            </div>
            <div style={{ fontWeight: 700, marginTop: "8px", fontSize: "14px", color: "#1a1b24" }}>{data.title}</div>
            <div style={{ fontSize: "11px", color: "#5d5d68", marginTop: "4px" }}>{data.module_id || id}</div>
            <Handle type="source" position={Position.Right} style={{ background: cfg.color }} />
        </div>
    );
}

const NODE_TYPES = { pathway: PathwayNode };

/* ---- Layout Helper ---- */
function buildLayout(nodes, edges) {
    const PHASE_ORDER = ["Foundation", "Core", "Advanced"];
    const groups = {};
    PHASE_ORDER.forEach((p) => { groups[p] = []; });

    nodes.forEach((n) => {
        const rawPhase = n.phase || "Foundation";
        const phase = PHASE_ORDER.find(p => p.toLowerCase() === rawPhase.toLowerCase()) || "Foundation";
        groups[phase].push(n);
    });

    const rfNodes = [];
    let col = 0;
    PHASE_ORDER.forEach((phase) => {
        const group = groups[phase];
        group.forEach((n, row) => {
            rfNodes.push({
                id: n.module_id || `n-${Math.random()}`,
                type: "pathway",
                position: { x: col * 320, y: row * 160 },
                data: { ...n, phase },
            });
        });
        if (group.length > 0) col++;
    });

    // FALLBACK IF EMPTY
    if (rfNodes.length === 0 && nodes.length > 0) {
        console.warn("[Graph] rfNodes is empty despite having raw nodes!", nodes);
    }

    const sourceEdges = edges && edges.length > 0 ? edges : [];
    // If no edges from backend, build sequential ones
    const finalEdges = sourceEdges.length > 0 ? sourceEdges : (rfNodes.length > 1 ? rfNodes.slice(0, -1).map((n, i) => ({ from: n.id, to: rfNodes[i+1].id })) : []);

    const rfEdges = finalEdges.map((e, i) => ({
        id: `e-${i}`,
        source: e.from || e.source,
        target: e.to || e.target,
        animated: true,
        style: { stroke: "#6e76ff", strokeWidth: 2.5 },
    }));

    return { rfNodes, rfEdges };
}

export default function PathwayFlowGraph({ pathway, onSelectModule }) {
    console.log("[Graph] Prop 'pathway' received:", pathway);
    const rawNodes = pathway?.nodes || [];
    const rawEdges = pathway?.edges || [];

    const { rfNodes, rfEdges } = useMemo(
        () => {
            const layout = buildLayout(rawNodes, rawEdges);
            // Inject onSelectModule
            layout.rfNodes = layout.rfNodes.map(n => ({
                ...n,
                data: { ...n.data, onSelect: onSelectModule }
            }));
            console.log("[Graph] Built layout:", layout.rfNodes.length, "nodes,", layout.rfEdges.length, "edges");
            return layout;
        },
        [rawNodes, rawEdges, onSelectModule]
    );

    if (rawNodes.length === 0) return null;

    return (
        <div className="glass-card flow-card" style={{ padding: 0, overflow: "hidden", marginBottom: "48px" }}>
            <div className="flow-header" style={{ padding: "20px 32px", borderBottom: "2px solid #1a1b24", backgroundColor: "#fff" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", fontWeight: 700, fontSize: "20px" }}>
                    <Map size={24} /> Adaptive Learning Pathway
                </div>
            </div>

            <div style={{ height: "550px", backgroundColor: "#f3f0f7", position: "relative" }}>
                <ReactFlow
                    nodes={rfNodes}
                    edges={rfEdges}
                    nodeTypes={NODE_TYPES}
                    fitView
                    fitViewOptions={{ padding: 0.3 }}
                >
                    <Background variant={BackgroundVariant.Dots} gap={24} color="#1a1b24" />
                    <Controls />
                    <MiniMap />
                </ReactFlow>
            </div>
        </div>
    );
}

