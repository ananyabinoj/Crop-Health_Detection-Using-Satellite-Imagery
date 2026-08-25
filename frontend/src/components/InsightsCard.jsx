import React from "react";
import {
  FileText,
  AlertCircle,
  CheckCircle2,
  MapPin,
  Flame,
  Droplets,
  Sprout,
  ShieldAlert,
  Clock,
  ArrowRight,
} from "lucide-react";

export default function InsightsCard({ analysis }) {
  if (!analysis || !analysis.plain_language) {
    return (
      <div className="glass-panel" style={{ padding: "24px" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No agronomic insights generated yet.</p>
      </div>
    );
  }

  const { headline, executive_summary, primary_issue, issue_type, affected_quadrant, action_items } =
    analysis.plain_language;
  const isDeclining = analysis.trend?.is_declining;

  // Icon & Theme depending on issue type
  const issueConfig = {
    WATER_DEFICIT: {
      icon: Droplets,
      color: "#06b6d4",
      bgBadge: "rgba(6, 182, 212, 0.15)",
      borderBadge: "rgba(6, 182, 212, 0.35)",
    },
    NUTRIENT_DEFICIENCY: {
      icon: Sprout,
      color: "#f59e0b",
      bgBadge: "rgba(245, 158, 11, 0.15)",
      borderBadge: "rgba(245, 158, 11, 0.35)",
    },
    CANOPY_THINNING: {
      icon: ShieldAlert,
      color: "#f43f5e",
      bgBadge: "rgba(244, 63, 94, 0.15)",
      borderBadge: "rgba(244, 63, 94, 0.35)",
    },
    OPTIMAL: {
      icon: CheckCircle2,
      color: "#10b981",
      bgBadge: "rgba(16, 185, 129, 0.15)",
      borderBadge: "rgba(16, 185, 129, 0.35)",
    },
  }[issue_type || "OPTIMAL"] || {
    icon: AlertCircle,
    color: "#38bdf8",
    bgBadge: "rgba(56, 189, 248, 0.15)",
    borderBadge: "rgba(56, 189, 248, 0.35)",
  };

  const IssueIcon = issueConfig.icon;

  return (
    <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "18px" }}>
      
      {/* Top Header */}
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
            <FileText size={18} color="#34d399" />
          </div>
          <div>
            <h2 style={{ fontSize: "1.05rem", fontWeight: "700", color: "#f8fafc" }}>
              Agronomic Diagnosis & Action Plan
            </h2>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Plain-language translation for field management
            </p>
          </div>
        </div>

        {/* Primary Issue Badge */}
        <div
          className="badge"
          style={{
            backgroundColor: issueConfig.bgBadge,
            color: issueConfig.color,
            border: `1px solid ${issueConfig.borderBadge}`,
            fontSize: "0.78rem",
            padding: "5px 12px",
          }}
        >
          <IssueIcon size={14} />
          <span>{primary_issue}</span>
        </div>
      </div>

      {/* Headline & Executive Summary Box */}
      <div
        style={{
          background: isDeclining ? "rgba(239, 68, 68, 0.06)" : "rgba(16, 185, 129, 0.05)",
          border: `1px solid ${isDeclining ? "rgba(239, 68, 68, 0.25)" : "rgba(16, 185, 129, 0.2)"}`,
          borderRadius: "12px",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
          {isDeclining ? (
            <AlertCircle size={20} color="#f87171" style={{ flexShrink: 0, marginTop: "2px" }} />
          ) : (
            <CheckCircle2 size={20} color="#34d399" style={{ flexShrink: 0, marginTop: "2px" }} />
          )}
          <div>
            <h3 style={{ fontSize: "0.95rem", fontWeight: "700", color: "#f8fafc", marginBottom: "4px" }}>
              {headline}
            </h3>
            <p style={{ fontSize: "0.85rem", color: "#cbd5e1", lineHeight: "1.5" }}>
              {executive_summary}
            </p>
          </div>
        </div>

        {/* Affected Section Pill */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.76rem", color: "var(--text-dim)", marginTop: "4px", paddingLeft: "30px" }}>
          <MapPin size={13} color="#34d399" />
          <span>Focal Location: <strong style={{ color: "#e2e8f0" }}>{affected_quadrant || "Uniform field-wide"}</strong></span>
        </div>
      </div>

      {/* Actionable Recommendations Checklist */}
      <div>
        <h4 style={{ fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "12px" }}>
          Prioritized Action Checklist
        </h4>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {action_items && action_items.map((item, idx) => {
            const badgeClass =
              item.priority === "HIGH"
                ? "badge-rose"
                : item.priority === "MEDIUM"
                ? "badge-amber"
                : "badge-emerald";

            return (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "12px",
                  background: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "12px 14px",
                  transition: "background 0.2s ease",
                }}
              >
                <span className={`badge ${badgeClass}`} style={{ flexShrink: 0, marginTop: "1px" }}>
                  {item.badge || item.priority}
                </span>

                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: "0.86rem", fontWeight: "600", color: "#f1f5f9", marginBottom: "4px" }}>
                    {item.action}
                  </p>
                  <p style={{ fontSize: "0.76rem", color: "var(--text-muted)", lineHeight: "1.4" }}>
                    <span style={{ color: "#34d399", fontWeight: "600" }}>Agronomic Rationale: </span>
                    {item.rationale}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
}
