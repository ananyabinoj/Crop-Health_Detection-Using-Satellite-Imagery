import React, { useState, useEffect } from "react";
import { X, Sliders, Check, Info, Sparkles, RefreshCw } from "lucide-react";

export default function StageConfigModal({
  isOpen,
  onClose,
  growthStages,
  currentStage,
  currentWeights,
  onApplyWeights,
}) {
  if (!isOpen) return null;

  const [selectedStage, setSelectedStage] = useState(currentStage || "VEGETATIVE");
  const [weights, setWeights] = useState({
    ndvi: currentWeights?.ndvi ?? 0.35,
    evi: currentWeights?.evi ?? 0.25,
    gci: currentWeights?.gci ?? 0.25,
    ndwi: currentWeights?.ndwi ?? 0.15,
  });

  // When stage changes, load preset defaults
  const handleStageSelect = (stageKey) => {
    setSelectedStage(stageKey);
    const preset = growthStages.find((s) => s.stage_key === stageKey);
    if (preset && preset.weights) {
      setWeights({
        ndvi: preset.weights.ndvi,
        evi: preset.weights.evi,
        gci: preset.weights.gci,
        ndwi: preset.weights.ndwi,
      });
    }
  };

  const handleSliderChange = (key, rawVal) => {
    const val = parseFloat(rawVal);
    setWeights((prev) => ({
      ...prev,
      [key]: val,
    }));
  };

  const totalWeight = weights.ndvi + weights.evi + weights.gci + weights.ndwi;

  const handleSaveAndApply = () => {
    // Normalize to sum 1.0
    const normFactor = totalWeight > 0 ? totalWeight : 1.0;
    const normalized = {
      ndvi: Number((weights.ndvi / normFactor).toFixed(3)),
      evi: Number((weights.evi / normFactor).toFixed(3)),
      gci: Number((weights.gci / normFactor).toFixed(3)),
      ndwi: Number((weights.ndwi / normFactor).toFixed(3)),
    };

    onApplyWeights({
      growth_stage: selectedStage,
      custom_weights: normalized,
    });
    onClose();
  };

  const activePreset = growthStages.find((s) => s.stage_key === selectedStage);

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 2000,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: "100%",
          maxWidth: "580px",
          background: "rgba(11, 22, 24, 0.96)",
          padding: "24px",
          display: "flex",
          flexDirection: "column",
          gap: "18px",
          maxHeight: "90vh",
          overflowY: "auto",
        }}
      >
        {/* Modal Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "34px",
                height: "34px",
                borderRadius: "8px",
                backgroundColor: "rgba(16, 185, 129, 0.15)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Sliders size={18} color="#34d399" />
            </div>
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: "700", color: "#f8fafc" }}>
                Growth-Stage CCHS Calibration
              </h3>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                Dynamically adjust index weights based on crop phenology
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer",
              padding: "4px",
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Stage Selector Pills */}
        <div>
          <label style={{ fontSize: "0.78rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: "8px" }}>
            Select Phenological Growth Stage
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: "8px" }}>
            {[
              { key: "EMERGENCE", label: "Emergence" },
              { key: "VEGETATIVE", label: "Vegetative" },
              { key: "FLOWERING", label: "Flowering" },
              { key: "GRAIN_FILLING", label: "Grain Fill" },
              { key: "PRE_HARVEST", label: "Pre-Harvest" },
            ].map((st) => (
              <button
                key={st.key}
                onClick={() => handleStageSelect(st.key)}
                style={{
                  background: selectedStage === st.key ? "rgba(16, 185, 129, 0.25)" : "rgba(255, 255, 255, 0.04)",
                  color: selectedStage === st.key ? "#34d399" : "#94a3b8",
                  border: selectedStage === st.key ? "1px solid #10b981" : "1px solid var(--border-subtle)",
                  borderRadius: "8px",
                  padding: "8px 6px",
                  fontSize: "0.76rem",
                  fontWeight: selectedStage === st.key ? "700" : "500",
                  cursor: "pointer",
                  textAlign: "center",
                }}
              >
                {st.label}
              </button>
            ))}
          </div>
        </div>

        {/* Agronomic Rationale Note */}
        {activePreset && (
          <div
            style={{
              background: "rgba(16, 185, 129, 0.06)",
              border: "1px solid rgba(16, 185, 129, 0.2)",
              borderRadius: "8px",
              padding: "10px 14px",
              display: "flex",
              alignItems: "flex-start",
              gap: "8px",
              fontSize: "0.78rem",
              color: "#cbd5e1",
              lineHeight: "1.4",
            }}
          >
            <Info size={16} color="#34d399" style={{ flexShrink: 0, marginTop: "2px" }} />
            <div>
              <strong style={{ color: "#34d399" }}>Agronomic Rationale: </strong>
              {activePreset.description || "Calibrated weighting formula for this phenological stage."}
            </div>
          </div>
        )}

        {/* Interactive Weight Sliders */}
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <label style={{ fontSize: "0.78rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
            Fine-Tune Index Weight Contribution
          </label>

          {[
            { key: "ndvi", label: "NDVI (Green Biomass)", color: "#10b981", val: weights.ndvi },
            { key: "ndwi", label: "NDWI (Canopy Water Content)", color: "#06b6d4", val: weights.ndwi },
            { key: "gci", label: "GCI (Chlorophyll & Nitrogen)", color: "#22c55e", val: weights.gci },
            { key: "evi", label: "EVI (Canopy Structure)", color: "#84cc16", val: weights.evi },
          ].map((slider) => {
            const pct = totalWeight > 0 ? ((slider.val / totalWeight) * 100).toFixed(0) : 25;
            return (
              <div key={slider.key} style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
                  <span style={{ color: "#f8fafc", fontWeight: "600" }}>{slider.label}</span>
                  <span style={{ color: slider.color, fontWeight: "700" }}>{pct}%</span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.80"
                  step="0.05"
                  value={slider.val}
                  onChange={(e) => handleSliderChange(slider.key, e.target.value)}
                  style={{
                    width: "100%",
                    accentColor: slider.color,
                    cursor: "pointer",
                  }}
                />
              </div>
            );
          })}
        </div>

        {/* Action Buttons */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "10px", marginTop: "8px" }}>
          <button onClick={onClose} className="btn-secondary" style={{ fontSize: "0.82rem" }}>
            Cancel
          </button>
          <button onClick={handleSaveAndApply} className="btn-primary" style={{ fontSize: "0.82rem" }}>
            <RefreshCw size={15} />
            <span>Apply & Recalculate CCHS</span>
          </button>
        </div>

      </div>
    </div>
  );
}
