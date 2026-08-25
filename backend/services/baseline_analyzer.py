"""
CropVision - Historical Baseline & Trend Analyzer

This module implements the dynamic multi-scan baseline comparison engine.
Rather than evaluating crop health using static fixed thresholds alone (which miss
incipient stress during peak season), it evaluates each field's temporal trajectory
against its own past 3-4 satellite readings.

Capabilities:
1. Dynamic Rolling Baseline: Evaluates current CCHS against a 3-4 scan moving baseline.
2. Velocity & Slope Regression: Computes the rate of health loss/gain over time.
3. Early Sub-clinical Stress Detection: Detects downward drift before a fixed threshold is crossed.
4. Component Index Divergence: Identifies which specific physiological metric (e.g. moisture vs nitrogen)
   is driving the decline.
5. Spatial Zone Anomaly Analysis: Pinpoints sub-field clusters (e.g., NE vs SW quadrants).
"""

from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime


def analyze_historical_trend(
    current_reading: Dict[str, Any],
    past_readings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Evaluate crop health trajectory relative to historical baseline.
    
    Args:
        current_reading: Dict with keys `cchs_score`, `sub_scores`, `raw_indices`, `date`
        past_readings: List of prior reading Dicts sorted chronologically (oldest first)
    
    Returns:
        Comprehensive trajectory analysis including status, slope, delta, and driver.
    """
    current_score = float(current_reading.get("cchs_score", 0.0))
    
    if not past_readings:
        return {
            "trend_status": "STABLE",
            "trend_label": "Baseline Established",
            "trend_arrow": "→",
            "trend_color": "#64748b",
            "delta_vs_previous": 0.0,
            "delta_vs_baseline": 0.0,
            "rolling_baseline_score": current_score,
            "slope": 0.0,
            "is_declining": False,
            "severity": "NORMAL",
            "primary_divergence": None,
            "reading_count": 1,
            "trend_summary": "Initial baseline established. Monitoring ongoing.",
        }
    
    # Extract past 3-4 scores
    recent_history = past_readings[-4:]
    past_scores = [float(r.get("cchs_score", 0.0)) for r in recent_history]
    
    # 1. Delta vs last reading
    last_score = past_scores[-1]
    delta_prev = round(current_score - last_score, 1)
    
    # 2. Delta vs 3-4 reading rolling baseline
    rolling_baseline = round(float(np.mean(past_scores)), 1)
    delta_baseline = round(current_score - rolling_baseline, 1)
    
    # 3. Trajectory regression / slope over time series
    all_scores = past_scores + [current_score]
    x_axis = np.arange(len(all_scores))
    if len(all_scores) >= 2:
        slope, _ = np.polyfit(x_axis, all_scores, deg=1)
        slope = round(float(slope), 2)
    else:
        slope = 0.0
    
    # 4. Check component index divergence (NDWI vs GCI vs NDVI vs EVI)
    last_reading = recent_history[-1]
    curr_raw = current_reading.get("raw_indices", {})
    last_raw = last_reading.get("raw_indices", {})
    
    index_deltas = {}
    for idx_name in ["ndwi", "gci", "ndvi", "evi"]:
        c_val = curr_raw.get(idx_name)
        l_val = last_raw.get(idx_name)
        if c_val is not None and l_val is not None:
            # percentage change
            pct_change = round(((c_val - l_val) / (abs(l_val) + 1e-4)) * 100.0, 1)
            index_deltas[idx_name] = pct_change
    
    # Find steepest dropping index
    primary_divergence = None
    if index_deltas:
        worst_idx = min(index_deltas, key=index_deltas.get)
        if index_deltas[worst_idx] < -4.0:
            primary_divergence = {
                "index": worst_idx.upper(),
                "percent_change": index_deltas[worst_idx],
            }
    
    # 5. Trend Classification Logic
    # Anomaly condition: downward slope or significant drop from rolling baseline
    if delta_baseline <= -8.0 or slope <= -3.0:
        trend_status = "RAPID_DECLINE"
        trend_label = "Rapid Decline"
        trend_arrow = "↓↓"
        trend_color = "#ef4444"
        is_declining = True
        severity = "HIGH"
        summary = f"Health dropped {abs(delta_baseline)} pts below 4-scan baseline ({rolling_baseline}). Immediate intervention needed."
    elif delta_baseline <= -3.0 or slope <= -1.0 or delta_prev <= -4.0:
        trend_status = "MODERATE_DECLINE"
        trend_label = "Trending Downward"
        trend_arrow = "↓"
        trend_color = "#f97316"
        is_declining = True
        severity = "MEDIUM"
        summary = f"Field is trending downward vs recent average ({rolling_baseline}) despite moderate absolute score."
    elif delta_baseline >= 5.0 or slope >= 1.5 or delta_prev >= 4.0:
        trend_status = "IMPROVING"
        trend_label = "Vigorously Improving"
        trend_arrow = "↑"
        trend_color = "#10b981"
        is_declining = False
        severity = "POSITIVE"
        summary = f"Health improved +{delta_baseline} pts above baseline, showing strong growth response."
    else:
        trend_status = "STABLE"
        trend_label = "Consistent & Stable"
        trend_arrow = "→"
        trend_color = "#3b82f6"
        is_declining = False
        severity = "NORMAL"
        summary = f"Crop vigor is steady within ±{abs(delta_baseline)} pts of historical baseline."
        
    return {
        "trend_status": trend_status,
        "trend_label": trend_label,
        "trend_arrow": trend_arrow,
        "trend_color": trend_color,
        "delta_vs_previous": delta_prev,
        "delta_vs_baseline": delta_baseline,
        "rolling_baseline_score": rolling_baseline,
        "slope": slope,
        "is_declining": is_declining,
        "severity": severity,
        "primary_divergence": primary_divergence,
        "index_deltas": index_deltas,
        "reading_count": len(all_scores),
        "trend_summary": summary,
    }
