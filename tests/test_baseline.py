"""
Unit tests for Historical Baseline Trend & Anomaly Detection
"""

import pytest
from backend.services.baseline_analyzer import analyze_historical_trend


def test_baseline_empty_history():
    current = {
        "cchs_score": 82.0,
        "sub_scores": {"ndvi_score": 85, "evi_score": 80, "gci_score": 82, "ndwi_score": 80},
        "raw_indices": {"ndvi": 0.72, "evi": 0.55, "gci": 4.1, "ndwi": 0.35},
        "date": "2026-06-01",
    }
    res = analyze_historical_trend(current, [])
    assert res["trend_status"] == "STABLE"
    assert res["is_declining"] is False
    assert res["reading_count"] == 1


def test_baseline_declining_trend_flag():
    # Past 3 readings: 88, 86, 83 (Rolling baseline = 85.7)
    # Current reading: 71 (Delta = -14.7)
    past = [
        {"cchs_score": 88.0, "raw_indices": {"ndvi": 0.75, "evi": 0.60, "gci": 4.5, "ndwi": 0.38}, "date": "2026-06-01"},
        {"cchs_score": 86.0, "raw_indices": {"ndvi": 0.74, "evi": 0.59, "gci": 4.3, "ndwi": 0.36}, "date": "2026-06-15"},
        {"cchs_score": 83.0, "raw_indices": {"ndvi": 0.72, "evi": 0.57, "gci": 4.1, "ndwi": 0.30}, "date": "2026-07-01"},
    ]
    current = {
        "cchs_score": 71.0,
        "raw_indices": {"ndvi": 0.70, "evi": 0.52, "gci": 3.8, "ndwi": 0.15},  # NDWI dropped significantly
        "sub_scores": {"ndvi_score": 80, "evi_score": 70, "gci_score": 65, "ndwi_score": 45},
        "date": "2026-07-15",
    }
    
    res = analyze_historical_trend(current, past)
    
    assert res["is_declining"] is True
    assert res["trend_status"] in ["RAPID_DECLINE", "MODERATE_DECLINE"]
    assert res["delta_vs_baseline"] < -10.0
    assert res["primary_divergence"] is not None
    assert res["primary_divergence"]["index"] == "NDWI"


def test_baseline_improving_trend():
    past = [
        {"cchs_score": 70.0, "raw_indices": {"ndvi": 0.50, "evi": 0.40, "gci": 2.5, "ndwi": 0.20}, "date": "2026-01-01"},
        {"cchs_score": 75.0, "raw_indices": {"ndvi": 0.58, "evi": 0.45, "gci": 3.0, "ndwi": 0.24}, "date": "2026-01-15"},
        {"cchs_score": 80.0, "raw_indices": {"ndvi": 0.65, "evi": 0.52, "gci": 3.6, "ndwi": 0.28}, "date": "2026-02-01"},
    ]
    current = {
        "cchs_score": 86.0,
        "raw_indices": {"ndvi": 0.72, "evi": 0.58, "gci": 4.2, "ndwi": 0.32},
        "sub_scores": {"ndvi_score": 85, "evi_score": 80, "gci_score": 82, "ndwi_score": 80},
        "date": "2026-02-15",
    }
    
    res = analyze_historical_trend(current, past)
    assert res["trend_status"] == "IMPROVING"
    assert res["is_declining"] is False
    assert res["delta_vs_baseline"] > 5.0
