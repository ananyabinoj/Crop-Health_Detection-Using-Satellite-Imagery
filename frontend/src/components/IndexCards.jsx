import React from "react";
import { HelpCircle, Droplets, Leaf, Activity, Layers } from "lucide-react";

export default function IndexCards({ analysis }) {
  if (!analysis) return null;

  const raw = analysis.raw_indices || {};
  const sub = analysis.sub_scores || {};
  const weights = analysis.weights_used || {};

  const indices = [
    {
      key: "ndvi",
      name: "NDVI",
      title: "Normalized Difference Vegetation Index",
      target: "Canopy Density & Green Biomass",
      formula: "(B8 - B4) / (B8 + B4)",
      bands: "NIR (842nm) vs Red (665nm)",
      rawVal: raw.ndvi ?? 0,
      subScore: sub.ndvi_score ?? 0,
      weight: weights.ndvi ?? 0.25,
      color: "#10b981",
      icon: Leaf,
      description: "Measures chlorophyll red absorption vs cell-wall NIR reflection for photosynthetic biomass.",
    },
    {
      key: "ndwi",
      name: "NDWI",
      title: "Normalized Difference Water Index",
      target: "Canopy Moisture & Water Stress",
      formula: "(B8 - B11) / (B8 + B11)",
      bands: "NIR (842nm) vs SWIR (1610nm)",
      rawVal: raw.ndwi ?? 0,
      subScore: sub.ndwi_score ?? 0,
      weight: weights.ndwi ?? 0.25,
      color: "#06b6d4",
      icon: Droplets,
      description: "Directly measures liquid water content in spongy mesophyll cells; detects drought/irrigation deficits.",
    },
    {
      key: "gci",
      name: "GCI",
      title: "Green Chlorophyll Index",
      target: "Nitrogen & Chlorophyll Concentration",
      formula: "(B8 / B3) - 1.0",
      bands: "NIR (842nm) / Green (560nm)",
      rawVal: raw.gci ?? 0,
      subScore: sub.gci_score ?? 0,
      weight: weights.gci ?? 0.25,
      color: "#22c55e",
      icon: Activity,
      description: "Highly sensitive to nitrogen uptake and leaf chlorosis well before visual yellowing occurs.",
    },
    {
      key: "evi",
      name: "EVI",
      title: "Enhanced Vegetation Index",
      target: "Canopy Structure & Soil Decoupling",
      formula: "2.5 * (B8 - B4) / (B8 + 6*B4 - 7.5*B2 + 1)",
      bands: "NIR, Red, and Blue (490nm)",
      rawVal: raw.evi ?? 0,
      subScore: sub.evi_score ?? 0,
      weight: weights.evi ?? 0.25,
      color: "#84cc16",
      icon: Layers,
      description: "Decouples background soil noise and atmospheric aerosols; sensitive in high-biomass canopies.",
    },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
      {indices.map((idx) => {
        const IconComponent = idx.icon;
        return (
          <div
            key={idx.key}
            className="glass-panel"
            style={{
              padding: "18px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              position: "relative",
              overflow: "hidden",
            }}
          >
            {/* Ambient Corner Glow */}
            <div
              style={{
                position: "absolute",
                top: "-20px",
                right: "-20px",
                width: "80px",
                height: "80px",
                borderRadius: "50%",
                background: idx.color,
                filter: "blur(35px)",
                opacity: 0.15,
                pointerEvents: "none",
              }}
            />

            {/* Title & Icon Header */}
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "6px",
                    backgroundColor: `${idx.color}22`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <IconComponent size={16} color={idx.color} />
                </div>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <span style={{ fontSize: "1.05rem", fontWeight: "800", color: "#f8fafc" }}>
                      {idx.name}
                    </span>
                    <span
                      style={{
                        fontSize: "0.68rem",
                        padding: "1px 6px",
                        borderRadius: "4px",
                        backgroundColor: "rgba(255, 255, 255, 0.08)",
                        color: "var(--text-muted)",
                        fontWeight: "600",
                      }}
                    >
                      Weight: {(idx.weight * 100).toFixed(0)}%
                    </span>
                  </div>
                  <span style={{ fontSize: "0.72rem", color: "var(--text-dim)", display: "block" }}>
                    {idx.target}
                  </span>
                </div>
              </div>
            </div>

            {/* Values: Raw & Sub-Score */}
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", margin: "4px 0" }}>
              <div>
                <span style={{ fontSize: "0.72rem", color: "var(--text-dim)", display: "block" }}>
                  Raw Sentinel-2
                </span>
                <span className="mono-code" style={{ fontSize: "1.3rem", fontWeight: "700", color: "#f8fafc" }}>
                  {typeof idx.rawVal === "number" ? idx.rawVal.toFixed(3) : idx.rawVal}
                </span>
              </div>
              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--text-dim)", display: "block" }}>
                  Normalized Sub-Score
                </span>
                <span style={{ fontSize: "1.1rem", fontWeight: "700", color: idx.color }}>
                  {typeof idx.subScore === "number" ? idx.subScore.toFixed(1) : idx.subScore}{" "}
                  <span style={{ fontSize: "0.72rem", color: "var(--text-dim)" }}>/100</span>
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            <div style={{ width: "100%", height: "6px", background: "rgba(255, 255, 255, 0.06)", borderRadius: "3px", overflow: "hidden" }}>
              <div
                style={{
                  width: `${Math.min(100, Math.max(0, idx.subScore))}%`,
                  height: "100%",
                  background: idx.color,
                  borderRadius: "3px",
                  transition: "width 0.8s ease",
                }}
              />
            </div>

            {/* Formula & Band Reference Footnote */}
            <div
              style={{
                fontSize: "0.7rem",
                color: "var(--text-muted)",
                background: "rgba(0, 0, 0, 0.2)",
                padding: "6px 8px",
                borderRadius: "6px",
                lineHeight: "1.3",
              }}
            >
              <div className="mono-code" style={{ color: "#94a3b8", marginBottom: "2px" }}>
                Formula: {idx.formula}
              </div>
              <div style={{ color: "var(--text-dim)", fontSize: "0.68rem" }}>
                {idx.description}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
