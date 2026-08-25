"""
CropVision - Historical Trajectory Router
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import FieldDB, AnalysisRecordDB

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("/{field_id}")
def get_field_history(field_id: int, db: Session = Depends(get_db)):
    """Retrieve full chronological historical health records for a field."""
    field = db.query(FieldDB).filter(FieldDB.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found.")
        
    records = (
        db.query(AnalysisRecordDB)
        .filter(AnalysisRecordDB.field_id == field_id)
        .order_by(AnalysisRecordDB.scan_date.asc())
        .all()
    )
    
    timeline = []
    for r in records:
        timeline.append({
            "id": r.id,
            "date": r.scan_date,
            "growth_stage": r.growth_stage,
            "cchs_score": r.cchs_score,
            "status": r.status_label,
            "raw_indices": r.raw_indices,
            "sub_scores": r.sub_scores,
            "weights_used": r.weights_used,
            "trend": r.trend,
            "plain_language": r.plain_language,
            "zone_distribution": r.zone_distribution,
        })
        
    return {
        "field_id": field.id,
        "field_name": field.name,
        "crop_type": field.crop_type,
        "total_scans": len(timeline),
        "timeline": timeline,
    }
