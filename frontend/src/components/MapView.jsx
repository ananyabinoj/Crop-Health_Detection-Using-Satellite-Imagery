import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  Layers,
  MapPin,
  Maximize2,
  PenTool,
  Check,
  X,
  Eye,
  Sparkles,
} from "lucide-react";

export default function MapView({
  selectedField,
  analysis,
  onSaveDrawnField,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const boundaryLayerRef = useRef(null);
  const gridLayerRef = useRef(null);
  const drawLayerRef = useRef(null);

  const [activeLayerMode, setActiveLayerMode] = useState("cchs"); // "cchs", "ndvi", "ndwi", "gci", "none"
  const [baseMapType, setBaseMapType] = useState("satellite"); // "satellite", "dark"
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawPoints, setDrawPoints] = useState([]);
  const [newFieldName, setNewFieldName] = useState("");
  const [newCropType, setNewCropType] = useState("Corn");

  // Initialize Map Instance
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [42.034, -93.625],
        zoom: 15,
        zoomControl: false,
        attributionControl: false,
      });

      L.control.zoom({ position: "bottomright" }).addTo(map);

      // Base tile layers
      const satelliteLayer = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 19 }
      );
      const darkLayer = L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        { maxZoom: 19 }
      );

      satelliteLayer.addTo(map);
      mapInstanceRef.current = { map, satelliteLayer, darkLayer };
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.map.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Base Map Type
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const { map, satelliteLayer, darkLayer } = mapInstanceRef.current;

    if (baseMapType === "satellite") {
      map.removeLayer(darkLayer);
      satelliteLayer.addTo(map);
    } else {
      map.removeLayer(satelliteLayer);
      darkLayer.addTo(map);
    }
  }, [baseMapType]);

  // Render Boundary & Spatial Grid Layers
  useEffect(() => {
    if (!mapInstanceRef.current || !selectedField) return;
    const { map } = mapInstanceRef.current;

    // Clear previous layers
    if (boundaryLayerRef.current) {
      map.removeLayer(boundaryLayerRef.current);
      boundaryLayerRef.current = null;
    }
    if (gridLayerRef.current) {
      map.removeLayer(gridLayerRef.current);
      gridLayerRef.current = null;
    }

    try {
      // 1. Render Boundary Polygon
      const boundaryGeoJSON = selectedField.boundary_geojson;
      if (boundaryGeoJSON) {
        const bLayer = L.geoJSON(boundaryGeoJSON, {
          style: {
            color: "#10b981",
            weight: 3,
            fillColor: "#10b981",
            fillOpacity: 0.05,
            dashArray: "4, 4",
          },
        }).addTo(map);
        boundaryLayerRef.current = bLayer;
        map.fitBounds(bLayer.getBounds(), { padding: [40, 40], maxZoom: 16 });
      }

      // 2. Render Spatial 10m Grid Cells
      if (analysis && analysis.spatial_grid && activeLayerMode !== "none") {
        const gridLayer = L.geoJSON(analysis.spatial_grid, {
          style: (feature) => {
            const props = feature.properties || {};
            let fillColor = "#10b981";
            let opacity = 0.55;

            if (activeLayerMode === "cchs") {
              fillColor = props.color || (props.cchs_score >= 65 ? "#10b981" : props.cchs_score >= 50 ? "#f59e0b" : "#ef4444");
              opacity = 0.65;
            } else if (activeLayerMode === "ndvi") {
              const ndvi = props.ndvi || 0.5;
              fillColor = ndvi >= 0.7 ? "#059669" : ndvi >= 0.5 ? "#10b981" : ndvi >= 0.35 ? "#eab308" : "#ef4444";
              opacity = 0.65;
            } else if (activeLayerMode === "ndwi") {
              const ndwi = props.ndwi || 0.2;
              fillColor = ndwi >= 0.3 ? "#0284c7" : ndwi >= 0.2 ? "#06b6d4" : ndwi >= 0.1 ? "#38bdf8" : "#f97316";
              opacity = 0.65;
            } else if (activeLayerMode === "gci") {
              const gci = props.gci || 3.0;
              fillColor = gci >= 4.0 ? "#15803d" : gci >= 2.5 ? "#22c55e" : gci >= 1.5 ? "#a3e635" : "#eab308";
              opacity = 0.65;
            }

            return {
              color: "rgba(255, 255, 255, 0.15)",
              weight: 0.5,
              fillColor: fillColor,
              fillOpacity: opacity,
            };
          },
          onEachFeature: (feature, layer) => {
            const p = feature.properties || {};
            layer.bindPopup(`
              <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.82rem; min-width: 160px;">
                <div style="font-weight: 800; color: #34d399; margin-bottom: 6px; font-size: 0.9rem;">
                  10m Cell Analysis
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                  <span style="color: #94a3b8;">CCHS Score:</span>
                  <strong style="color: #f8fafc;">${p.cchs_score} / 100</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                  <span style="color: #94a3b8;">Zone Status:</span>
                  <strong style="color: ${p.color};">${p.zone_category || p.health_status}</strong>
                </div>
                <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 6px 0;" />
                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                  <span style="color: #94a3b8;">NDVI (Biomass):</span>
                  <span style="color: #f8fafc; font-family: monospace;">${p.ndvi}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                  <span style="color: #94a3b8;">NDWI (Moisture):</span>
                  <span style="color: #f8fafc; font-family: monospace;">${p.ndwi}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                  <span style="color: #94a3b8;">GCI (Chlorophyll):</span>
                  <span style="color: #f8fafc; font-family: monospace;">${p.gci}</span>
                </div>
              </div>
            `);
          },
        }).addTo(map);
        gridLayerRef.current = gridLayer;
      }
    } catch (e) {
      console.error("Map layer rendering error:", e);
    }
  }, [selectedField, analysis, activeLayerMode]);

  // Handle Drawing Interaction
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const { map } = mapInstanceRef.current;

    const handleMapClick = (e) => {
      if (!isDrawing) return;
      const { lat, lng } = e.latlng;
      setDrawPoints((prev) => [...prev, [lng, lat]]);
    };

    map.on("click", handleMapClick);
    return () => {
      map.off("click", handleMapClick);
    };
  }, [isDrawing]);

  // Render Live Drawing Polygons
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const { map } = mapInstanceRef.current;

    if (drawLayerRef.current) {
      map.removeLayer(drawLayerRef.current);
      drawLayerRef.current = null;
    }

    if (drawPoints.length > 0) {
      const latlngs = drawPoints.map((pt) => [pt[1], pt[0]]);
      const poly = L.polygon(latlngs, {
        color: "#38bdf8",
        weight: 3,
        fillColor: "#0284c7",
        fillOpacity: 0.25,
        dashArray: "6, 6",
      }).addTo(map);
      drawLayerRef.current = poly;
    }
  }, [drawPoints]);

  const handleFinishDrawing = () => {
    if (drawPoints.length < 3) {
      alert("Please click at least 3 points on the map to define a closed field boundary.");
      return;
    }
    // Close polygon
    const closed = [...drawPoints, drawPoints[0]];
    const geojson = {
      type: "Polygon",
      coordinates: [closed],
    };

    onSaveDrawnField({
      name: newFieldName.trim() || `Drawn Field #${Math.floor(Math.random() * 900 + 100)}`,
      crop_type: newCropType,
      boundary_geojson: geojson,
    });

    // Reset
    setIsDrawing(false);
    setDrawPoints([]);
    setNewFieldName("");
  };

  return (
    <div
      className="glass-panel"
      style={{
        position: "relative",
        height: "540px",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Top Map Control Bar */}
      <div
        style={{
          position: "absolute",
          top: "14px",
          left: "14px",
          right: "14px",
          zIndex: 1000,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "10px",
          pointerEvents: "auto",
        }}
      >
        {/* Layer Mode Switcher */}
        <div
          style={{
            background: "rgba(10, 20, 22, 0.88)",
            backdropFilter: "blur(12px)",
            border: "1px solid var(--border-highlight)",
            borderRadius: "10px",
            padding: "4px",
            display: "flex",
            alignItems: "center",
            gap: "4px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
          }}
        >
          <span style={{ fontSize: "0.72rem", fontWeight: "700", color: "var(--text-muted)", padding: "0 8px" }}>
            Overlay:
          </span>
          {[
            { id: "cchs", label: "Health Zones (CCHS)" },
            { id: "ndvi", label: "NDVI" },
            { id: "ndwi", label: "NDWI (Water)" },
            { id: "gci", label: "GCI (Chlorophyll)" },
            { id: "none", label: "Boundary Only" },
          ].map((l) => (
            <button
              key={l.id}
              onClick={() => setActiveLayerMode(l.id)}
              style={{
                background: activeLayerMode === l.id ? "rgba(16, 185, 129, 0.25)" : "transparent",
                color: activeLayerMode === l.id ? "#34d399" : "var(--text-muted)",
                border: activeLayerMode === l.id ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid transparent",
                borderRadius: "6px",
                padding: "5px 10px",
                fontSize: "0.74rem",
                fontWeight: activeLayerMode === l.id ? "700" : "500",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {l.label}
            </button>
          ))}
        </div>

        {/* Base Map Toggle & Draw Trigger */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {/* Base Map Toggle */}
          <div
            style={{
              background: "rgba(10, 20, 22, 0.88)",
              backdropFilter: "blur(12px)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "8px",
              padding: "4px 8px",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Basemap:</span>
            <button
              onClick={() => setBaseMapType(baseMapType === "satellite" ? "dark" : "satellite")}
              style={{
                background: "rgba(255, 255, 255, 0.08)",
                color: "#f8fafc",
                border: "none",
                borderRadius: "4px",
                padding: "3px 8px",
                fontSize: "0.72rem",
                cursor: "pointer",
                fontWeight: "600",
              }}
            >
              {baseMapType === "satellite" ? "Satellite Imagery" : "Dark Carto"}
            </button>
          </div>

          {/* Interactive Draw Boundary Button */}
          <button
            onClick={() => {
              setIsDrawing(!isDrawing);
              setDrawPoints([]);
            }}
            className={isDrawing ? "btn-primary" : "btn-secondary"}
            style={{
              fontSize: "0.75rem",
              padding: "6px 12px",
              background: isDrawing ? "#0284c7" : undefined,
            }}
          >
            <PenTool size={14} />
            <span>{isDrawing ? "Cancel Drawing" : "Draw Boundary"}</span>
          </button>
        </div>
      </div>

      {/* Leaflet Canvas Container */}
      <div ref={mapContainerRef} style={{ flex: 1, width: "100%", height: "100%" }} />

      {/* Drawing Instructions Banner (Visible during drawing mode) */}
      {isDrawing && (
        <div
          style={{
            position: "absolute",
            bottom: "20px",
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 1000,
            background: "rgba(12, 24, 28, 0.95)",
            backdropFilter: "blur(16px)",
            border: "1px solid #38bdf8",
            borderRadius: "12px",
            padding: "12px 20px",
            display: "flex",
            alignItems: "center",
            gap: "16px",
            boxShadow: "0 10px 30px rgba(0,0,0,0.6)",
          }}
        >
          <div>
            <div style={{ fontSize: "0.82rem", fontWeight: "700", color: "#38bdf8" }}>
              Click on the map to place boundary corner vertices ({drawPoints.length} points placed)
            </div>
            <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
              <input
                type="text"
                placeholder="Field Name (e.g. West Farm #3)"
                value={newFieldName}
                onChange={(e) => setNewFieldName(e.target.value)}
                style={{ fontSize: "0.75rem", padding: "4px 8px", width: "160px" }}
              />
              <select
                value={newCropType}
                onChange={(e) => setNewCropType(e.target.value)}
                style={{ fontSize: "0.75rem", padding: "4px 8px" }}
              >
                <option value="Corn">Corn</option>
                <option value="Wheat">Wheat</option>
                <option value="Soybean">Soybean</option>
                <option value="Cotton">Cotton</option>
                <option value="Wine Grapes">Wine Grapes</option>
              </select>
            </div>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={handleFinishDrawing}
              disabled={drawPoints.length < 3}
              className="btn-primary"
              style={{ fontSize: "0.76rem", padding: "6px 12px" }}
            >
              <Check size={14} />
              <span>Save & Analyze</span>
            </button>
            <button
              onClick={() => {
                setIsDrawing(false);
                setDrawPoints([]);
              }}
              className="btn-secondary"
              style={{ fontSize: "0.76rem", padding: "6px 10px" }}
            >
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Map Legend Overlay */}
      <div
        style={{
          position: "absolute",
          bottom: "16px",
          left: "16px",
          zIndex: 900,
          background: "rgba(10, 20, 22, 0.9)",
          backdropFilter: "blur(12px)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "8px",
          padding: "8px 12px",
          display: "flex",
          flexDirection: "column",
          gap: "6px",
          boxShadow: "0 6px 18px rgba(0,0,0,0.4)",
        }}
      >
        <span style={{ fontSize: "0.7rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>
          Health Zone Legend
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "0.72rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "2px", background: "#10b981" }} />
            <span>Healthy (&gt;65)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "2px", background: "#f59e0b" }} />
            <span>Moderate (50-64)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "2px", background: "#ef4444" }} />
            <span>Stressed (&lt;50)</span>
          </div>
        </div>
      </div>

    </div>
  );
}
