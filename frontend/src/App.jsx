import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import CchsCard from "./components/CchsCard";
import InsightsCard from "./components/InsightsCard";
import IndexCards from "./components/IndexCards";
import MapView from "./components/MapView";
import TrendChart from "./components/TrendChart";
import ZoneDistributionBar from "./components/ZoneDistributionBar";
import StageConfigModal from "./components/StageConfigModal";
import FieldUploadModal from "./components/FieldUploadModal";
import { api } from "./services/api";
import {
  Satellite,
  Play,
  RotateCw,
  Sparkles,
  Droplets,
  AlertTriangle,
  Flame,
  Info,
} from "lucide-react";

export default function App() {
  const [fields, setFields] = useState([]);
  const [selectedField, setSelectedField] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [growthStages, setGrowthStages] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [isScanning, setIsScanning] = useState(false);

  // Modals
  const [isStageModalOpen, setIsStageModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Initial Data Fetch
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      const [fieldList, stages] = await Promise.all([
        api.getFields(),
        api.getGrowthStages(),
      ]);

      setFields(fieldList);
      setGrowthStages(stages);

      if (fieldList.length > 0) {
        await selectField(fieldList[0]);
      }
    } catch (err) {
      console.error("Failed to load initial data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const selectField = async (field) => {
    try {
      setSelectedField(field);
      const [details, history] = await Promise.all([
        api.getFieldDetails(field.id),
        api.getFieldHistory(field.id),
      ]);

      if (details.latest_analysis) {
        setAnalysis(details.latest_analysis);
      } else {
        // Run initial scan if none exists
        const res = await api.runAnalysis({
          field_id: field.id,
          growth_stage: field.current_growth_stage || "VEGETATIVE",
        });
        setAnalysis(res);
      }
      setHistoryData(history);
    } catch (err) {
      console.error("Error selecting field:", err);
    }
  };

  // Re-run Analysis with custom weights or stage
  const handleApplyWeights = async ({ growth_stage, custom_weights }) => {
    if (!selectedField) return;
    try {
      setIsScanning(true);
      const res = await api.runAnalysis({
        field_id: selectedField.id,
        growth_stage,
        custom_weights,
      });
      setAnalysis(res);
      const history = await api.getFieldHistory(selectedField.id);
      setHistoryData(history);
    } catch (err) {
      console.error("Error applying stage weights:", err);
    } finally {
      setIsScanning(false);
    }
  };

  // Quick Demo Scenario Runner
  const handleRunScenario = async (scenarioKey) => {
    if (!selectedField) return;
    try {
      setIsScanning(true);
      const res = await api.runAnalysis({
        field_id: selectedField.id,
        growth_stage: analysis?.growth_stage || selectedField.current_growth_stage || "VEGETATIVE",
        simulate_scenario: scenarioKey,
      });
      setAnalysis(res);
      const history = await api.getFieldHistory(selectedField.id);
      setHistoryData(history);
      // Refresh field list for latest scores
      const fieldList = await api.getFields();
      setFields(fieldList);
    } catch (err) {
      console.error("Scenario simulation error:", err);
    } finally {
      setIsScanning(false);
    }
  };

  // Save Drawn Field from Map
  const handleSaveDrawnField = async (fieldPayload) => {
    try {
      setIsLoading(true);
      const created = await api.createField(fieldPayload);
      const fieldList = await api.getFields();
      setFields(fieldList);
      await selectField(created);
    } catch (err) {
      console.error("Error saving drawn field:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Export PDF Report Download
  const handleExportReport = async () => {
    if (!selectedField) return;
    try {
      setIsExporting(true);
      const downloadUrl = api.getReportDownloadUrl(selectedField.id);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.setAttribute("download", `CropVision_${selectedField.name}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error("Failed to export PDF report:", err);
    } finally {
      setTimeout(() => setIsExporting(false), 1200);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", paddingBottom: "40px" }}>
      
      {/* Top Navbar */}
      <Navbar
        fields={fields}
        selectedField={selectedField}
        onSelectField={selectField}
        onOpenStageModal={() => setIsStageModalOpen(true)}
        onOpenUploadModal={() => setIsUploadModalOpen(true)}
        onExportReport={handleExportReport}
        isExporting={isExporting}
        growthStage={analysis?.growth_stage}
      />

      {/* Main Dashboard Body */}
      <main style={{ maxWidth: "1600px", margin: "18px auto 0 auto", padding: "0 20px", width: "100%", display: "flex", flexDirection: "column", gap: "20px" }}>
        
        {/* Field Title & Interactive Demo Bar */}
        <div
          className="glass-panel"
          style={{
            padding: "14px 20px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <h2 style={{ fontSize: "1.2rem", fontWeight: "800", color: "#f8fafc" }}>
                {selectedField ? selectedField.name : "Field Overview"}
              </h2>
              <span className="badge badge-emerald" style={{ fontSize: "0.72rem" }}>
                {selectedField?.crop_type || "Crop"}
              </span>
              <span className="badge badge-cyan" style={{ fontSize: "0.72rem" }}>
                {selectedField?.location_name || "Location"}
              </span>
            </div>
            <p style={{ fontSize: "0.76rem", color: "var(--text-muted)", marginTop: "2px" }}>
              Area: <strong>{selectedField?.area_hectares || 10} ha</strong> • Growth Phase:{" "}
              <strong style={{ color: "#34d399" }}>
                {analysis?.growth_stage ? analysis.growth_stage.replace("_", " ") : "Vegetative"}
              </strong>
            </p>
          </div>

          {/* Interactive Simulation / Live Rescan Bar */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.74rem", fontWeight: "700", color: "var(--text-dim)", textTransform: "uppercase" }}>
              Interactive Demo Scenarios:
            </span>
            <button
              onClick={() => handleRunScenario("WATER_DEFICIT_NE")}
              disabled={isScanning}
              className="btn-secondary"
              style={{ fontSize: "0.74rem", padding: "5px 10px", gap: "5px", color: "#38bdf8" }}
              title="Simulate irrigation deficit & moisture drop in Northeast quadrant"
            >
              <Droplets size={13} />
              <span>Simulate Water Deficit (NE)</span>
            </button>
            <button
              onClick={() => handleRunScenario("NITROGEN_DEFICIT_S")}
              disabled={isScanning}
              className="btn-secondary"
              style={{ fontSize: "0.74rem", padding: "5px 10px", gap: "5px", color: "#fbbf24" }}
              title="Simulate nitrogen chlorosis in South parcel"
            >
              <Sparkles size={13} />
              <span>Simulate Nutrient Deficiency</span>
            </button>
            <button
              onClick={() => handleRunScenario("HIGH_VIGOR_UNIFORM")}
              disabled={isScanning}
              className="btn-secondary"
              style={{ fontSize: "0.74rem", padding: "5px 10px", gap: "5px", color: "#34d399" }}
              title="Simulate peak optimal vigor across entire field"
            >
              <Play size={13} />
              <span>Optimal Vigor</span>
            </button>
            <button
              onClick={() => handleRunScenario("HIGH_VIGOR_UNIFORM")}
              disabled={isScanning}
              className="btn-primary"
              style={{ fontSize: "0.74rem", padding: "5px 12px" }}
            >
              <RotateCw size={13} className={isScanning ? "pulse-indicator" : ""} />
              <span>{isScanning ? "Scanning..." : "Rescan Sentinel-2"}</span>
            </button>
          </div>
        </div>

        {/* Top Grid: CCHS Gauge Card + Agronomic Diagnosis Card */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: "20px" }}>
          <CchsCard
            analysis={analysis}
            onOpenStageModal={() => setIsStageModalOpen(true)}
          />
          <InsightsCard analysis={analysis} />
        </div>

        {/* Middle: 4 Multispectral Index Breakdown Cards */}
        <IndexCards analysis={analysis} />

        {/* Map & Field Health Zones Visualizer */}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <MapView
            selectedField={selectedField}
            analysis={analysis}
            onSaveDrawnField={handleSaveDrawnField}
          />
          <ZoneDistributionBar
            zoneDistribution={analysis?.zone_distribution}
            areaHectares={selectedField?.area_hectares}
          />
        </div>

        {/* Historical Multi-Scan Trend Timeline Chart */}
        <TrendChart historyData={historyData} />

      </main>

      {/* Modals */}
      <StageConfigModal
        isOpen={isStageModalOpen}
        onClose={() => setIsStageModalOpen(false)}
        growthStages={growthStages}
        currentStage={analysis?.growth_stage}
        currentWeights={analysis?.weights_used}
        onApplyWeights={handleApplyWeights}
      />

      <FieldUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onFieldCreated={async (newField) => {
          const fieldList = await api.getFields();
          setFields(fieldList);
          await selectField(newField);
        }}
      />

    </div>
  );
}
