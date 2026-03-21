import React, { useState, useMemo, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    BackgroundVariant,
    Handle,
    Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { Map, Clock, CheckCircle, Circle, Maximize2, Minimize2 } from "lucide-react";

/* ---- Phase config ---- */
const PHASE_CONFIG = {
    Foundation: { color: "#3b82f6", badge: "Foundation" },
    Core: { color: "#a855f7", badge: "Core" },
    Advanced: { color: "#f87171", badge: "Advanced" },
};

/* ---- Custom Node ---- */
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
                minWidth: "280px",
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
                    letterSpacing: "0.5px"
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
                        display: "flex", alignItems: "center"
                    }}
                >
                    {isCompleted ? <CheckCircle size={26} fill="#22c55e" color="#fff" /> : <Circle size={26} strokeWidth={2} />}
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
                    <div style={{ display: "flex", alignItems: "center" }}>• {data.skill_gaps_covered.length} skills</div>
                )}
            </div>

            <Handle type="source" position={Position.Bottom} style={{ background: cfg.color, width: 10, height: 10, border: "2px solid #fff" }} />
        </div>
    );
}

const NODE_TYPES = { pathway: PathwayNode };

/* ---- Layout Helper ---- */
function buildLayout(nodes, edges, completedMods, onToggleComplete) {
    // Top-to-bottom vertical layout using the topologically sorted order
    const rfNodes = nodes.map((n, i) => ({
        id: n.module_id || `n-${Math.random()}`,
        type: "pathway",
        position: { x: 0, y: i * 220 }, // Vertically arranged
        data: {
            ...n,
            completed: completedMods.has(n.module_id),
            onToggleComplete
        },
    }));

    const sourceEdges = edges && edges.length > 0 ? edges : [];
    const finalEdges = sourceEdges.length > 0 ? sourceEdges : (rfNodes.length > 1 ? rfNodes.slice(0, -1).map((n, i) => ({ from: n.id, to: rfNodes[i + 1].id })) : []);

    const rfEdges = finalEdges.map((e, i) => {
        const sourceId = e.from || e.source;
        const targetId = e.to || e.target;
        const isCompleted = completedMods.has(sourceId);

        return {
            id: `e-${i}`,
            source: sourceId,
            target: targetId,
            animated: !isCompleted,
            style: {
                stroke: isCompleted ? "#22c55e" : "#cbd5e1",
                strokeWidth: 2.5
            },
        };
    });

    return { rfNodes, rfEdges };
}

/* ---- Shared ReactFlow Canvas ---- */
function RoadmapCanvas({ rfNodes, rfEdges }) {
    return (
        <ReactFlow
            nodes={rfNodes}
            edges={rfEdges}
            nodeTypes={NODE_TYPES}
            fitView
            fitViewOptions={{ padding: 0.2 }}
        >
            <Background variant={BackgroundVariant.Dots} gap={24} color="rgba(26,27,36,0.15)" />
            <Controls />
            <MiniMap
                nodeColor={(n) => {
                    const cfg = PHASE_CONFIG[n.data?.phase];
                    return cfg?.color ?? "#94a3b8";
                }}
                style={{ border: "2px solid #1a1b24", borderRadius: 8 }}
            />
        </ReactFlow>
    );
}

export default function PathwayFlowGraph({ pathway, onSelectModule }) {
    const rawNodes = pathway?.nodes || [];
    const rawEdges = pathway?.edges || [];

    const [completedMods, setCompletedMods] = useState(new Set());
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Escape key exits fullscreen
    useEffect(() => {
        const onKey = (e) => { if (e.key === "Escape") setIsFullscreen(false); };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, []);

    // Lock body scroll when fullscreen
    useEffect(() => {
        document.body.style.overflow = isFullscreen ? "hidden" : "";
        return () => { document.body.style.overflow = ""; };
    }, [isFullscreen]);

    const handleToggleComplete = useCallback((moduleId) => {
        setCompletedMods(prev => {
            const next = new Set(prev);
            if (next.has(moduleId)) { next.delete(moduleId); } else { next.add(moduleId); }
            return next;
        });
    }, []);

    const { rfNodes, rfEdges } = useMemo(() => {
        const layout = buildLayout(rawNodes, rawEdges, completedMods, handleToggleComplete);
        layout.rfNodes = layout.rfNodes.map(n => ({
            ...n,
            data: { ...n.data, onSelect: onSelectModule }
        }));
        return layout;
    }, [rawNodes, rawEdges, completedMods, handleToggleComplete, onSelectModule]);

    if (rawNodes.length === 0) return null;

    const total = rawNodes.length;
    const completed = completedMods.size;
    const pct = total === 0 ? 0 : Math.round((completed / total) * 100);

    /* ---- Shared header ---- */
    const header = (
        <div style={{
            padding: "16px 28px",
            borderBottom: "2px solid #1a1b24",
            backgroundColor: "#fff",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
            flexShrink: 0,
        }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", fontWeight: 800, fontSize: "20px" }}>
                <Map size={22} /> Learning Roadmap
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                {/* Progress */}
                <div style={{ fontWeight: 600, fontSize: "13px", color: "#5d5d68" }}>
                    {completed} / {total} complete
                </div>
                <div style={{
                    width: "130px", height: "10px",
                    background: "#f3f0f7", borderRadius: "10px",
                    overflow: "hidden", border: "1px solid #1a1b24"
                }}>
                    <div style={{
                        width: `${pct}%`, height: "100%",
                        background: "#22c55e",
                        transition: "width 0.4s cubic-bezier(0.4, 0, 0.2, 1)"
                    }} />
                </div>
                <div style={{ fontWeight: 800, fontSize: "15px", color: pct === 100 ? "#22c55e" : "#1a1b24", minWidth: 36 }}>
                    {pct}%
                </div>

                {/* Expand / collapse button */}
                <button
                    onClick={() => setIsFullscreen(f => !f)}
                    title={isFullscreen ? "Minimize (Esc)" : "Expand roadmap"}
                    style={{
                        display: "flex", alignItems: "center", gap: "6px",
                        padding: "7px 14px",
                        border: "2px solid #1a1b24",
                        borderRadius: "8px",
                        background: isFullscreen ? "#1a1b24" : "#fff",
                        color: isFullscreen ? "#fff" : "#1a1b24",
                        fontWeight: 700, fontSize: "13px",
                        cursor: "pointer",
                        boxShadow: "2px 2px 0px 0px #1a1b24",
                        transition: "all 0.15s",
                    }}
                >
                    {isFullscreen
                        ? <><Minimize2 size={15} /> Minimize</>  
                        : <><Maximize2 size={15} /> Expand</>}
                </button>
            </div>
        </div>
    );

    /* ---- Inline (normal) view ---- */
    const inlineView = (
        <div className="glass-card flow-card" style={{ padding: 0, overflow: "hidden", marginBottom: "48px" }}>
            {header}
            <div style={{ height: "650px", backgroundColor: "#f3f0f7", position: "relative" }}>
                <RoadmapCanvas rfNodes={rfNodes} rfEdges={rfEdges} />
            </div>
        </div>
    );

    /* ---- Fullscreen portal ---- */
    const fullscreenView = createPortal(
        <div style={{
            position: "fixed", inset: 0, zIndex: 9999,
            display: "flex", flexDirection: "column",
            background: "#f3f0f7",
        }}>
            {header}
            <div style={{ flex: 1, position: "relative" }}>
                <RoadmapCanvas rfNodes={rfNodes} rfEdges={rfEdges} />
            </div>
        </div>,
        document.body
    );

    return (
        <>
            {inlineView}
            {isFullscreen && fullscreenView}
        </>
    );
}
