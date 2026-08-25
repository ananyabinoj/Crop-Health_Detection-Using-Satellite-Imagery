"""
Integration tests for FastAPI endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.seed_data import seed_database

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()


def test_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["product"] == "CropVision"
    
    h_res = client.get("/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "healthy"


def test_get_fields():
    res = client.get("/api/fields")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 4
    first_field = data[0]
    assert "name" in first_field
    assert "boundary_geojson" in first_field
    assert first_field["latest_cchs"] is not None


def test_get_growth_stages():
    res = client.get("/api/analysis/growth-stages")
    assert res.status_code == 200
    stages = res.json()
    assert len(stages) >= 5
    stage_keys = [s["stage_key"] for s in stages]
    assert "FLOWERING" in stage_keys
    assert "VEGETATIVE" in stage_keys


def test_run_analysis_endpoint():
    # Fetch first field
    fields = client.get("/api/fields").json()
    field_id = fields[0]["id"]
    
    payload = {
        "field_id": field_id,
        "growth_stage": "FLOWERING",
        "simulate_scenario": "WATER_DEFICIT_NE",
    }
    res = client.post("/api/analysis/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    
    assert "cchs_score" in data
    assert "classification" in data
    assert "sub_scores" in data
    assert "raw_indices" in data
    assert "trend" in data
    assert "plain_language" in data
    assert "spatial_grid" in data
    assert data["plain_language"]["headline"] is not None
    assert len(data["plain_language"]["action_items"]) >= 3


def test_field_history_endpoint():
    fields = client.get("/api/fields").json()
    field_id = fields[0]["id"]
    
    res = client.get(f"/api/history/{field_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["total_scans"] >= 4
    assert len(data["timeline"]) >= 4


def test_pdf_report_export_endpoint():
    fields = client.get("/api/fields").json()
    field_id = fields[0]["id"]
    
    res = client.get(f"/api/reports/pdf/{field_id}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 1000  # Non-empty PDF binary
    assert res.content[:4] == b"%PDF"
