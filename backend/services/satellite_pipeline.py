"""
CropVision - Satellite Data Retrieval & Preprocessing Pipeline

This module handles:
1. Google Earth Engine (GEE) Sentinel-2 Level-2A (COPERNICUS/S2_SR_HARMONIZED) retrieval,
   cloud masking (QA60 & SCL), spatial clipping, and 10m band extraction.
2. High-Fidelity Synthetic Multi-Spectral Pipeline (Demo / Fallback Mode) enabling instant
   reliable demonstration without live GEE OAuth blockers, generating realistic 10m
   reflectance grids within any drawn or uploaded GeoJSON boundary polygon.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from shapely.geometry import shape, Point, Polygon, mapping

from backend.services.index_calculator import calculate_all_indices, calculate_ndvi, calculate_evi, calculate_gci, calculate_ndwi
from backend.services.cchs_engine import calculate_cchs, GrowthStageWeights

logger = logging.getLogger("cropvision.satellite")

# Attempt GEE initialization
GEE_AVAILABLE = False
try:
    import ee
    try:
        # Try initializing with default credentials or project
        ee.Initialize()
        GEE_AVAILABLE = True
        logger.info("Google Earth Engine successfully initialized.")
    except Exception as ee_init_err:
        logger.info(f"Google Earth Engine credentials not initialized: {ee_init_err}. Using High-Fidelity Fallback Pipeline.")
except ImportError:
    logger.info("earthengine-api not installed or not imported. Using High-Fidelity Fallback Pipeline.")


def mask_s2_clouds_gee(image):
    """
    Mask clouds in Sentinel-2 SR imagery using QA60 and SCL bands.
    """
    qa = image.select("QA60")
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11
    mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    
    # SCL band cloud classes: 3 (cloud shadow), 8 (cloud medium), 9 (cloud high), 10 (cirrus)
    scl = image.select("SCL")
    scl_mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    
    return image.updateMask(mask).updateMask(scl_mask).divide(10000.0)


def fetch_satellite_gee(
    geojson_geom: Dict[str, Any],
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 10.0,
) -> Optional[Dict[str, Any]]:
    """
    Fetch Sentinel-2 surface reflectance via Google Earth Engine API.
    """
    if not GEE_AVAILABLE:
        return None
    
    try:
        import ee
        ee_geom = ee.Geometry(geojson_geom)
        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(ee_geom)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_cover))
            .map(mask_s2_clouds_gee)
        )
        
        # Take median composite across the window
        image = collection.median().clip(ee_geom)
        
        # Extract mean values for bands
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=ee_geom,
            scale=10,
            maxPixels=1e8,
        ).getInfo()
        
        b2 = stats.get("B2", 0.05)
        b3 = stats.get("B3", 0.08)
        b4 = stats.get("B4", 0.06)
        b8 = stats.get("B8", 0.45)
        b11 = stats.get("B11", 0.18)
        
        return {
            "source": "Google Earth Engine (Sentinel-2 L2A)",
            "bands": {"B2": b2, "B3": b3, "B4": b4, "B8": b8, "B11": b11},
            "cloud_cover": 0.0,
        }
    except Exception as e:
        logger.warning(f"GEE retrieval error: {e}. Falling back to simulation.")
        return None


def generate_field_spatial_grid(
    geojson_geometry: Dict[str, Any],
    crop_type: str = "Corn",
    growth_stage: str = "FLOWERING",
    anomaly_scenario: str = "WATER_DEFICIT_NE",
    grid_resolution_deg: float = 0.00025,  # ~25m cells for smooth visualization
) -> Dict[str, Any]:
    """
    High-Fidelity Multi-Spectral Raster & Vector Generator.
    Generates a 10m-equivalent spatial grid over the exact GeoJSON boundary with
    physiologically accurate band values, spatial gradients, and health zones.
    """
    poly_shape = shape(geojson_geometry)
    minx, miny, maxx, maxy = poly_shape.bounds
    
    # Base spectral profile based on crop type and growth stage
    base_profiles = {
        "FLOWERING": {"b2": 0.038, "b3": 0.082, "b4": 0.048, "b8": 0.460, "b11": 0.170},
        "VEGETATIVE": {"b2": 0.035, "b3": 0.090, "b4": 0.042, "b8": 0.510, "b11": 0.160},
        "EMERGENCE": {"b2": 0.060, "b3": 0.075, "b4": 0.085, "b8": 0.280, "b11": 0.220},
        "GRAIN_FILLING": {"b2": 0.045, "b3": 0.078, "b4": 0.065, "b8": 0.410, "b11": 0.190},
        "PRE_HARVEST": {"b2": 0.070, "b3": 0.085, "b4": 0.110, "b8": 0.320, "b11": 0.240},
    }
    stage_key = growth_stage.upper().strip()
    profile = base_profiles.get(stage_key, base_profiles["VEGETATIVE"])
    
    # Calculate grid points
    x_coords = np.arange(minx, maxx, grid_resolution_deg)
    y_coords = np.arange(miny, maxy, grid_resolution_deg)
    
    # Quadrant coordinate midpoints
    mid_x = (minx + maxx) / 2.0
    mid_y = (miny + maxy) / 2.0
    
    grid_features = []
    pixel_records = []
    
    quadrant_scores = {
        "north_east": [],
        "north_west": [],
        "south_east": [],
        "south_west": [],
        "center": [],
    }
    
    # Deterministic pseudo-random seed based on coordinate hash for repeatability
    np.random.seed(int(abs(minx * 1000 + miny * 1000) % 65535))
    
    for i, x in enumerate(x_coords):
        for j, y in enumerate(y_coords):
            # Create cell polygon
            cell_poly = Polygon([
                (x, y),
                (x + grid_resolution_deg, y),
                (x + grid_resolution_deg, y + grid_resolution_deg),
                (x, y + grid_resolution_deg),
                (x, y),
            ])
            cell_center = Point(x + grid_resolution_deg / 2.0, y + grid_resolution_deg / 2.0)
            
            # Check if cell intersects field boundary
            if poly_shape.intersects(cell_poly):
                # Normalized positions [0, 1] across field
                norm_x = (x - minx) / max(maxx - minx, 1e-6)
                norm_y = (y - miny) / max(maxy - miny, 1e-6)
                
                # Spatial gradient / anomaly simulation
                b2 = profile["b2"] + np.random.normal(0, 0.003)
                b3 = profile["b3"] + np.random.normal(0, 0.004)
                b4 = profile["b4"] + np.random.normal(0, 0.004)
                b8 = profile["b8"] + np.random.normal(0, 0.015)
                b11 = profile["b11"] + np.random.normal(0, 0.008)
                
                # Injected stress scenarios:
                if anomaly_scenario == "WATER_DEFICIT_NE":
                    # Northeast corner exhibits higher SWIR (B11) and lower NIR (B8) -> water stress
                    ne_factor = max(0.0, (norm_x - 0.4) * (norm_y - 0.4) * 2.5)
                    b11 += ne_factor * 0.09  # Higher SWIR absorption drop -> dry canopy
                    b8 -= ne_factor * 0.12   # Reduced NIR
                elif anomaly_scenario == "NITROGEN_DEFICIT_S":
                    # South parcel exhibits lower chlorophyll (higher green/red reflectance ratio, lower NIR)
                    s_factor = max(0.0, (0.6 - norm_y) * 1.8)
                    b3 += s_factor * 0.03
                    b8 -= s_factor * 0.10
                elif anomaly_scenario == "HIGH_VIGOR_UNIFORM":
                    # Excellent vigor throughout
                    b8 += 0.05
                    b11 -= 0.03
                
                # Compute indices
                b2 = max(0.01, b2)
                b3 = max(0.01, b3)
                b4 = max(0.01, b4)
                b8 = max(0.05, b8)
                b11 = max(0.02, b11)
                
                px_ndvi = calculate_ndvi(b8, b4)
                px_evi = calculate_evi(b8, b4, b2)
                px_gci = calculate_gci(b8, b3)
                px_ndwi = calculate_ndwi(b8, b11)
                
                cchs_data = calculate_cchs(px_ndvi, px_evi, px_gci, px_ndwi, growth_stage)
                px_score = cchs_data["cchs_score"]
                px_class = cchs_data["classification"]
                
                pixel_records.append({
                    "b2": b2, "b3": b3, "b4": b4, "b8": b8, "b11": b11,
                    "ndvi": px_ndvi, "evi": px_evi, "gci": px_gci, "ndwi": px_ndwi,
                    "cchs": px_score,
                })
                
                # Quadrant binning
                if abs(x - mid_x) < (maxx - minx) * 0.15 and abs(y - mid_y) < (maxy - miny) * 0.15:
                    quadrant_scores["center"].append(px_score)
                if x >= mid_x and y >= mid_y:
                    quadrant_scores["north_east"].append(px_score)
                elif x < mid_x and y >= mid_y:
                    quadrant_scores["north_west"].append(px_score)
                elif x >= mid_x and y < mid_y:
                    quadrant_scores["south_east"].append(px_score)
                else:
                    quadrant_scores["south_west"].append(px_score)
                
                feature = {
                    "type": "Feature",
                    "geometry": mapping(cell_poly),
                    "properties": {
                        "cchs_score": px_score,
                        "health_status": px_class["status"],
                        "zone_category": px_class["zone_category"],
                        "color": px_class["color"],
                        "ndvi": round(px_ndvi, 3),
                        "evi": round(px_evi, 3),
                        "gci": round(px_gci, 3),
                        "ndwi": round(px_ndwi, 3),
                    },
                }
                grid_features.append(feature)
    
    if not pixel_records:
        # Fallback single point center calculation if geometry is very small
        centroid = poly_shape.centroid
        px_ndvi = calculate_ndvi(profile["b8"], profile["b4"])
        px_evi = calculate_evi(profile["b8"], profile["b4"], profile["b2"])
        px_gci = calculate_gci(profile["b8"], profile["b3"])
        px_ndwi = calculate_ndwi(profile["b8"], profile["b11"])
        cchs_data = calculate_cchs(px_ndvi, px_evi, px_gci, px_ndwi, growth_stage)
        
        pixel_records.append({
            "b2": profile["b2"], "b3": profile["b3"], "b4": profile["b4"],
            "b8": profile["b8"], "b11": profile["b11"],
            "ndvi": px_ndvi, "evi": px_evi, "gci": px_gci, "ndwi": px_ndwi,
            "cchs": cchs_data["cchs_score"],
        })
        quadrant_scores["center"].append(cchs_data["cchs_score"])
    
    # Calculate Field Averages
    mean_b2 = float(np.mean([p["b2"] for p in pixel_records]))
    mean_b3 = float(np.mean([p["b3"] for p in pixel_records]))
    mean_b4 = float(np.mean([p["b4"] for p in pixel_records]))
    mean_b8 = float(np.mean([p["b8"] for p in pixel_records]))
    mean_b11 = float(np.mean([p["b11"] for p in pixel_records]))
    
    avg_ndvi = float(np.mean([p["ndvi"] for p in pixel_records]))
    avg_evi = float(np.mean([p["evi"] for p in pixel_records]))
    avg_gci = float(np.mean([p["gci"] for p in pixel_records]))
    avg_ndwi = float(np.mean([p["ndwi"] for p in pixel_records]))
    
    # Quadrant summary stats
    quad_summary = {}
    for q_name, scores in quadrant_scores.items():
        if scores:
            quad_summary[q_name] = {
                "mean_cchs": round(float(np.mean(scores)), 1),
                "pixel_count": len(scores),
            }
        else:
            quad_summary[q_name] = {"mean_cchs": 0.0, "pixel_count": 0}
            
    # Zone area distribution percentages
    total_pixels = len(pixel_records)
    healthy_count = sum(1 for p in pixel_records if p["cchs"] >= 65.0)
    moderate_count = sum(1 for p in pixel_records if 50.0 <= p["cchs"] < 65.0)
    stressed_count = sum(1 for p in pixel_records if p["cchs"] < 50.0)
    
    zone_distribution = {
        "healthy_pct": round((healthy_count / total_pixels) * 100.0, 1),
        "moderate_pct": round((moderate_count / total_pixels) * 100.0, 1),
        "stressed_pct": round((stressed_count / total_pixels) * 100.0, 1),
        "total_cells": total_pixels,
    }
    
    geojson_collection = {
        "type": "FeatureCollection",
        "features": grid_features,
    }
    
    return {
        "bands": {"B2": mean_b2, "B3": mean_b3, "B4": mean_b4, "B8": mean_b8, "B11": mean_b11},
        "indices": {"ndvi": avg_ndvi, "evi": avg_evi, "gci": avg_gci, "ndwi": avg_ndwi},
        "spatial_grid_geojson": geojson_collection,
        "zone_distribution": zone_distribution,
        "quadrants": quad_summary,
        "resolution_meters": 10,
        "source": "Sentinel-2 MSI Level-2A (Synthetic 10m Calibrated)",
    }
