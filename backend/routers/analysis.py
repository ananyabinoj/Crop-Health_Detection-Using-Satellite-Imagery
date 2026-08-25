"""
CropVision - Satellite Analysis & CCHS Calculation Router
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    FieldDB,
    AnalysisRecordDB,
    GrowthStagePresetDB,
    RunAnalysisRequest,
    StageConfigUpdate,
)
from backend.services.cchs_engine import (
    calculate_cchs,
    GrowthStageWeights,
    DEFAULT_STAGE_WEIGHTS,
)
from backend.services.baseline_analyzer import analyze_historical_trend
from backend.services.plain_language import generate_plain_language_report
from backend.services.satellite_pipeline import (
    fetch_satellite_gee,
    generate_field_spatial_grid,
)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.get("/growth-stages")
def get_growth_stages(db: Session = Depends(get_db)):
    """Retrieve all growth stage weighting configurations."""
    presets = db.query(GrowthStagePresetDB).all()
    results = []
    for p in presets:
        results.append({
            "stage_key": p.stage_key,
            "stage_label": p.stage_label,
            "weights": {
                "ndvi": p.ndvi_weight,
                "evi": p.evi_weight,
                "gci": p.gci_weight,
                "ndwi": p.ndwi_weight,
            },
            "description": p.description,
        })
    return results


@router.put("/growth-stages/{stage_key}")
def update_growth_stage(stage_key: str, payload: StageConfigUpdate, db: Session = Depends(get_db)):
    """Update custom default weights for a specific growth stage."""
    stage_key = stage_key.upper().strip()
    preset = db.query(GrowthStagePresetDB).filter(GrowthStagePresetDB.stage_key == stage_key).first()
    if not preset:
        preset = GrowthStagePresetDB(stage_key=stage_key, stage_label=payload.stage_label)
        db.add(preset)
        
    # Normalize weights to sum to 1.0
    total = payload.ndvi_weight + payload.evi_weight + payload.gci_weight + payload.ndwi_weight
    if total <= 0:
        total = 1.0
        
    preset.stage_label = payload.stage_label
    preset.ndvi_weight = round(payload.ndvi_weight / total, 4)
    preset.evi_weight = round(payload.evi_weight / total, 4)
    preset.gci_weight = round(payload.gci_weight / total, 4)
    preset.ndwi_weight = round(payload.ndwi_weight / total, 4)
    if payload.description:
        preset.description = payload.description
        
    db.commit()
    return {
        "status": "success",
        "stage_key": preset.stage_key,
        "weights": {
            "ndvi": preset.ndvi_weight,
            "evi": preset.evi_weight,
            "gci": preset.gci_weight,
            "ndwi": preset.ndwi_weight,
        },
    }


@router.post("/run")
def run_field_analysis(payload: RunAnalysisRequest, db: Session = Depends(get_db)):
    """
    Execute satellite data retrieval, multispectral index computation,
    growth-stage aware CCHS scoring, rolling baseline trend analysis,
    and plain-language agronomic diagnosis.
    """
    field = db.query(FieldDB).filter(FieldDB.id == payload.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found.")
        
    growth_stage = payload.growth_stage or field.current_growth_stage or "VEGETATIVE"
    scan_date = payload.scan_date or datetime.now().strftime("%Y-%m-%d")
    
    # 1. Resolve Growth Stage Weights
    custom_weights_obj = None
    if payload.custom_weights:
        custom_weights_obj = GrowthStageWeights(
            ndvi=payload.custom_weights.ndvi,
            evi=payload.custom_weights.evi,
            gci=payload.custom_weights.gci,
            ndwi=payload.custom_weights.ndwi,
            description="Custom user weights applied for this analysis run",
        )
    else:
        # Check DB preset
        preset = db.query(GrowthStagePresetDB).filter(GrowthStagePresetDB.stage_key == growth_stage.upper()).first()
        if preset:
            custom_weights_obj = GrowthStageWeights(
                ndvi=preset.ndvi_weight,
                evi=preset.evi_weight,
                gci=preset.gci_weight,
                ndwi=preset.ndwi_weight,
                description=preset.description or "",
            )
            
    # 2. Retrieve Satellite Multispectral Data (GEE or High-Fidelity Spatial Pipeline)
    scenario = payload.simulate_scenario or "HIGH_VIGOR_UNIFORM"
    spatial_res = generate_field_spatial_grid(
        geojson_geometry=field.boundary_geojson,
        crop_type=field.crop_type,
        growth_stage=growth_stage,
        anomaly_scenario=scenario,
    )
    
    indices = spatial_res["indices"]
    
    # 3. Calculate Composite Crop Health Score (CCHS)
    cchs_res = calculate_cchs(
        ndvi=indices["ndvi"],
        evi=indices["evi"],
        gci=indices["gci"],
        ndwi=indices["ndwi"],
        growth_stage=growth_stage,
        custom_weights=custom_weights_obj,
    )
    
    # 4. Fetch Historical Readings for Baseline Trend Comparison
    past_db_records = (
        db.query(AnalysisRecordDB)
        .filter(AnalysisRecordDB.field_id == field.id)
        .order_by(AnalysisRecordDB.scan_date.asc())
        .all()
    )
    
    past_readings_context = []
    for r in past_db_records:
        past_readings_context.append({
            "cchs_score": r.cchs_score,
            "raw_indices": r.raw_indices,
            "sub_scores": r.sub_scores,
            "date": r.scan_date,
            "growth_stage": r.growth_stage,
            "status": r.status_label,
        })
        
    trend_res = analyze_historical_trend(
        current_reading={
            "cchs_score": cchs_res["cchs_score"],
            "sub_scores": cchs_res["sub_scores"],
            "raw_indices": cchs_res["raw_indices"],
            "date": scan_date,
        },
        past_readings=past_readings_context,
    )
    
    # 5. Generate Plain-Language Agronomic Interpretation
    plain_res = generate_plain_language_report(
        cchs_result=cchs_res,
        trend_result=trend_res,
        crop_name=field.crop_type,
        spatial_stats=spatial_res,
    )
    
    # 6. Save Analysis Record to Database
    record = AnalysisRecordDB(
        field_id=field.id,
        scan_date=scan_date,
        growth_stage=growth_stage,
        cchs_score=cchs_res["cchs_score"],
        status_label=cchs_res["classification"]["label"],
        raw_indices=cchs_res["raw_indices"],
        sub_scores=cchs_res["sub_scores"],
        weights_used=cchs_res["weights_used"],
        bands=spatial_res["bands"],
        trend=trend_res,
        plain_language=plain_res,
        spatial_grid=spatial_res["spatial_grid_geojson"],
        zone_distribution=spatial_res["zone_distribution"],
        quadrants=spatial_res["quadrants"],
    )
    db.add(record)
    
    # Update field's current growth stage if changed
    if field.current_growth_stage != growth_stage:
        field.current_growth_stage = growth_stage
        
    db.commit()
    db.refresh(record)
    
    return {
        "analysis_id": record.id,
        "field_id": field.id,
        "field_name": field.name,
        "crop_type": field.crop_type,
        "scan_date": record.scan_date,
        "growth_stage": record.growth_stage,
        "cchs_score": record.cchs_score,
        "classification": cchs_res["classification"],
        "sub_scores": record.sub_scores,
        "raw_indices": record.raw_indices,
        "weights_used": record.weights_used,
        "bands": record.bands,
        "trend": record.trend,
        "plain_language": record.plain_language,
        "spatial_grid": record.spatial_grid,
        "zone_distribution": record.zone_distribution,
        "quadrants": record.quadrants,
    }
