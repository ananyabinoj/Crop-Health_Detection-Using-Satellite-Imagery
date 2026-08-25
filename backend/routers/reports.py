"""
CropVision - PDF Reports Export Router
"""

import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import FieldDB, AnalysisRecordDB
from backend.services.report_generator import generate_crop_health_pdf

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/pdf/{field_id}")
def export_pdf_report(field_id: int, db: Session = Depends(get_db)):
    """Generate and stream an executive agricultural health PDF report."""
    field = db.query(FieldDB).filter(FieldDB.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found.")
        
    records = (
        db.query(AnalysisRecordDB)
        .filter(AnalysisRecordDB.field_id == field_id)
        .order_by(AnalysisRecordDB.scan_date.asc())
        .all()
    )
    
    if not records:
        raise HTTPException(status_code=400, detail="No satellite analysis records found for this field. Please run analysis first.")
        
    latest_record = records[-1]
    
    field_data = {
        "id": field.id,
        "name": field.name,
        "location_name": field.location_name,
        "crop_type": field.crop_type,
        "area_hectares": field.area_hectares,
        "boundary_geojson": field.boundary_geojson,
    }
    
    analysis_data = {
        "id": latest_record.id,
        "date": latest_record.scan_date,
        "growth_stage": latest_record.growth_stage,
        "cchs_score": latest_record.cchs_score,
        "classification": {
            "status": "GOOD" if latest_record.cchs_score >= 65 else "MODERATE",
            "label": latest_record.status_label,
            "color": "#10b981" if latest_record.cchs_score >= 65 else "#eab308" if latest_record.cchs_score >= 50 else "#ef4444",
        },
        "raw_indices": latest_record.raw_indices,
        "sub_scores": latest_record.sub_scores,
        "weights_used": latest_record.weights_used,
        "trend": latest_record.trend,
        "plain_language": latest_record.plain_language,
        "zone_distribution": latest_record.zone_distribution,
    }
    
    history_data = [
        {
            "date": r.scan_date,
            "growth_stage": r.growth_stage,
            "cchs_score": r.cchs_score,
            "status": r.status_label,
            "raw_indices": r.raw_indices,
        }
        for r in records
    ]
    
    pdf_bytes = generate_crop_health_pdf(field_data, analysis_data, history_data)
    
    clean_name = field.name.replace(" ", "_").replace("#", "").replace("/", "_")
    filename = f"CropVision_Report_{clean_name}_{latest_record.scan_date}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
