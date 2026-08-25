import React from "react";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  Info,
  Calendar,
  Layers,
  Sparkles,
} from "lucide-react";

export default function CchsCard({ analysis, onOpenStageModal }) {
  if (!analysis) {
    return (
      <div className="glass-panel" style={{ padding: "24px", minHeight: "280px", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No analysis data available.</p>
      </div>
    );
  }

  const score = analysis.cchs_score || 0;
  const classification = analysis.classification || {};
  const trend = analysis.trend || {};
  const subScores = analysis.sub_scores || {};
  const weights = analysis.weights_used || {};
  const stage = (analysis.growth_stage || "VEGETATIVE").replace("_", " ");

  // Circular gauge calculations
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, score));
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  // Score color
  const scoreColor =
    score >= 80 ? "#10b981" : score >= 65 ? "#22c55e" : score >= 50 ? "#f59e0b" : score >= 35 ? "#f97316" : "#ef4444";

  return (
    <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Top Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              background: "rgba(16, 185, 129, 0.15)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Activity size={18} color="#34d399" />
          </div>
          <div>
            <h2 style={{ fontSize: "1.05rem", fontWeight: "700", color: "#f8fafc" }}>
              Composite Crop Health Score
            </h2>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Multi-index weighted biophysical evaluation (0–100)
            </p>
          </div>
        </div>

        {/* Scan Date */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.78rem", color: "var(--text-dim)" }}>
          <Calendar size={14} />
          <span>{analysis.scan_date || "Today"}</span>
        </div>
      </div>

      {/* Main Score & Gauge Display */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "20px" }}>
        
        {/* Circular Gauge */}
        <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
          <div style={{ position: "relative", width: "130px", height: "130px" }}>
            <svg width="130" height="130" style={{ transform: "rotate(-90deg)" }}>
              {/* Background Track */}
              <circle
                cx="65"
                cy="65"
                r={radius}
                stroke="rgba(255, 255, 255, 0.08)"
                strokeWidth="10"
                fill="transparent"
              />
              {/* Progress Bar */}
              <circle
                cx="65"
                cy="65"
                r={radius}
                stroke={scoreColor}
                strokeWidth="10"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
                style={{ transition: "stroke-dashoffset 1s ease-in-out" }}
              />
            </svg>
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                textAlign: "center",
              }}
            >
              <span className="metric-value" style={{ fontSize: "2.1rem", color: "#f8fafc", lineHeight: "1" }}>
                {score}
              </span>
              <span style={{ fontSize: "0.75rem", color: "var(--text-dim)", display: "block", marginTop: "2px" }}>
                / 100
              </span>
            </div>
          </div>

          {/* Classification & Status */}
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <div
              className="badge"
              style={{
                backgroundColor: `${scoreColor}22`,
                color: scoreColor,
                border: `1px solid ${scoreColor}55`,
                fontSize: "0.85rem",
                padding: "6px 14px",
                alignSelf: "flex-start",
              }}
            >
              <Sparkles size={14} />
              <span>{classification.label || "Normal Vigor"}</span>
            </div>
            
            {/* Historical Baseline Comparison Badge */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 12px",
                borderRadius: "8px",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              {trend.is_declining ? (
                <TrendingDown size={18} color="#f87171" />
              ) : trend.delta_vs_baseline > 3 ? (
                <TrendingUp size={18} color="#34d399" />
              ) : (
                <Minus size={18} color="#60a5fa" />
              )}
              <div>
                <div style={{ fontSize: "0.82rem", fontWeight: "700", color: trend.trend_color || "#38bdf8" }}>
                  {trend.trend_label || "Baseline Established"}
                </div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                  {trend.delta_vs_baseline !== undefined
                    ? `${trend.delta_vs_baseline >= 0 ? "+" : ""}${trend.delta_vs_baseline} pts vs 4-scan baseline (${trend.rolling_baseline_score || score})`
                    : "No baseline history yet"}
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* Growth Stage Weight Profile Summary */}
        <div
          style={{
            flex: "1 1 240px",
            background: "rgba(0, 0, 0, 0.25)",
            padding: "14px 16px",
            borderRadius: "10px",
            border: "1px solid var(--border-subtle)",
            display: "flex",
            flexDirection: "column",
            gap: "10px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
              Stage Weighting Profile
            </span>
            <button
              onClick={onOpenStageModal}
              style={{
                background: "none",
                border: "none",
                color: "#34d399",
                fontSize: "0.72rem",
                cursor: "pointer",
                fontWeight: "600",
                textDecoration: "underline",
              }}
            >
              Tune Weights
            </button>
          </div>

          <p style={{ fontSize: "0.78rem", color: "#cbd5e1", lineHeight: "1.35" }}>
            Active Stage: <strong style={{ color: "#34d399" }}>{stage}</strong>. Index weights calibrated for current crop phenology:
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "0.75rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-dim)" }}>
              <span>NDVI (Vigor):</span>
              <strong style={{ color: "#e2e8f0" }}>{((weights.ndvi || 0.25) * 100).toFixed(0)}%</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-dim)" }}>
              <span>NDWI (Water):</span>
              <strong style={{ color: (weights.ndwi || 0.25) >= 0.3 ? "#38bdf8" : "#e2e8f0" }}>
                {((weights.ndwi || 0.25) * 100).toFixed(0)}%
              </strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-dim)" }}>
              <span>GCI (Chlorophyll):</span>
              <strong style={{ color: (weights.gci || 0.25) >= 0.3 ? "#a7f3d0" : "#e2e8f0" }}>
                {((weights.gci || 0.25) * 100).toFixed(0)}%
              </strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-dim)" }}>
              <span>EVI (Structure):</span>
              <strong style={{ color: "#e2e8f0" }}>{((weights.evi || 0.25) * 100).toFixed(0)}%</strong>
            </div>
          </div>
        </div>

      </div>

      {/* Sub-Score Progress Bars */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "10px", marginTop: "4px" }}>
        {[
          { label: "NDVI Score", val: subScores.ndvi_score || 0, color: "#10b981" },
          { label: "NDWI (Water)", val: subScores.ndwi_score || 0, color: "#06b6d4" },
          { label: "GCI (Nitrogen)", val: subScores.gci_score || 0, color: "#22c55e" },
          { label: "EVI (Canopy)", val: subScores.evi_score || 0, color: "#84cc16" },
        ].map((sub, idx) => (
          <div
            key={idx}
            style={{
              background: "rgba(255, 255, 255, 0.02)",
              padding: "8px 12px",
              borderRadius: "8px",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "4px" }}>
              <span>{sub.label}</span>
              <span style={{ fontWeight: "700", color: "#f8fafc" }}>{sub.val.toFixed(1)}</span>
            </div>
            <div style={{ width: "100%", height: "5px", background: "rgba(255, 255, 255, 0.08)", borderRadius: "3px", overflow: "hidden" }}>
              <div
                style={{
                  width: `${Math.min(100, Math.max(0, sub.val))}%`,
                  height: "100%",
                  background: sub.color,
                  borderRadius: "3px",
                  transition: "width 0.8s ease",
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
