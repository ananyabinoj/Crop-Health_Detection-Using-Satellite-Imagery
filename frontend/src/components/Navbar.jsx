import React from "react";
import {
  Sprout,
  Satellite,
  Layers,
  FileDown,
  PlusCircle,
  Sliders,
  Sparkles,
  ChevronDown,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

export default function Navbar({
  fields,
  selectedField,
  onSelectField,
  onOpenStageModal,
  onOpenUploadModal,
  onExportReport,
  isExporting,
  growthStage,
}) {
  return (
    <header className="glass-panel" style={{ margin: "16px 20px 0 20px", padding: "12px 20px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
        
        {/* Brand & Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #10b981 0%, #065f46 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 20px rgba(16, 185, 129, 0.4)",
            }}
          >
            <Sprout size={24} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <h1 style={{ fontSize: "1.25rem", fontWeight: "800", letterSpacing: "-0.02em", color: "#f8fafc" }}>
                CropVision
              </h1>
              <span className="badge badge-emerald" style={{ fontSize: "0.68rem", padding: "2px 8px" }}>
                MVP
              </span>
            </div>
            <p style={{ fontSize: "0.75rem", color: "var(--text-dim)", fontWeight: "500" }}>
              Satellite Multispectral Health Monitoring
            </p>
          </div>
        </div>

        {/* Center: Field Selector & Stage Pill */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
          {/* Field Dropdown */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: "600" }}>
              Monitored Field:
            </span>
            <div style={{ position: "relative", minWidth: "260px" }}>
              <select
                value={selectedField ? selectedField.id : ""}
                onChange={(e) => {
                  const fId = parseInt(e.target.value);
                  const f = fields.find((item) => item.id === fId);
                  if (f) onSelectField(f);
                }}
                style={{
                  width: "100%",
                  cursor: "pointer",
                  padding: "8px 32px 8px 12px",
                  fontSize: "0.85rem",
                  fontWeight: "600",
                  backgroundColor: "rgba(16, 32, 34, 0.9)",
                  border: "1px solid var(--border-highlight)",
                  borderRadius: "8px",
                  color: "#f1f5f9",
                  appearance: "none",
                }}
              >
                {fields.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name} ({f.crop_type} - {f.latest_cchs ? `${f.latest_cchs} pts` : "No scans"})
                  </option>
                ))}
              </select>
              <ChevronDown
                size={16}
                color="#10b981"
                style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}
              />
            </div>
          </div>

          {/* Growth Stage Configure Button */}
          <button
            onClick={onOpenStageModal}
            className="btn-secondary"
            style={{ fontSize: "0.8rem", padding: "7px 12px", gap: "6px" }}
            title="Configure growth stage & index weighting profile"
          >
            <Sliders size={15} color="#34d399" />
            <span>Stage: <strong>{growthStage ? growthStage.replace("_", " ") : "Vegetative"}</strong></span>
          </button>
        </div>

        {/* Right Action Buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {/* Satellite Status Badge */}
          <div
            className="badge badge-emerald"
            style={{ padding: "6px 12px", fontSize: "0.75rem", background: "rgba(16, 185, 129, 0.1)" }}
          >
            <Satellite size={14} className="pulse-indicator" color="#10b981" />
            <span>Sentinel-2 L2A (10m)</span>
          </div>

          {/* Add Field Button */}
          <button onClick={onOpenUploadModal} className="btn-secondary" style={{ fontSize: "0.82rem" }}>
            <PlusCircle size={16} color="#34d399" />
            <span>New Boundary</span>
          </button>

          {/* Export PDF */}
          <button
            onClick={onExportReport}
            disabled={isExporting}
            className="btn-primary"
            style={{ fontSize: "0.82rem" }}
          >
            <FileDown size={16} />
            <span>{isExporting ? "Generating PDF..." : "Export Report"}</span>
          </button>
        </div>

      </div>
    </header>
  );
}
