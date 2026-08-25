import React from "react";
import { PieChart, CheckCircle, AlertTriangle, XCircle } from "lucide-react";

export default function ZoneDistributionBar({ zoneDistribution, areaHectares }) {
  if (!zoneDistribution) return null;

  const { healthy_pct = 70, moderate_pct = 20, stressed_pct = 10, total_cells = 100 } =
    zoneDistribution;
  const area = areaHectares || 10.0;

  const healthyHa = ((healthy_pct / 100) * area).toFixed(1);
  const moderateHa = ((moderate_pct / 100) * area).toFixed(1);
  const stressedHa = ((stressed_pct / 100) * area).toFixed(1);

  return (
    <div
      className="glass-panel"
      style={{
        padding: "16px 20px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <PieChart size={16} color="#34d399" />
          <span style={{ fontSize: "0.85rem", fontWeight: "700", color: "#f8fafc" }}>
            Field Health Zone Segmentation
          </span>
        </div>
        <span style={{ fontSize: "0.74rem", color: "var(--text-dim)" }}>
          Total Area: <strong style={{ color: "#e2e8f0" }}>{area} ha</strong> (~{total_cells} 10m grid cells)
        </span>
      </div>

      {/* Segmented Distribution Bar */}
      <div
        style={{
          width: "100%",
          height: "14px",
          borderRadius: "7px",
          background: "rgba(255, 255, 255, 0.05)",
          display: "flex",
          overflow: "hidden",
          border: "1px solid var(--border-subtle)",
        }}
      >
        <div
          style={{
            width: `${healthy_pct}%`,
            height: "100%",
            background: "linear-gradient(90deg, #059669, #10b981)",
            transition: "width 0.8s ease",
          }}
          title={`Healthy: ${healthy_pct}%`}
        />
        <div
          style={{
            width: `${moderate_pct}%`,
            height: "100%",
            background: "linear-gradient(90deg, #d97706, #f59e0b)",
            transition: "width 0.8s ease",
          }}
          title={`Moderate: ${moderate_pct}%`}
        />
        <div
          style={{
            width: `${stressed_pct}%`,
            height: "100%",
            background: "linear-gradient(90deg, #dc2626, #ef4444)",
            transition: "width 0.8s ease",
          }}
          title={`Stressed: ${stressed_pct}%`}
        />
      </div>

      {/* Stats Breakdown Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", fontSize: "0.76rem" }}>
        {/* Healthy */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#34d399" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981" }} />
          <div>
            <strong>{healthy_pct}% Healthy</strong>
            <span style={{ color: "var(--text-dim)", display: "block", fontSize: "0.7rem" }}>
              {healthyHa} ha
            </span>
          </div>
        </div>

        {/* Moderate */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#fbbf24" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#f59e0b" }} />
          <div>
            <strong>{moderate_pct}% Moderate</strong>
            <span style={{ color: "var(--text-dim)", display: "block", fontSize: "0.7rem" }}>
              {moderateHa} ha
            </span>
          </div>
        </div>

        {/* Stressed */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#f87171" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#ef4444" }} />
          <div>
            <strong>{stressed_pct}% Stressed</strong>
            <span style={{ color: "var(--text-dim)", display: "block", fontSize: "0.7rem" }}>
              {stressedHa} ha
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
