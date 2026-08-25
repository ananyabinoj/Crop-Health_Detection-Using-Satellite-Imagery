import React, { useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Area,
} from "recharts";
import { History, TrendingDown, TrendingUp, AlertTriangle } from "lucide-react";

export default function TrendChart({ historyData }) {
  const [showNdvi, setShowNdvi] = useState(true);
  const [showNdwi, setShowNdwi] = useState(true);
  const [showGci, setShowGci] = useState(false);
  const [showEvi, setShowEvi] = useState(false);

  if (!historyData || !historyData.timeline || historyData.timeline.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: "24px" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No historical scans recorded yet.</p>
      </div>
    );
  }

  // Format data for Recharts
  const chartData = historyData.timeline.map((item) => ({
    date: item.date,
    cchs: item.cchs_score,
    ndvi_score: item.sub_scores?.ndvi_score || 0,
    ndwi_score: item.sub_scores?.ndwi_score || 0,
    gci_score: item.sub_scores?.gci_score || 0,
    evi_score: item.sub_scores?.evi_score || 0,
    growth_stage: (item.growth_stage || "").replace("_", " "),
    status: item.status,
    raw_ndvi: item.raw_indices?.ndvi,
    raw_ndwi: item.raw_indices?.ndwi,
  }));

  // Average baseline score
  const avgBaseline =
    chartData.length > 0
      ? (chartData.reduce((acc, d) => acc + d.cchs, 0) / chartData.length).toFixed(1)
      : 0;

  return (
    <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
      
      {/* Header & Controls */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
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
            <History size={18} color="#34d399" />
          </div>
          <div>
            <h2 style={{ fontSize: "1.05rem", fontWeight: "700", color: "#f8fafc" }}>
              Historical Health Trajectory & Baseline
            </h2>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Multi-scan temporal tracking vs rolling baseline ({chartData.length} observations)
            </p>
          </div>
        </div>

        {/* Index Toggle Checkboxes */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap", fontSize: "0.76rem" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "4px", cursor: "pointer", color: "#10b981" }}>
            <input
              type="checkbox"
              checked={showNdvi}
              onChange={(e) => setShowNdvi(e.target.checked)}
              style={{ accentColor: "#10b981" }}
            />
            <span>NDVI</span>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: "4px", cursor: "pointer", color: "#06b6d4" }}>
            <input
              type="checkbox"
              checked={showNdwi}
              onChange={(e) => setShowNdwi(e.target.checked)}
              style={{ accentColor: "#06b6d4" }}
            />
            <span>NDWI (Water)</span>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: "4px", cursor: "pointer", color: "#22c55e" }}>
            <input
              type="checkbox"
              checked={showGci}
              onChange={(e) => setShowGci(e.target.checked)}
              style={{ accentColor: "#22c55e" }}
            />
            <span>GCI</span>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: "4px", cursor: "pointer", color: "#84cc16" }}>
            <input
              type="checkbox"
              checked={showEvi}
              onChange={(e) => setShowEvi(e.target.checked)}
              style={{ accentColor: "#84cc16" }}
            />
            <span>EVI</span>
          </label>
        </div>
      </div>

      {/* Chart Canvas */}
      <div style={{ width: "100%", height: "260px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.06)" />
            <XAxis
              dataKey="date"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
            />
            <YAxis
              domain={[20, 100]}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(12, 24, 28, 0.95)",
                borderColor: "rgba(16, 185, 129, 0.4)",
                borderRadius: "10px",
                boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
                fontSize: "0.8rem",
                color: "#f8fafc",
              }}
              formatter={(val, name) => {
                const labels = {
                  cchs: "CCHS Composite Score",
                  ndvi_score: "NDVI Sub-Score",
                  ndwi_score: "NDWI (Water) Sub-Score",
                  gci_score: "GCI (Nitrogen) Sub-Score",
                  evi_score: "EVI Sub-Score",
                };
                return [`${val} / 100`, labels[name] || name];
              }}
              labelFormatter={(label, payload) => {
                const stage = payload && payload[0]?.payload?.growth_stage;
                return `Date: ${label} (${stage || "Observation"})`;
              }}
            />

            {/* Baseline Reference */}
            <ReferenceLine
              y={Number(avgBaseline)}
              stroke="#64748b"
              strokeDasharray="4 4"
              label={{
                value: `Baseline Mean (${avgBaseline})`,
                fill: "#94a3b8",
                fontSize: 10,
                position: "insideTopRight",
              }}
            />

            {/* Main CCHS Score Line */}
            <Line
              type="monotone"
              dataKey="cchs"
              name="cchs"
              stroke="#10b981"
              strokeWidth={3.5}
              dot={{ fill: "#10b981", r: 5, stroke: "#064e3b", strokeWidth: 2 }}
              activeDot={{ r: 7, fill: "#34d399" }}
            />

            {/* Optional Component Index Lines */}
            {showNdvi && (
              <Line
                type="monotone"
                dataKey="ndvi_score"
                name="ndvi_score"
                stroke="#059669"
                strokeWidth={1.8}
                strokeDasharray="2 2"
                dot={false}
              />
            )}
            {showNdwi && (
              <Line
                type="monotone"
                dataKey="ndwi_score"
                name="ndwi_score"
                stroke="#06b6d4"
                strokeWidth={2}
                dot={false}
              />
            )}
            {showGci && (
              <Line
                type="monotone"
                dataKey="gci_score"
                name="gci_score"
                stroke="#22c55e"
                strokeWidth={1.5}
                dot={false}
              />
            )}
            {showEvi && (
              <Line
                type="monotone"
                dataKey="evi_score"
                name="evi_score"
                stroke="#84cc16"
                strokeWidth={1.5}
                dot={false}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}
