"""
CropVision - Plain-Language Agronomic Interpretation & Recommendation Engine

This module translates complex multispectral indices (NDVI, EVI, GCI, NDWI),
growth stage phenology, and rolling baseline trends into intuitive, plain-language
reports that non-technical farmers and field managers can immediately act upon.
"""

from typing import Dict, Any, List, Optional


def generate_plain_language_report(
    cchs_result: Dict[str, Any],
    trend_result: Dict[str, Any],
    crop_name: str = "Crop",
    spatial_stats: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate farmer-friendly plain-language diagnosis and prioritized action items.
    """
    cchs_score = cchs_result.get("cchs_score", 0.0)
    classification = cchs_result.get("classification", {})
    status_key = classification.get("status", "GOOD")
    growth_stage = cchs_result.get("growth_stage", "VEGETATIVE")
    sub_scores = cchs_result.get("sub_scores", {})
    
    is_declining = trend_result.get("is_declining", False)
    trend_status = trend_result.get("trend_status", "STABLE")
    delta_baseline = trend_result.get("delta_vs_baseline", 0.0)
    primary_divergence = trend_result.get("primary_divergence")
    
    # Sub-score values
    s_ndvi = sub_scores.get("ndvi_score", 50.0)
    s_evi = sub_scores.get("evi_score", 50.0)
    s_gci = sub_scores.get("gci_score", 50.0)
    s_ndwi = sub_scores.get("ndwi_score", 50.0)
    
    # Spatial quadrant stress detection
    spatial_summary = "field-wide"
    stressed_quadrant = None
    if spatial_stats and "quadrants" in spatial_stats:
        quads = spatial_stats["quadrants"]
        worst_quad = min(quads, key=lambda q: quads[q].get("mean_cchs", 100))
        if quads[worst_quad].get("mean_cchs", 100) < cchs_score - 5.0:
            stressed_quadrant = worst_quad
            spatial_summary = f"specifically concentrated in the {worst_quad.replace('_', ' ').title()}"

    # Determine Primary Agronomic Stress Driver
    # Case A: Water stress (NDWI lowest sub-score or fastest dropping)
    if s_ndwi < 50.0 and s_ndwi < min(s_ndvi, s_gci) or (primary_divergence and primary_divergence.get("index") == "NDWI"):
        primary_issue = "Water Stress (Irrigation Deficit)"
        issue_type = "WATER_DEFICIT"
    # Case B: Nitrogen/Nutrient stress (GCI lowest sub-score or fastest dropping)
    elif s_gci < 50.0 and s_gci < min(s_ndvi, s_ndwi) or (primary_divergence and primary_divergence.get("index") == "GCI"):
        primary_issue = "Nutrient Deficiency (Nitrogen / Chlorophyll Shortage)"
        issue_type = "NUTRIENT_DEFICIENCY"
    # Case C: Canopy biomass / physical foliage thinning (NDVI / EVI low)
    elif min(s_ndvi, s_evi) < 45.0:
        primary_issue = "Canopy Density Reduction (Pest, Disease, or Thinning)"
        issue_type = "CANOPY_THINNING"
    # Case D: Healthy / Optimal
    else:
        primary_issue = "Optimal Vigorous Growth"
        issue_type = "OPTIMAL"

    # Construct Headline & Executive Narrative
    stage_friendly = {
        "EMERGENCE": "early emergence stage",
        "VEGETATIVE": "rapid vegetative growth phase",
        "FLOWERING": "critical flowering & reproductive stage",
        "GRAIN_FILLING": "grain filling and pod development stage",
        "PRE_HARVEST": "pre-harvest maturation stage",
    }.get(growth_stage, "growth stage")

    if is_declining:
        if issue_type == "WATER_DEFICIT":
            headline = f"Canopy Water Deficit Detected in {crop_name} ({spatial_summary.title()})"
            summary = (
                f"Your {crop_name} field health score is currently {cchs_score}/100 and trending downward "
                f"({trend_result.get('trend_label', 'Declining')}, {delta_baseline:+.1f} pts below historical average). "
                f"The satellite moisture index (NDWI) dropped notably {spatial_summary}. During this {stage_friendly}, "
                f"water restriction can directly restrict flower retention and biomass formation."
            )
        elif issue_type == "NUTRIENT_DEFICIENCY":
            headline = f"Early Nitrogen/Chlorophyll Decline Flagged ({spatial_summary.title()})"
            summary = (
                f"Crop health is scoring {cchs_score}/100 and trending downward. Satellite chlorophyll measurements (GCI) "
                f"indicate early leaf chlorosis {spatial_summary} before yellowing is visible on ground level. "
                f"Prompt nutrient intervention can prevent yield drag during this {stage_friendly}."
            )
        else:
            headline = f"Crop Stress Anomaly Detected vs Historical Baseline"
            summary = (
                f"Your field's health score has dropped to {cchs_score}/100, trailing its previous 4-scan baseline by "
                f"{abs(delta_baseline):.1f} points. Field inspection is advised to diagnose emerging canopy thinning."
            )
    else:
        if cchs_score >= 80.0:
            headline = f"Excellent {crop_name} Health & Uniform Canopy Vigor"
            summary = (
                f"Your {crop_name} is performing exceptionally well at {cchs_score}/100. Leaf chlorophyll, canopy biomass, "
                f"and moisture retention are all in optimal ranges across the field during this {stage_friendly}."
            )
        elif cchs_score >= 65.0:
            headline = f"Good Overall Vigor with Stable Growth Trend"
            summary = (
                f"The field demonstrates steady health at {cchs_score}/100. Canopy metrics are tracking within expected "
                f"targets for this {stage_friendly}, with consistent baseline stability."
            )
        else:
            headline = f"Moderate Crop Performance with Opportunity for Improvement"
            summary = (
                f"Field health is rated at {cchs_score}/100. While stable relative to past scans, targeted agronomic "
                f"adjustments will help maximize yield potential during this {stage_friendly}."
            )

    # Actionable 3-Point Checklist
    action_items: List[Dict[str, Any]] = []
    
    if issue_type == "WATER_DEFICIT":
        target_loc = stressed_quadrant.replace('_', ' ').upper() if stressed_quadrant else "affected sections"
        action_items = [
            {
                "priority": "HIGH",
                "badge": "Urgent",
                "action": f"Inspect irrigation lines and soil moisture sensors in {target_loc}.",
                "rationale": "Canopy moisture shows early depletion; restoring adequate soil moisture prevents heat stress.",
            },
            {
                "priority": "MEDIUM",
                "badge": "Recommended",
                "action": "Increase irrigation cycle by 15-20% over the next 48-72 hours if no rain is forecasted.",
                "rationale": f"Ensures adequate transpiration flow during {stage_friendly}.",
            },
            {
                "priority": "LOW",
                "badge": "Monitoring",
                "action": "Schedule follow-up satellite scan in 5 days to confirm moisture recovery.",
                "rationale": "Verifies that root-zone water absorption has restored cell turgor.",
            },
        ]
    elif issue_type == "NUTRIENT_DEFICIENCY":
        target_loc = stressed_quadrant.replace('_', ' ').upper() if stressed_quadrant else "low-vigor zones"
        action_items = [
            {
                "priority": "HIGH",
                "badge": "Urgent",
                "action": f"Conduct targeted soil & tissue sampling in {target_loc} to verify nitrogen/potassium levels.",
                "rationale": "Chlorophyll index (GCI) decline indicates nutrient uptake inhibition.",
            },
            {
                "priority": "MEDIUM",
                "badge": "Recommended",
                "action": "Evaluate foliar nitrogen or side-dress fertilizer application according to soil test results.",
                "rationale": "Quickly replenishes active leaf nitrogen for photosynthetic vigor.",
            },
            {
                "priority": "LOW",
                "badge": "Monitoring",
                "action": "Inspect root system for compaction or root nematode damage preventing nutrient uptake.",
                "rationale": "Rules out soil physical barriers in lower-performing parcels.",
            },
        ]
    elif issue_type == "CANOPY_THINNING":
        target_loc = stressed_quadrant.replace('_', ' ').upper() if stressed_quadrant else "flagged zones"
        action_items = [
            {
                "priority": "HIGH",
                "badge": "Urgent",
                "action": f"Scout {target_loc} for pest infestation, fungal blight, or herbicide drift damage.",
                "rationale": "Sharp NDVI/EVI drop suggests loss of active green leaf area.",
            },
            {
                "priority": "MEDIUM",
                "badge": "Recommended",
                "action": "Apply targeted crop protection if economic threshold for pests/fungus is confirmed.",
                "rationale": "Arrests spreading foliar damage before canopy collapses.",
            },
            {
                "priority": "LOW",
                "badge": "Monitoring",
                "action": "Compare field edges against center for localized wildlife or border weed encroachment.",
                "rationale": "Identifies spatial boundary anomalies.",
            },
        ]
    else:
        # Optimal / Healthy
        action_items = [
            {
                "priority": "LOW",
                "badge": "Routine",
                "action": "Maintain current irrigation scheduling and balanced nutrient management protocol.",
                "rationale": "All biophysical indices are tracking above optimum baselines.",
            },
            {
                "priority": "LOW",
                "badge": "Routine",
                "action": f"Monitor weather forecasts for sudden heat spikes or precipitation shifts during {stage_friendly}.",
                "rationale": "Proactive planning helps sustain high vigor through maturation.",
            },
            {
                "priority": "LOW",
                "badge": "Monitoring",
                "action": "Next automated satellite pass will track maturity progression in 5 days.",
                "rationale": "Continuous monitoring ensures early detection of any emerging anomalies.",
            },
        ]

    return {
        "headline": headline,
        "executive_summary": summary,
        "primary_issue": primary_issue,
        "issue_type": issue_type,
        "affected_quadrant": stressed_quadrant.replace('_', ' ').title() if stressed_quadrant else "Uniform field-wide",
        "action_items": action_items,
    }
