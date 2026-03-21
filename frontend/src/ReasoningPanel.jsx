import { CheckCircle } from "lucide-react";

export default function ReasoningPanel({ module: mod, traces, onClose }) {
    if (!mod) return null;

    const trace = mod.reasoning || traces?.find((t) => t.module_id === mod.module_id);

    return (
        <>
            <div className="reasoning-overlay" onClick={onClose} />
            <aside className="reasoning-drawer" role="complementary" aria-label="Reasoning trace">
                {/* Header */}
                <div className="drawer-header">
                    <div>
                        <div
                            style={{
                                fontSize: 11,
                                fontWeight: 700,
                                textTransform: "uppercase",
                                letterSpacing: "0.5px",
                                color: "var(--text-muted)",
                                marginBottom: 6,
                            }}
                        >
                            Module Reasoning
                        </div>
                        <div
                            style={{ fontSize: 17, fontWeight: 700, color: "var(--text-primary)" }}
                        >
                            {mod.title}
                        </div>
                        <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                            {mod.module_id} · Phase:{" "}
                            <span
                                style={{
                                    color:
                                        mod.phase === "Foundation"
                                            ? "var(--phase-foundation)"
                                            : mod.phase === "Core"
                                                ? "var(--phase-core)"
                                                : "var(--phase-advanced)",
                                    fontWeight: 600,
                                }}
                            >
                                {mod.phase}
                            </span>
                        </div>
                    </div>
                    <button
                        className="drawer-close"
                        onClick={onClose}
                        aria-label="Close panel"
                    >
                        x
                    </button>
                </div>

                    {/* Body */}
                    <div className="drawer-body">
                    {/* Reasoning Text */}
                    {trace && (
                        <div className="trace-section">
                            <div className="trace-section-label">Chain-of-Thought</div>
                            <div className="trace-text">
                                {trace.justification || "No reasoning trace available."}
                            </div>
                        </div>
                    )}

                    {/* Skills Targeted */}
                    {mod.skill_gaps_covered?.length > 0 && (
                        <div className="trace-section">
                            <div className="trace-section-label">Skill Gaps Covered</div>
                            <div className="skills-chips">
                                {mod.skill_gaps_covered.map((s) => (
                                    <span key={s} className="skill-chip">
                                        {s}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Grounding note */}
                    <div className="trace-section">
                        <div className="trace-section-label">Grounding</div>
                        <div
                            style={{
                                fontSize: 13,
                                color: "var(--text-secondary)",
                                lineHeight: 1.7,
                                padding: "12px 14px",
                                background: "rgba(52,211,153,0.06)",
                                border: "1px solid rgba(52,211,153,0.15)",
                                borderRadius: "var(--radius-sm)",
                            }}
                        >
                            <CheckCircle size={15} strokeWidth={2.5} style={{ display: "inline-block", verticalAlign: "text-bottom", marginRight: 6 }} />
                            This module is catalog-locked. The LLM only explains a pre-indexed course;
                            it never invents module IDs or titles. Zero hallucination guarantee.
                        </div>
                    </div>

                    {/* Quick stats */}
                    <div
                        style={{
                            marginTop: 8,
                        }}
                    >
                        <div
                            style={{
                                background: "var(--bg-card)",
                                border: "1px solid var(--border)",
                                borderRadius: "var(--radius-sm)",
                                padding: "14px",
                                textAlign: "center",
                            }}
                        >
                            <div
                                style={{
                                    fontSize: 18,
                                    fontWeight: 800,
                                    color: "var(--text-primary)",
                                }}
                            >
                                {mod.phase}
                            </div>
                            <div
                                style={{
                                    fontSize: 11,
                                    color: "var(--text-muted)",
                                    marginTop: 4,
                                    textTransform: "uppercase",
                                    letterSpacing: "0.4px",
                                }}
                            >
                                Phase
                            </div>
                        </div>
                    </div>
                </div>
            </aside>
        </>
    );
}
