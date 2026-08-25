import React, { useState } from "react";
import { X, Upload, PlusCircle, CheckCircle, FileCode, MapPin } from "lucide-react";
import { api } from "../services/api";

export default function FieldUploadModal({ isOpen, onClose, onFieldCreated }) {
  if (!isOpen) return null;

  const [activeTab, setActiveTab] = useState("presets"); // "presets", "upload"
  const [fieldName, setFieldName] = useState("");
  const [locationName, setLocationName] = useState("");
  const [cropType, setCropType] = useState("Corn");
  const [growthStage, setGrowthStage] = useState("VEGETATIVE");
  const [uploadedGeoJSON, setUploadedGeoJSON] = useState(null);
  const [fileName, setFileName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const presetTemplates = [
    {
      name: "Illinois Heartland Corn Field",
      location: "Champaign County, Illinois, USA",
      crop: "Corn",
      stage: "VEGETATIVE",
      geometry: {
        type: "Polygon",
        coordinates: [[
          [-88.245, 40.115],
          [-88.238, 40.115],
          [-88.238, 40.122],
          [-88.245, 40.122],
          [-88.245, 40.115],
        ]],
      },
    },
    {
      name: "Kansas Prairie Winter Wheat",
      location: "Saline County, Kansas, USA",
      crop: "Wheat",
      stage: "FLOWERING",
      geometry: {
        type: "Polygon",
        coordinates: [[
          [-97.615, 38.840],
          [-97.608, 38.840],
          [-97.608, 38.847],
          [-97.615, 38.847],
          [-97.615, 38.840],
        ]],
      },
    },
    {
      name: "Bordeaux Premier Vineyard",
      location: "Gironde, Aquitaine, France",
      crop: "Wine Grapes",
      stage: "GRAIN_FILLING",
      geometry: {
        type: "Polygon",
        coordinates: [[
          [-0.582, 44.835],
          [-0.575, 44.835],
          [-0.575, 44.842],
          [-0.582, 44.842],
          [-0.582, 44.835],
        ]],
      },
    },
    {
      name: "Texas High Plains Cotton Field",
      location: "Lubbock County, Texas, USA",
      crop: "Cotton",
      stage: "FLOWERING",
      geometry: {
        type: "Polygon",
        coordinates: [[
          [-101.885, 33.575],
          [-101.878, 33.575],
          [-101.878, 33.582],
          [-101.885, 33.582],
          [-101.885, 33.575],
        ]],
      },
    },
  ];

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setFileName(file.name);
    setErrorMsg("");

    try {
      const res = await api.uploadBoundaryFile(file);
      setUploadedGeoJSON(res.geometry);
      if (!fieldName) {
        setFieldName(file.name.replace(/\.[^/.]+$/, ""));
      }
    } catch (err) {
      setErrorMsg("Failed to parse GeoJSON file. Ensure it contains a valid Polygon geometry.");
    }
  };

  const handleSelectPreset = (preset) => {
    setFieldName(preset.name);
    setLocationName(preset.location);
    setCropType(preset.crop);
    setGrowthStage(preset.stage);
    setUploadedGeoJSON(preset.geometry);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!uploadedGeoJSON) {
      setErrorMsg("Please select a preset boundary or upload a GeoJSON file.");
      return;
    }
    if (!fieldName.trim()) {
      setErrorMsg("Please provide a field name.");
      return;
    }

    setIsSubmitting(true);
    setErrorMsg("");

    try {
      const created = await api.createField({
        name: fieldName.trim(),
        location_name: locationName.trim() || "Farm Parcel",
        crop_type: cropType,
        current_growth_stage: growthStage,
        boundary_geojson: uploadedGeoJSON,
      });

      // Run initial satellite analysis
      const analysisResult = await api.runAnalysis({
        field_id: created.id,
        growth_stage: growthStage,
        simulate_scenario: "HIGH_VIGOR_UNIFORM",
      });

      onFieldCreated(created);
      onClose();
    } catch (err) {
      setErrorMsg("Failed to create field: " + (err.response?.data?.detail || err.message));
    } finally {
      setIsSubmitting(false);
    }
  };

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
          maxWidth: "600px",
          background: "rgba(11, 22, 24, 0.96)",
          padding: "24px",
          display: "flex",
          flexDirection: "column",
          gap: "18px",
          maxHeight: "90vh",
          overflowY: "auto",
        }}
      >
        {/* Header */}
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
              <PlusCircle size={18} color="#34d399" />
            </div>
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: "700", color: "#f8fafc" }}>
                Add Monitored Field Boundary
              </h3>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                Upload GeoJSON file or choose an agricultural parcel template
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

        {/* Tab Switcher */}
        <div style={{ display: "flex", borderBottom: "1px solid var(--border-subtle)", gap: "8px" }}>
          <button
            onClick={() => setActiveTab("presets")}
            style={{
              background: "none",
              border: "none",
              borderBottom: activeTab === "presets" ? "2px solid #10b981" : "2px solid transparent",
              color: activeTab === "presets" ? "#34d399" : "var(--text-muted)",
              padding: "8px 14px",
              fontSize: "0.82rem",
              fontWeight: activeTab === "presets" ? "700" : "500",
              cursor: "pointer",
            }}
          >
            Agricultural Presets
          </button>
          <button
            onClick={() => setActiveTab("upload")}
            style={{
              background: "none",
              border: "none",
              borderBottom: activeTab === "upload" ? "2px solid #10b981" : "2px solid transparent",
              color: activeTab === "upload" ? "#34d399" : "var(--text-muted)",
              padding: "8px 14px",
              fontSize: "0.82rem",
              fontWeight: activeTab === "upload" ? "700" : "500",
              cursor: "pointer",
            }}
          >
            Upload GeoJSON File
          </button>
        </div>

        {errorMsg && (
          <div
            style={{
              background: "rgba(239, 68, 68, 0.1)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              borderRadius: "8px",
              padding: "10px",
              color: "#f87171",
              fontSize: "0.8rem",
            }}
          >
            {errorMsg}
          </div>
        )}

        {/* Preset Selector */}
        {activeTab === "presets" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            {presetTemplates.map((p, idx) => (
              <div
                key={idx}
                onClick={() => handleSelectPreset(p)}
                style={{
                  background: fieldName === p.name ? "rgba(16, 185, 129, 0.15)" : "rgba(255, 255, 255, 0.03)",
                  border: fieldName === p.name ? "1px solid #10b981" : "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "12px",
                  cursor: "pointer",
                  display: "flex",
                  flexDirection: "column",
                  gap: "4px",
                  transition: "all 0.15s ease",
                }}
              >
                <span style={{ fontSize: "0.85rem", fontWeight: "700", color: "#f8fafc" }}>
                  {p.name}
                </span>
                <span style={{ fontSize: "0.74rem", color: "var(--text-dim)" }}>
                  {p.location}
                </span>
                <div style={{ display: "flex", gap: "6px", marginTop: "4px" }}>
                  <span className="badge badge-emerald" style={{ fontSize: "0.68rem", padding: "1px 6px" }}>
                    {p.crop}
                  </span>
                  <span className="badge badge-cyan" style={{ fontSize: "0.68rem", padding: "1px 6px" }}>
                    {p.stage}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* File Upload Box */}
        {activeTab === "upload" && (
          <div
            style={{
              border: "2px dashed var(--border-highlight)",
              borderRadius: "12px",
              padding: "24px",
              textAlign: "center",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "10px",
              background: "rgba(0, 0, 0, 0.2)",
            }}
          >
            <FileCode size={36} color="#34d399" />
            <div>
              <p style={{ fontSize: "0.85rem", fontWeight: "600", color: "#f8fafc" }}>
                {fileName ? `Selected: ${fileName}` : "Select a GeoJSON or JSON Boundary File"}
              </p>
              <p style={{ fontSize: "0.74rem", color: "var(--text-dim)" }}>
                Supports standard WGS84 Polygon or MultiPolygon GeoJSON
              </p>
            </div>
            <label className="btn-secondary" style={{ fontSize: "0.8rem", cursor: "pointer" }}>
              <Upload size={14} />
              <span>Browse File</span>
              <input
                type="file"
                accept=".geojson,.json"
                onChange={handleFileUpload}
                style={{ display: "none" }}
              />
            </label>
          </div>
        )}

        {/* Form Fields */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div>
            <label style={{ fontSize: "0.78rem", fontWeight: "600", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Field Name:
            </label>
            <input
              type="text"
              required
              value={fieldName}
              onChange={(e) => setFieldName(e.target.value)}
              placeholder="e.g. North Acre Plot #4"
              style={{ width: "100%" }}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            <div>
              <label style={{ fontSize: "0.78rem", fontWeight: "600", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                Crop Type:
              </label>
              <select
                value={cropType}
                onChange={(e) => setCropType(e.target.value)}
                style={{ width: "100%" }}
              >
                <option value="Corn">Corn (Maize)</option>
                <option value="Wheat">Wheat</option>
                <option value="Soybean">Soybean</option>
                <option value="Cotton">Cotton</option>
                <option value="Wine Grapes">Wine Grapes</option>
                <option value="Rice">Rice</option>
                <option value="Sunflower">Sunflower</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: "0.78rem", fontWeight: "600", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                Current Growth Stage:
              </label>
              <select
                value={growthStage}
                onChange={(e) => setGrowthStage(e.target.value)}
                style={{ width: "100%" }}
              >
                <option value="EMERGENCE">Emergence / Early Veg</option>
                <option value="VEGETATIVE">Rapid Vegetative</option>
                <option value="FLOWERING">Flowering / Heading</option>
                <option value="GRAIN_FILLING">Grain Filling / Pods</option>
                <option value="PRE_HARVEST">Pre-Harvest / Maturation</option>
              </select>
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
            <button type="button" onClick={onClose} className="btn-secondary" style={{ fontSize: "0.82rem" }}>
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary"
              style={{ fontSize: "0.82rem" }}
            >
              {isSubmitting ? "Running Sentinel-2 Scan..." : "Register Field & Analyze"}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}
