"""
CropVision - Data Models & Schemas

Defines SQLAlchemy ORM models and Pydantic validation schemas.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend.database import Base


# =========================================================
# SQLAlchemy ORM Models
# =========================================================

class FieldDB(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    location_name = Column(String(120), nullable=True)
    crop_type = Column(String(80), default="Corn")
    area_hectares = Column(Float, default=10.0)
    boundary_geojson = Column(JSON, nullable=False)
    current_growth_stage = Column(String(50), default="VEGETATIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis_records = relationship(
        "AnalysisRecordDB",
        back_populates="field",
        cascade="all, delete-orphan",
        order_by="AnalysisRecordDB.scan_date.asc()",
    )


class AnalysisRecordDB(Base):
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=False)
    scan_date = Column(String(30), nullable=False)
    growth_stage = Column(String(50), default="VEGETATIVE")
    cchs_score = Column(Float, nullable=False)
    status_label = Column(String(50), default="Good")
    
    # JSON serializations for rich structured data
    raw_indices = Column(JSON, nullable=False)        # {"ndvi": 0.72, "evi": 0.51, ...}
    sub_scores = Column(JSON, nullable=False)         # {"ndvi_score": 82.5, ...}
    weights_used = Column(JSON, nullable=False)       # {"ndvi": 0.35, "evi": 0.25, ...}
    bands = Column(JSON, nullable=True)               # {"B2": 0.04, "B3": 0.08, ...}
    trend = Column(JSON, nullable=True)               # {"trend_status": "DECLINING", ...}
    plain_language = Column(JSON, nullable=True)      # {"headline": "...", "action_items": [...]}
    spatial_grid = Column(JSON, nullable=True)        # GeoJSON FeatureCollection of 10m cells
    zone_distribution = Column(JSON, nullable=True)   # {"healthy_pct": 74.2, ...}
    quadrants = Column(JSON, nullable=True)           # Quadrant stats
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("FieldDB", back_populates="analysis_records")


class GrowthStagePresetDB(Base):
    __tablename__ = "growth_stage_presets"

    id = Column(Integer, primary_key=True, index=True)
    stage_key = Column(String(50), unique=True, nullable=False)
    stage_label = Column(String(100), nullable=False)
    ndvi_weight = Column(Float, default=0.25)
    evi_weight = Column(Float, default=0.25)
    gci_weight = Column(Float, default=0.25)
    ndwi_weight = Column(Float, default=0.25)
    description = Column(Text, default="")


# =========================================================
# Pydantic Request & Response Schemas
# =========================================================

class FieldCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    location_name: Optional[str] = "Farm Parcel"
    crop_type: str = Field(default="Corn")
    current_growth_stage: str = Field(default="VEGETATIVE")
    boundary_geojson: Dict[str, Any] = Field(..., description="GeoJSON Polygon geometry or Feature")


from pydantic import BaseModel, Field, ConfigDict

class FieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    location_name: Optional[str]
    crop_type: str
    area_hectares: float
    current_growth_stage: str
    boundary_geojson: Dict[str, Any]
    created_at: datetime
    record_count: Optional[int] = 0
    latest_cchs: Optional[float] = None
    latest_status: Optional[str] = None


class CustomWeightsInput(BaseModel):
    ndvi: float = Field(..., ge=0.0, le=1.0)
    evi: float = Field(..., ge=0.0, le=1.0)
    gci: float = Field(..., ge=0.0, le=1.0)
    ndwi: float = Field(..., ge=0.0, le=1.0)


class RunAnalysisRequest(BaseModel):
    field_id: int
    scan_date: Optional[str] = None
    growth_stage: Optional[str] = None
    custom_weights: Optional[CustomWeightsInput] = None
    simulate_scenario: Optional[str] = None  # e.g., "WATER_DEFICIT_NE", "NITROGEN_DEFICIT_S", "HIGH_VIGOR_UNIFORM"


class StageConfigUpdate(BaseModel):
    stage_key: str
    stage_label: str
    ndvi_weight: float
    evi_weight: float
    gci_weight: float
    ndwi_weight: float
    description: Optional[str] = ""
