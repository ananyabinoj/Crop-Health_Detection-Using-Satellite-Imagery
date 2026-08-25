"""
CropVision - Database Seed & Demo Data Loader

Populates the database with realistic agricultural fields, growth stage presets,
and multi-scan historical satellite observation records.
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from shapely.geometry import Polygon

from backend.database import SessionLocal, init_db
from backend.models import FieldDB, AnalysisRecordDB, GrowthStagePresetDB
from backend.services.cchs_engine import DEFAULT_STAGE_WEIGHTS, calculate_cchs, GrowthStageWeights
from backend.services.baseline_analyzer import analyze_historical_trend
from backend.services.plain_language import generate_plain_language_report
from backend.services.satellite_pipeline import generate_field_spatial_grid


DEMO_FIELDS = [
    {
        "name": "Green Valley Corn Field (Parcel #12)",
        "location_name": "Story County, Iowa, USA",
        "crop_type": "Corn",
        "current_growth_stage": "FLOWERING",
        "area_hectares": 18.5,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [-93.6280, 42.0320],
                [-93.6210, 42.0320],
                [-93.6210, 42.0380],
                [-93.6280, 42.0380],
                [-93.6280, 42.0320],
            ]],
        },
        "history": [
            {
                "date": "2026-06-15",
                "stage": "VEGETATIVE",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.032, "B3": 0.088, "B4": 0.038, "B8": 0.520, "B11": 0.150},
            },
            {
                "date": "2026-06-27",
                "stage": "VEGETATIVE",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.034, "B3": 0.090, "B4": 0.040, "B8": 0.530, "B11": 0.155},
            },
            {
                "date": "2026-07-10",
                "stage": "FLOWERING",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.036, "B3": 0.084, "B4": 0.045, "B8": 0.490, "B11": 0.170},
            },
            {
                "date": "2026-07-22",
                "stage": "FLOWERING",
                "scenario": "WATER_DEFICIT_NE",  # Injected decline: Northeast quadrant water stress
                "bands": {"B2": 0.040, "B3": 0.080, "B4": 0.052, "B8": 0.430, "B11": 0.220},
            },
        ],
    },
    {
        "name": "Punjab Golden Wheat Farm (Sector 4B)",
        "location_name": "Ludhiana, Punjab, India",
        "crop_type": "Wheat",
        "current_growth_stage": "VEGETATIVE",
        "area_hectares": 12.0,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [75.8520, 30.8980],
                [75.8600, 30.8980],
                [75.8600, 30.9040],
                [75.8520, 30.9040],
                [75.8520, 30.8980],
            ]],
        },
        "history": [
            {
                "date": "2026-01-10",
                "stage": "EMERGENCE",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.055, "B3": 0.076, "B4": 0.075, "B8": 0.310, "B11": 0.210},
            },
            {
                "date": "2026-01-25",
                "stage": "VEGETATIVE",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.040, "B3": 0.085, "B4": 0.050, "B8": 0.440, "B11": 0.170},
            },
            {
                "date": "2026-02-10",
                "stage": "VEGETATIVE",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.035, "B3": 0.092, "B4": 0.042, "B8": 0.510, "B11": 0.155},
            },
            {
                "date": "2026-02-24",
                "stage": "VEGETATIVE",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.032, "B3": 0.096, "B4": 0.038, "B8": 0.560, "B11": 0.145},
            },
        ],
    },
    {
        "name": "Mato Grosso Soybean Field (Plot #8)",
        "location_name": "Sorriso, Mato Grosso, Brazil",
        "crop_type": "Soybean",
        "current_growth_stage": "GRAIN_FILLING",
        "area_hectares": 35.0,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [-55.7180, -12.5490],
                [-55.7060, -12.5490],
                [-55.7060, -12.5400],
                [-55.7180, -12.5400],
                [-55.7180, -12.5490],
            ]],
        },
        "history": [
            {
                "date": "2026-01-05",
                "stage": "VEGETATIVE",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.035, "B3": 0.088, "B4": 0.042, "B8": 0.490, "B11": 0.160},
            },
            {
                "date": "2026-01-20",
                "stage": "FLOWERING",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.038, "B3": 0.084, "B4": 0.048, "B8": 0.460, "B11": 0.170},
            },
            {
                "date": "2026-02-05",
                "stage": "GRAIN_FILLING",
                "scenario": "NITROGEN_DEFICIT_S",
                "bands": {"B2": 0.044, "B3": 0.078, "B4": 0.060, "B8": 0.410, "B11": 0.190},
            },
            {
                "date": "2026-02-20",
                "stage": "GRAIN_FILLING",
                "scenario": "NITROGEN_DEFICIT_S",
                "bands": {"B2": 0.048, "B3": 0.072, "B4": 0.068, "B8": 0.380, "B11": 0.200},
            },
        ],
    },
    {
        "name": "Napa Valley Heritage Vineyard",
        "location_name": "Oakville, California, USA",
        "crop_type": "Wine Grapes",
        "current_growth_stage": "PRE_HARVEST",
        "area_hectares": 8.0,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [-122.4100, 38.4280],
                [-122.4020, 38.4280],
                [-122.4020, 38.4340],
                [-122.4100, 38.4340],
                [-122.4100, 38.4280],
            ]],
        },
        "history": [
            {
                "date": "2026-06-01",
                "stage": "VEGETATIVE",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.036, "B3": 0.085, "B4": 0.044, "B8": 0.480, "B11": 0.165},
            },
            {
                "date": "2026-06-20",
                "stage": "FLOWERING",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.038, "B3": 0.082, "B4": 0.046, "B8": 0.470, "B11": 0.170},
            },
            {
                "date": "2026-07-10",
                "stage": "GRAIN_FILLING",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.042, "B3": 0.080, "B4": 0.055, "B8": 0.450, "B11": 0.180},
            },
            {
                "date": "2026-07-30",
                "stage": "PRE_HARVEST",
                "scenario": "HIGH_VIGOR_UNIFORM",
                "bands": {"B2": 0.046, "B3": 0.078, "B4": 0.060, "B8": 0.440, "B11": 0.190},
            },
        ],
    },
]


def seed_database():
    """Initializes and seeds database with default presets and sample fields."""
    init_db()
    db: Session = SessionLocal()
    
    try:
        # 1. Seed Growth Stage Presets
        for stage_key, weights in DEFAULT_STAGE_WEIGHTS.items():
            existing = db.query(GrowthStagePresetDB).filter(GrowthStagePresetDB.stage_key == stage_key).first()
            if not existing:
                preset = GrowthStagePresetDB(
                    stage_key=stage_key,
                    stage_label=stage_key.replace("_", " ").title(),
                    ndvi_weight=weights.ndvi,
                    evi_weight=weights.evi,
                    gci_weight=weights.gci,
                    ndwi_weight=weights.ndwi,
                    description=weights.description,
                )
                db.add(preset)
        db.commit()
        
        # 2. Seed Fields if empty
        if db.query(FieldDB).count() == 0:
            for field_info in DEMO_FIELDS:
                field = FieldDB(
                    name=field_info["name"],
                    location_name=field_info["location_name"],
                    crop_type=field_info["crop_type"],
                    area_hectares=field_info["area_hectares"],
                    boundary_geojson=field_info["boundary_geojson"],
                    current_growth_stage=field_info["current_growth_stage"],
                )
                db.add(field)
                db.flush()  # assign field.id
                
                # Process historical readings
                past_readings_context = []
                for scan in field_info["history"]:
                    # Generate spatial raster grid & index calculations
                    spatial_res = generate_field_spatial_grid(
                        geojson_geometry=field_info["boundary_geojson"],
                        crop_type=field_info["crop_type"],
                        growth_stage=scan["stage"],
                        anomaly_scenario=scan["scenario"],
                    )
                    
                    indices = spatial_res["indices"]
                    cchs_res = calculate_cchs(
                        ndvi=indices["ndvi"],
                        evi=indices["evi"],
                        gci=indices["gci"],
                        ndwi=indices["ndwi"],
                        growth_stage=scan["stage"],
                    )
                    
                    # Analyze trend vs prior readings
                    trend_res = analyze_historical_trend(
                        current_reading={
                            "cchs_score": cchs_res["cchs_score"],
                            "sub_scores": cchs_res["sub_scores"],
                            "raw_indices": cchs_res["raw_indices"],
                            "date": scan["date"],
                        },
                        past_readings=past_readings_context,
                    )
                    
                    # Generate plain language interpretation
                    plain_res = generate_plain_language_report(
                        cchs_result=cchs_res,
                        trend_result=trend_res,
                        crop_name=field_info["crop_type"],
                        spatial_stats=spatial_res,
                    )
                    
                    record = AnalysisRecordDB(
                        field_id=field.id,
                        scan_date=scan["date"],
                        growth_stage=scan["stage"],
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
                    
                    past_readings_context.append({
                        "cchs_score": cchs_res["cchs_score"],
                        "raw_indices": cchs_res["raw_indices"],
                        "sub_scores": cchs_res["sub_scores"],
                        "date": scan["date"],
                        "growth_stage": scan["stage"],
                        "status": cchs_res["classification"]["label"],
                    })
                
                db.commit()
            print("Successfully seeded CropVision demo database with 4 multi-scan fields.")
        else:
            print("Database already contains fields. Seed skipped.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
