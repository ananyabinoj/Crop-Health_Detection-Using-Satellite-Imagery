"""
CropVision - Composite Crop Health Score (CCHS) Engine

This module is the core proprietary intellectual property of CropVision.
It integrates multiple satellite-derived biophysical indices (NDVI, EVI, GCI, NDWI)
into a single, actionable 0-100 score.

Key Methodology:
1. Biophysical Index Normalization:
   Raw index values have diverse scales and non-linear agronomic responses. Each raw index
   is calibrated against healthy crop physiological ranges and scaled to a standardized
   0-100 sub-score.
   - NDVI (Biomass / Ground Cover): Scaled from 0.10 (bare soil) to 0.85 (peak canopy).
   - EVI (Structural Canopy Vigor): Scaled from 0.08 to 0.75 (dense non-saturated foliage).
   - GCI (Chlorophyll & Nitrogen Status): Scaled from 0.50 to 5.50 (nitrogen-replete tissue).
   - NDWI (Canopy Water Thickness): Scaled from -0.15 (severe wilting) to 0.45 (turgid leaves).

2. Phenological Growth-Stage Aware Dynamic Weighting:
   Different crop growth phases have vastly different physiological priorities:
   - Early Vegetative / Emergence: Ground cover & early root/shoot vigor are paramount (High NDVI/EVI).
   - Rapid Vegetative: Nitrogen uptake and canopy expansion dominate (Balanced NDVI/EVI/GCI).
   - Flowering / Heading / Reproductive: Extreme vulnerability to moisture deficits (NDWI weighted heavily, 35%),
     combined with peak photosynthesis demand (GCI 30%).
   - Grain Filling / Fruit Ripening: Photosynthetic maintenance and nutrient translocation (GCI/NDWI high).
   - Pre-Harvest / Maturation: Natural senescence begins; water stress is natural drying, so NDWI weight is reduced.

The growth stage profiles are completely configurable and extensible per crop type.
"""

from typing import Dict, Any, Union, Optional
from pydantic import BaseModel, Field
import numpy as np


class GrowthStageWeights(BaseModel):
    ndvi: float = Field(..., ge=0.0, le=1.0, description="Weight for Normalized Difference Vegetation Index")
    evi: float = Field(..., ge=0.0, le=1.0, description="Weight for Enhanced Vegetation Index")
    gci: float = Field(..., ge=0.0, le=1.0, description="Weight for Green Chlorophyll Index")
    ndwi: float = Field(..., ge=0.0, le=1.0, description="Weight for Normalized Difference Water Index")
    description: str = Field(default="", description="Agronomic rationale for this weighting matrix")

    def normalized(self) -> "GrowthStageWeights":
        """Ensure sum of weights equals exactly 1.0."""
        total = self.ndvi + self.evi + self.gci + self.ndwi
        if total <= 0:
            return GrowthStageWeights(ndvi=0.25, evi=0.25, gci=0.25, ndwi=0.25, description=self.description)
        return GrowthStageWeights(
            ndvi=round(self.ndvi / total, 4),
            evi=round(self.evi / total, 4),
            gci=round(self.gci / total, 4),
            ndwi=round(self.ndwi / total, 4),
            description=self.description,
        )


# Default Growth Stage Profiles
DEFAULT_STAGE_WEIGHTS: Dict[str, GrowthStageWeights] = {
    "EMERGENCE": GrowthStageWeights(
        ndvi=0.40,
        evi=0.30,
        gci=0.15,
        ndwi=0.15,
        description="Emergence & Early Vegetative: Focus on canopy coverage, ground establishment, and early biomass.",
    ),
    "VEGETATIVE": GrowthStageWeights(
        ndvi=0.35,
        evi=0.25,
        gci=0.25,
        ndwi=0.15,
        description="Rapid Vegetative Growth: Balanced focus on leaf area index (LAI), structural vigor, and nitrogen absorption.",
    ),
    "FLOWERING": GrowthStageWeights(
        ndvi=0.20,
        evi=0.15,
        gci=0.30,
        ndwi=0.35,
        description="Flowering & Reproductive: Peak sensitivity to water deficit (NDWI 35%) and chlorophyll activity (GCI 30%).",
    ),
    "GRAIN_FILLING": GrowthStageWeights(
        ndvi=0.25,
        evi=0.20,
        gci=0.30,
        ndwi=0.25,
        description="Grain Filling / Fruit Maturation: Active chlorophyll maintenance for starch filling and balanced moisture.",
    ),
    "PRE_HARVEST": GrowthStageWeights(
        ndvi=0.30,
        evi=0.25,
        gci=0.25,
        ndwi=0.20,
        description="Pre-Harvest & Maturation: Natural senescence underway; reduced penalty for drying canopy (NDWI 20%).",
    ),
}


def normalize_ndvi(raw_ndvi: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Scale raw NDVI [-1.0, 1.0] to agricultural sub-score [0, 100].
    Typical agricultural range: 0.10 (bare soil/emerging) to 0.85 (dense healthy canopy).
    """
    min_val, max_val = 0.10, 0.85
    arr = np.asarray(raw_ndvi, dtype=np.float64)
    scaled = (arr - min_val) / (max_val - min_val) * 100.0
    clipped = np.clip(scaled, 0.0, 100.0)
    if isinstance(raw_ndvi, (int, float)):
        return round(float(clipped.item()), 1)
    return clipped


def normalize_evi(raw_evi: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Scale raw EVI [-1.0, 1.0] to agricultural sub-score [0, 100].
    Typical agricultural range: 0.08 to 0.75.
    """
    min_val, max_val = 0.08, 0.75
    arr = np.asarray(raw_evi, dtype=np.float64)
    scaled = (arr - min_val) / (max_val - min_val) * 100.0
    clipped = np.clip(scaled, 0.0, 100.0)
    if isinstance(raw_evi, (int, float)):
        return round(float(clipped.item()), 1)
    return clipped


def normalize_gci(raw_gci: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Scale raw GCI [0.0, 10.0+] to agricultural sub-score [0, 100].
    Typical agricultural range: 0.50 (chlorosis/nutrient starvation) to 5.50 (nitrogen-rich foliage).
    """
    min_val, max_val = 0.50, 5.50
    arr = np.asarray(raw_gci, dtype=np.float64)
    scaled = (arr - min_val) / (max_val - min_val) * 100.0
    clipped = np.clip(scaled, 0.0, 100.0)
    if isinstance(raw_gci, (int, float)):
        return round(float(clipped.item()), 1)
    return clipped


def normalize_ndwi(raw_ndwi: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Scale raw NDWI [-1.0, 1.0] to agricultural sub-score [0, 100].
    Typical agricultural range: -0.15 (severe wilting/canopy water deficit) to 0.45 (hydrated canopy).
    """
    min_val, max_val = -0.15, 0.45
    arr = np.asarray(raw_ndwi, dtype=np.float64)
    scaled = (arr - min_val) / (max_val - min_val) * 100.0
    clipped = np.clip(scaled, 0.0, 100.0)
    if isinstance(raw_ndwi, (int, float)):
        return round(float(clipped.item()), 1)
    return clipped


def get_health_classification(cchs_score: float) -> Dict[str, str]:
    """
    Map a CCHS score (0-100) to standard agronomic health category, badge styling, and summary.
    """
    if cchs_score >= 80.0:
        return {
            "status": "EXCELLENT",
            "label": "Optimal Health",
            "color": "#10b981",  # Emerald Green
            "badge_class": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
            "zone_category": "Healthy",
            "summary": "Canopy biomass, chlorophyll levels, and moisture hydration are at peak potential.",
        }
    elif cchs_score >= 65.0:
        return {
            "status": "GOOD",
            "label": "Good Vigor",
            "color": "#22c55e",  # Green
            "badge_class": "bg-green-500/20 text-green-400 border-green-500/30",
            "zone_category": "Healthy",
            "summary": "Vegetation is healthy with minor normal field heterogeneity.",
        }
    elif cchs_score >= 50.0:
        return {
            "status": "MODERATE",
            "label": "Moderate / Mild Stress",
            "color": "#eab308",  # Amber/Yellow
            "badge_class": "bg-amber-500/20 text-amber-400 border-amber-500/30",
            "zone_category": "Moderate",
            "summary": "Subtle canopy stress detected. Inspection recommended before symptoms spread.",
        }
    elif cchs_score >= 35.0:
        return {
            "status": "STRESSED",
            "label": "Stressed / Attention Required",
            "color": "#f97316",  # Orange
            "badge_class": "bg-orange-500/20 text-orange-400 border-orange-500/30",
            "zone_category": "Stressed",
            "summary": "Noticeable vegetation or water stress impacting crop development.",
        }
    else:
        return {
            "status": "CRITICAL",
            "label": "Severe Stress / Critical Deficit",
            "color": "#ef4444",  # Red
            "badge_class": "bg-red-500/20 text-red-400 border-red-500/30",
            "zone_category": "Stressed",
            "summary": "Significant crop loss risk. Immediate corrective action required.",
        }


def calculate_cchs(
    ndvi: Union[float, np.ndarray],
    evi: Union[float, np.ndarray],
    gci: Union[float, np.ndarray],
    ndwi: Union[float, np.ndarray],
    growth_stage: str = "VEGETATIVE",
    custom_weights: Optional[GrowthStageWeights] = None,
) -> Dict[str, Any]:
    """
    Calculate the Composite Crop Health Score (CCHS) from raw index values.
    
    Args:
        ndvi: Raw NDVI value or array
        evi: Raw EVI value or array
        gci: Raw GCI value or array
        ndwi: Raw NDWI value or array
        growth_stage: Stage key ("EMERGENCE", "VEGETATIVE", "FLOWERING", "GRAIN_FILLING", "PRE_HARVEST")
        custom_weights: Optional override for stage weights
        
    Returns:
        Dict containing composite score, normalized sub-scores, active weights, and classification.
    """
    stage_key = growth_stage.upper().strip()
    if custom_weights:
        weights = custom_weights.normalized()
    else:
        weights = DEFAULT_STAGE_WEIGHTS.get(stage_key, DEFAULT_STAGE_WEIGHTS["VEGETATIVE"]).normalized()
    
    sub_ndvi = normalize_ndvi(ndvi)
    sub_evi = normalize_evi(evi)
    sub_gci = normalize_gci(gci)
    sub_ndwi = normalize_ndwi(ndwi)
    
    if isinstance(ndvi, (int, float)):
        composite = (
            weights.ndvi * sub_ndvi
            + weights.evi * sub_evi
            + weights.gci * sub_gci
            + weights.ndwi * sub_ndwi
        )
        cchs_score = round(float(np.clip(composite, 0.0, 100.0)), 1)
        classification = get_health_classification(cchs_score)
        
        return {
            "cchs_score": cchs_score,
            "classification": classification,
            "growth_stage": stage_key,
            "weights_used": {
                "ndvi": weights.ndvi,
                "evi": weights.evi,
                "gci": weights.gci,
                "ndwi": weights.ndwi,
            },
            "sub_scores": {
                "ndvi_score": sub_ndvi,
                "evi_score": sub_evi,
                "gci_score": sub_gci,
                "ndwi_score": sub_ndwi,
            },
            "raw_indices": {
                "ndvi": round(float(ndvi), 4),
                "evi": round(float(evi), 4),
                "gci": round(float(gci), 4),
                "ndwi": round(float(ndwi), 4),
            },
        }
    else:
        # Spatial numpy array calculation
        composite_arr = (
            weights.ndvi * sub_ndvi
            + weights.evi * sub_evi
            + weights.gci * sub_gci
            + weights.ndwi * sub_ndwi
        )
        cchs_arr = np.clip(composite_arr, 0.0, 100.0)
        mean_score = round(float(np.nanmean(cchs_arr)), 1)
        classification = get_health_classification(mean_score)
        
        return {
            "cchs_array": cchs_arr,
            "cchs_score": mean_score,
            "classification": classification,
            "growth_stage": stage_key,
            "weights_used": {
                "ndvi": weights.ndvi,
                "evi": weights.evi,
                "gci": weights.gci,
                "ndwi": weights.ndwi,
            },
        }
