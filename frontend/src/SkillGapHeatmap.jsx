import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Cell,
    ResponsiveContainer,
} from "recharts";
import { BarChart3 } from "lucide-react";

function gapColor(normalizedScore) {
    // Color bands on the normalized 0–1 scale
    if (normalizedScore >= 0.7) return "var(--accent-coral)";
    if (normalizedScore >= 0.4) return "var(--accent-amber)";
    return "var(--accent-teal)";
}

const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
        <div
            style={{
                background: "var(--bg-surface)",
                border: "2px solid #1a1b24",
                borderRadius: 10,
                padding: "12px 16px",
                fontSize: 13,
                boxShadow: "3px 3px 0px 0px #1a1b24",
            }}
        >
            <div style={{ fontWeight: 700, marginBottom: 6, color: "var(--text-primary)" }}>
                {d.name}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                <div style={{ color: "var(--text-secondary)" }}>
                    Relative priority:{" "}
                    <span style={{ color: gapColor(d.normalized), fontWeight: 700 }}>
                        {Math.round(d.normalized * 100)}%
                    </span>
                </div>
                <div style={{ color: "var(--text-secondary)", fontSize: 12 }}>
                    Raw gap score:{" "}
                    <span style={{ fontWeight: 600 }}>{d.rawScore.toFixed(2)}</span>
                </div>
                {d.importance && (
                    <div style={{ color: "var(--text-secondary)", fontSize: 12 }}>
                        O*NET Importance: {Math.round(d.importance * 100)}
                    </div>
                )}
            </div>
        </div>
    );
};

export default function SkillGapHeatmap({ gapVector }) {
    if (!gapVector || gapVector.length === 0) return null;

    // Sort highest gap first, take top 12
    const sorted = [...gapVector]
        .sort((a, b) => (b.gap_score ?? 0) - (a.gap_score ?? 0))
        .slice(0, 12);

    // Find the raw max for normalization — must be > 0 to avoid divide-by-zero
    const rawMax = Math.max(
        ...sorted.map((g) => g.gap_score ?? 0),
        0.001
    );

    const data = sorted.map((g) => {
        // Raw score: prefer gap_score, fall back to level delta
        const rawScore =
            g.gap_score ??
            (typeof g.required_level === "number" && typeof g.current_level === "number"
                ? Math.max(0, g.required_level - g.current_level)
                : 0.5);

        // Normalize: highest gap = 1.0, others scale proportionally
        const normalized = Math.min(1, Math.max(0, rawScore / rawMax));

        return {
            name: g.skill_name || g.onet_id || "Unknown Skill",
            normalized,   // used for bar width
            rawScore,     // shown in tooltip
            importance: g.importance,
        };
    });

    return (
        <div className="glass-card chart-card">
            <div className="chart-title">
                <BarChart3 size={28} strokeWidth={2.5} /> Skill Gap Analysis
                <span
                    style={{
                        fontSize: 11,
                        fontWeight: 500,
                        color: "var(--text-muted)",
                        marginLeft: "auto",
                    }}
                >
                    Top {data.length} gaps identified
                </span>
            </div>

            {/* Legend — thresholds now refer to relative priority */}
            <div style={{ display: "flex", gap: 16, marginBottom: 16, flexWrap: "wrap" }}>
                {[
                    { color: "var(--accent-coral)", label: "High priority (>70%)" },
                    { color: "var(--accent-amber)", label: "Medium priority (40–70%)" },
                    { color: "var(--accent-teal)", label: "Lower priority (<40%)" },
                ].map((l) => (
                    <div
                        key={l.label}
                        style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11 }}
                    >
                        <span
                            style={{
                                width: 10,
                                height: 10,
                                borderRadius: 3,
                                background: l.color,
                                display: "inline-block",
                            }}
                        />
                        <span style={{ color: "var(--text-secondary)" }}>{l.label}</span>
                    </div>
                ))}
            </div>

            <div style={{ height: 320, minWidth: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={data}
                        layout="vertical"
                        margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
                    >
                        <CartesianGrid
                            horizontal={false}
                            stroke="rgba(0,0,0,0.06)"
                        />
                        <XAxis
                            type="number"
                            domain={[0, 1]}
                            tickFormatter={(v) => `${Math.round(v * 100)}%`}
                            tick={{ fill: "var(--text-muted)", fontSize: 11 }}
                            axisLine={{ stroke: "var(--border)" }}
                            tickLine={false}
                        />
                        <YAxis
                            type="category"
                            dataKey="name"
                            width={140}
                            tick={{ fill: "var(--text-secondary)", fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(26,27,36,0.04)" }} />
                        <Bar dataKey="normalized" radius={[0, 4, 4, 0]} maxBarSize={18}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={gapColor(entry.normalized)} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
