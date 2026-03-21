import React, { useState, useMemo, useCallback } from "react";
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    BackgroundVariant,
    Handle,
    Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { Map, Clock, CheckCircle, Circle } from "lucide-react";

/* ---- Phase config ---- */
const PHASE_CONFIG = {
    Foundation: { color: "#3b82f6", badge: "Foundation", bg: "rgba(59,130,246,0.08)", icon: "🏗" },
    Core: { color: "#a855f7", badge: "Core", bg: "rgba(168,85,247,0.08)", icon: "⚙️" },
    Advanced: { color: "#f87171", badge: "Advanced", bg: "rgba(248,113,113,0.08)", icon: "🚀" },
};

/* ---- Phase Divider Node ---- */
function PhaseHeaderNode({ data }) {
    const cfg = PHASE_CONFIG[data.phase] || PHASE_CONFIG.Foundation;
    return (
        <div style={{
            width: "360px",
            padding: "12px 24px",
            borderRadius: "12px",
            background: cfg.bg,
            border: `2px dashed ${cfg.color}`,
            display: "flex",
            alignItems: "center",
            gap: "10px",
            pointerEvents: "none",
            userSelect: "none",
        }}>
            <span style={{ fontSize: "20px" }}>{cfg.icon}</span>
            <div>
                <div style={{
                    fontSize: "13px",
                    fontWeight: 800,
                    textTransform: "uppercase",
                    letterSpacing: "1px",
                    color: cfg.color,
                }}>
                    {cfg.badge} Phase
                </div>
                <div style={{ fontSize: "11px", color: "#5d5d68", marginTop: "2px" }}>
                    {data.count} module{data.count !== 1 ? "s" : ""}
                </div>
            </div>
        </div>
    );
}

/* ---- Module Card Node ---- */
function PathwayNode({ id, data }) {
    const cfg = PHASE_CONFIG[data.phase] || PHASE_CONFIG.Foundation;
    const isCompleted = data.completed;
    const duration = data.estimated_duration || 60;

    return (
        <div
            className={`rf-node phase-${data.phase?.toLowerCase()}`}
            style={{
                border: isCompleted ? "2px solid #22c55e" : "2px solid #1a1b24",
                padding: "20px",
                borderRadius: "16px",
                background: isCompleted ? "#f0fff4" : "#ffffff",
                boxShadow: isCompleted ? "4px 4px 0px 0px #22c55e" : "4px 4px 0px 0px #1a1b24",
                minWidth: "320px",
                maxWidth: "360px",
                transition: "all 0.2s",
                cursor: "pointer",
            }}
            onClick={() => data.onSelect && data.onSelect(data)}
        >
            <Handle type="target" position={Position.Top} style={{ background: cfg.color, width: 10, height: 10, border: "2px solid #fff" }} />

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                <div style={{
                    fontSize: "11px",
                    fontWeight: 800,
                    backgroundColor: cfg.color,
                    color: "#fff",
                    padding: "4px 10px",
                    borderRadius: "20px",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                }}>
                    {cfg.badge}
                </div>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        data.onToggleComplete && data.onToggleComplete(id);
                    }}
                    style={{
                        background: "none", border: "none", cursor: "pointer", padding: 0,
                        color: isCompleted ? "#22c55e" : "#cbd5e1",
                        display: "flex", alignItems: "center",
                    }}
                >
                    {isCompleted
                        ? <CheckCircle size={26} fill="#22c55e" color="#fff" />
                        : <Circle size={26} strokeWidth={2} />}
                </button>
            </div>

            <div style={{ fontWeight: 800, fontSize: "16px", color: "#1a1b24", marginBottom: "12px", lineHeight: 1.3 }}>
                {data.title}
            </div>

            <div style={{ display: "flex", gap: "16px", fontSize: "12px", color: "#5d5d68", fontWeight: 600 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <Clock size={14} /> {duration} min
                </div>
                {data.skill_gaps_covered?.length > 0 && (
                    <div>• {data.skill_gaps_covered.length} skill{data.skill_gaps_covered.length !== 1 ? "s" : ""}</div>
                )}
            </div>

            <Handle type="source" position={Position.Bottom} style={{ background: cfg.color, width: 10, height: 10, border: "2px solid #fff" }} />
        </div>
    );
}

const NODE_TYPES = { pathway: PathwayNode, phaseHeader: PhaseHeaderNode };

/* ---- Layout Helper ---- */
const PHASE_ORDER = ["Foundation", "Core", "Advanced"];
const NODE_H = 180;      // height of a module card
const HEADER_H = 80;     // height of a phase header
const GAP_BETWEEN = 40;  // gap between items
const PHASE_GAP = 60;    // extra gap before a new phase header

function buildLayout(nodes, edges, completedMods, onToggleComplete) {
    // Normalise phase names
    const normalisePhase = (raw) =>
        PHASE_ORDER.find(p => p.toLowerCase() === (raw || "").toLowerCase()) || "Foundation";

    // Group nodes by phase while preserving topological order
    const groups = { Foundation: [], Core: [], Advanced: [] };
    nodes.forEach(n => groups[normalisePhase(n.phase)].push(n));

    const rfNodes = [];
    const nodeIdSet = new Set();      // module node ids so we can skip edges to/from headers
    let yOffset = 0;

    PHASE_ORDER.forEach(phase => {
        const group = groups[phase];
        if (group.length === 0) return;

        // --- Phase Header Divider ---
        if (rfNodes.length > 0) yOffset += PHASE_GAP;       // extra breathing room before each phase
        const headerId = `__phase_header_${phase}`;
        rfNodes.push({
            id: headerId,
            type: "phaseHeader",
            position: { x: 0, y: yOffset },
            data: { phase, count: group.length },
            draggable: false,
            selectable: false,
        });
        yOffset += HEADER_H + GAP_BETWEEN;

        // --- Module Cards for this phase ---
        group.forEach(n => {
            const nodeId = n.module_id || `n-${Math.random()}`;
            rfNodes.push({
                id: nodeId,
                type: "pathway",
                position: { x: 0, y: yOffset },
                data: {
                    ...n,
                    phase,
                    completed: completedMods.has(n.module_id),
                    onToggleComplete,
                },
            });
            nodeIdSet.add(nodeId);
            yOffset += NODE_H + GAP_BETWEEN;
        });
    });

    // --- Edges (only between real module nodes) ---
    const sourceEdges = edges && edges.length > 0 ? edges : [];
    const realNodeIds = [...nodeIdSet];

    const finalEdges =
        sourceEdges.length > 0
            ? sourceEdges.filter(e => nodeIdSet.has(e.source ?? e.from) && nodeIdSet.has(e.target ?? e.to))
            : realNodeIds.length > 1
                ? realNodeIds.slice(0, -1).map((id, i) => ({ source: id, target: realNodeIds[i + 1] }))
                : [];

    const rfEdges = finalEdges.map((e, i) => {
        const sourceId = e.source ?? e.from;
        const targetId = e.target ?? e.to;
        const done = completedMods.has(sourceId);
        return {
            id: `e-${i}`,
            source: sourceId,
            target: targetId,
            animated: !done,
            style: { stroke: done ? "#22c55e" : "#a5b4fc", strokeWidth: 2.5 },
        };
    });

    return { rfNodes, rfEdges };
}

/* ---- Component ---- */
export default function PathwayFlowGraph({ pathway, onSelectModule }) {
    console.log("[Graph] Prop 'pathway' received:", pathway);
    const rawNodes = pathway?.nodes || [];
    const rawEdges = pathway?.edges || [];

    const [completedMods, setCompletedMods] = useState(new Set());

    const handleToggleComplete = useCallback((moduleId) => {
        setCompletedMods(prev => {
            const next = new Set(prev);
            next.has(moduleId) ? next.delete(moduleId) : next.add(moduleId);
            return next;
        });
    }, []);

    const { rfNodes, rfEdges } = useMemo(() => {
        const layout = buildLayout(rawNodes, rawEdges, completedMods, handleToggleComplete);
        layout.rfNodes = layout.rfNodes.map(n =>
            n.type === "pathway"
                ? { ...n, data: { ...n.data, onSelect: onSelectModule } }
                : n
        );
        return layout;
    }, [rawNodes, rawEdges, completedMods, handleToggleComplete, onSelectModule]);

    if (rawNodes.length === 0) return null;

    const total = rawNodes.length;
    const completed = completedMods.size;
    const pct = total === 0 ? 0 : Math.round((completed / total) * 100);

    return (
        <div className="glass-card flow-card" style={{ padding: 0, overflow: "hidden", marginBottom: "48px" }}>
            {/* Header */}
            <div className="flow-header" style={{ padding: "20px 32px", borderBottom: "2px solid #1a1b24", backgroundColor: "#fff" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px", fontWeight: 800, fontSize: "20px" }}>
                        <Map size={24} /> Learning Roadmap
                    </div>

                    {/* Progress */}
                    <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                        <div style={{ fontWeight: 600, fontSize: "14px", color: "#5d5d68" }}>
                            {completed} of {total} completed
                        </div>
                        <div style={{
                            width: "150px", height: "12px",
                            background: "#f3f0f7", borderRadius: "10px",
                            overflow: "hidden", border: "1px solid #1a1b24",
                        }}>
                            <div style={{
                                width: `${pct}%`, height: "100%",
                                background: "#22c55e",
                                transition: "width 0.4s cubic-bezier(0.4,0,0.2,1)",
                            }} />
                        </div>
                        <div style={{ fontWeight: 800, fontSize: "16px", color: pct === 100 ? "#22c55e" : "#1a1b24" }}>
                            {pct}%
                        </div>
                    </div>
                </div>
            </div>

            {/* Flow Canvas */}
            <div style={{ height: "750px", backgroundColor: "#f3f0f7", position: "relative" }}>
                <ReactFlow
                    nodes={rfNodes}
                    edges={rfEdges}
                    nodeTypes={NODE_TYPES}
                    fitView
                    fitViewOptions={{ padding: 0.2 }}
                >
                    <Background variant={BackgroundVariant.Dots} gap={24} color="#c4c9d8" />
                    <Controls />
                    <MiniMap nodeColor={n => {
                        if (n.type === "phaseHeader") return "#e0e0e0";
                        const phase = n.data?.phase;
                        return PHASE_CONFIG[phase]?.color ?? "#94a3b8";
                    }} />
                </ReactFlow>
            </div>
        </div>
    );
}