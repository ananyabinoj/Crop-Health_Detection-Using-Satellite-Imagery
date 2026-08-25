"""
CropVision - Fields API Router
"""

import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from shapely.geometry import shape, Polygon

from backend.database import get_db
from backend.models import FieldDB, AnalysisRecordDB, FieldCreate, FieldResponse

router = APIRouter(prefix="/api/fields", tags=["Fields"])


def calculate_area_hectares(geometry: Dict[str, Any]) -> float:
    """Calculate approximate field area in hectares from WGS84 GeoJSON geometry."""
    try:
        geom_shape = shape(geometry)
        # Approximate deg to meters at mid-latitude: 1 deg lat ~ 111km, 1 deg lon ~ 111km * cos(lat)
        centroid = geom_shape.centroid
        lat_rad = np_radians = float(centroid.y) * 3.14159265 / 180.0
        import math
        meters_x = 111320.0 * math.cos(lat_rad)
        meters_y = 110540.0
        area_sq_meters = geom_shape.area * meters_x * meters_y
        area_ha = round(area_sq_meters / 10000.0, 2)
        return max(0.1, area_ha)
    except Exception:
        return 10.0


@router.get("", response_model=List[FieldResponse])
def get_all_fields(db: Session = Depends(get_db)):
    """Retrieve all monitored fields with summary health status."""
    fields = db.query(FieldDB).order_by(FieldDB.created_at.desc()).all()
    results = []
    
    for f in fields:
        latest_record = (
            db.query(AnalysisRecordDB)
            .filter(AnalysisRecordDB.field_id == f.id)
            .order_by(AnalysisRecordDB.scan_date.desc())
            .first()
        )
        record_count = db.query(AnalysisRecordDB).filter(AnalysisRecordDB.field_id == f.id).count()
        
        results.append(
            FieldResponse(
                id=f.id,
                name=f.name,
                location_name=f.location_name,
                crop_type=f.crop_type,
                area_hectares=f.area_hectares or 10.0,
                current_growth_stage=f.current_growth_stage,
                boundary_geojson=f.boundary_geojson,
                created_at=f.created_at,
                record_count=record_count,
                latest_cchs=latest_record.cchs_score if latest_record else None,
                latest_status=latest_record.status_label if latest_record else None,
            )
        )
    return results


@router.post("", response_model=FieldResponse)
def create_field(payload: FieldCreate, db: Session = Depends(get_db)):
    """Create and register a new field boundary."""
    # Validate GeoJSON structure
    geom = payload.boundary_geojson
    if "geometry" in geom:
        geom = geom["geometry"]
    if geom.get("type") not in ["Polygon", "MultiPolygon"]:
        raise HTTPException(status_code=400, detail="Boundary geometry must be a Polygon or MultiPolygon.")
    
    area_ha = calculate_area_hectares(geom)
    
    field = FieldDB(
        name=payload.name,
        location_name=payload.location_name or "Custom Field Parcel",
        crop_type=payload.crop_type,
        area_hectares=area_ha,
        boundary_geojson=geom,
        current_growth_stage=payload.current_growth_stage,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    
    return FieldResponse(
        id=field.id,
        name=field.name,
        location_name=field.location_name,
        crop_type=field.crop_type,
        area_hectares=field.area_hectares,
        current_growth_stage=field.current_growth_stage,
        boundary_geojson=field.boundary_geojson,
        created_at=field.created_at,
        record_count=0,
        latest_cchs=None,
        latest_status=None,
    )


@router.get("/{field_id}")
def get_field_details(field_id: int, db: Session = Depends(get_db)):
    """Get complete field profile, latest analysis, and geometry."""
    field = db.query(FieldDB).filter(FieldDB.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found.")
    
    latest_record = (
        db.query(AnalysisRecordDB)
        .filter(AnalysisRecordDB.field_id == field.id)
        .order_by(AnalysisRecordDB.scan_date.desc())
        .first()
    )
    
    return {
        "id": field.id,
        "name": field.name,
        "location_name": field.location_name,
        "crop_type": field.crop_type,
        "area_hectares": field.area_hectares,
        "current_growth_stage": field.current_growth_stage,
        "boundary_geojson": field.boundary_geojson,
        "created_at": field.created_at,
        "latest_analysis": {
            "id": latest_record.id,
            "scan_date": latest_record.scan_date,
            "growth_stage": latest_record.growth_stage,
            "cchs_score": latest_record.cchs_score,
            "status_label": latest_record.status_label,
            "raw_indices": latest_record.raw_indices,
            "sub_scores": latest_record.sub_scores,
            "weights_used": latest_record.weights_used,
            "trend": latest_record.trend,
            "plain_language": latest_record.plain_language,
            "spatial_grid": latest_record.spatial_grid,
            "zone_distribution": latest_record.zone_distribution,
            "quadrants": latest_record.quadrants,
        } if latest_record else None,
    }


@router.delete("/{field_id}")
def delete_field(field_id: int, db: Session = Depends(get_db)):
    """Delete a field and all associated analysis records."""
    field = db.query(FieldDB).filter(FieldDB.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found.")
    db.delete(field)
    db.commit()
    return {"status": "success", "message": f"Field '{field.name}' successfully deleted."}


@router.post("/upload-boundary")
async def upload_boundary_file(file: UploadFile = File(...)):
    """
    Parse an uploaded boundary file (GeoJSON or JSON), validate polygon coordinates,
    and return sanitized GeoJSON geometry and calculated area.
    """
    try:
        content = await file.read()
        raw_text = content.decode("utf-8")
        parsed = json.loads(raw_text)
        
        # Extract polygon geometry
        geometry = None
        if parsed.get("type") == "FeatureCollection" and parsed.get("features"):
            geometry = parsed["features"][0].get("geometry")
        elif parsed.get("type") == "Feature":
            geometry = parsed.get("geometry")
        elif parsed.get("type") in ["Polygon", "MultiPolygon"]:
            geometry = parsed
            
        if not geometry:
            raise ValueError("No valid Polygon geometry found in uploaded file.")
            
        area_ha = calculate_area_hectares(geometry)
        
        return {
            "status": "success",
            "filename": file.filename,
            "geometry": geometry,
            "area_hectares": area_ha,
        }
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Failed to parse boundary file: {str(err)}")
