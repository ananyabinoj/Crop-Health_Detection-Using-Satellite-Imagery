"""
Unit tests for Composite Crop Health Score (CCHS) and Growth Stage Weighting
"""

import pytest
from backend.services.cchs_engine import (
    calculate_cchs,
    normalize_ndvi,
    normalize_evi,
    normalize_gci,
    normalize_ndwi,
    get_health_classification,
    GrowthStageWeights,
    DEFAULT_STAGE_WEIGHTS,
)


def test_normalization_functions():
    # NDVI 0.85 should scale to ~100
    assert normalize_ndvi(0.85) == 100.0
    # NDVI 0.10 should scale to 0
    assert normalize_ndvi(0.10) == 0.0
    
    # EVI 0.75 should scale to 100
    assert normalize_evi(0.75) == 100.0
    
    # GCI 5.50 should scale to 100
    assert normalize_gci(5.50) == 100.0
    
    # NDWI 0.45 should scale to 100
    assert normalize_ndwi(0.45) == 100.0


def test_growth_stage_weight_divergence():
    # In Flowering stage, NDWI (water) weight should be higher than in Emergence
    flowering_w = DEFAULT_STAGE_WEIGHTS["FLOWERING"]
    emergence_w = DEFAULT_STAGE_WEIGHTS["EMERGENCE"]
    
    assert flowering_w.ndwi > emergence_w.ndwi
    assert emergence_w.ndvi > flowering_w.ndvi


def test_cchs_dynamic_impact():
    # Field has high NDVI (0.75) but low moisture NDWI (0.05)
    # Under VEGETATIVE stage vs FLOWERING stage
    veg_result = calculate_cchs(ndvi=0.75, evi=0.60, gci=4.0, ndwi=0.05, growth_stage="VEGETATIVE")
    flowering_result = calculate_cchs(ndvi=0.75, evi=0.60, gci=4.0, ndwi=0.05, growth_stage="FLOWERING")
    
    # Because NDWI is stressed, FLOWERING stage (which penalizes water deficit heavier) should produce a lower score
    assert flowering_result["cchs_score"] < veg_result["cchs_score"]


def test_custom_weights_override():
    custom_w = GrowthStageWeights(ndvi=0.10, evi=0.10, gci=0.10, ndwi=0.70)
    result = calculate_cchs(ndvi=0.80, evi=0.70, gci=5.0, ndwi=-0.10, custom_weights=custom_w)
    
    # NDWI is near zero sub-score and weighted 70%, score should drop substantially
    assert result["cchs_score"] < 40.0


def test_health_classification_grades():
    assert get_health_classification(85.0)["status"] == "EXCELLENT"
    assert get_health_classification(70.0)["status"] == "GOOD"
    assert get_health_classification(55.0)["status"] == "MODERATE"
    assert get_health_classification(40.0)["status"] == "STRESSED"
    assert get_health_classification(25.0)["status"] == "CRITICAL"
