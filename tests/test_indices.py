"""
Unit tests for Sentinel-2 Multispectral Index Calculations
"""

import pytest
import numpy as np
from backend.services.index_calculator import (
    calculate_ndvi,
    calculate_evi,
    calculate_gci,
    calculate_ndwi,
    calculate_all_indices,
)


def test_ndvi_bounds_and_values():
    # Dense healthy vegetation (High NIR, Low Red)
    val = calculate_ndvi(nir=0.55, red=0.05)
    assert 0.80 <= val <= 0.85
    
    # Bare soil (Moderate NIR, Moderate Red)
    soil_val = calculate_ndvi(nir=0.20, red=0.18)
    assert 0.0 <= soil_val <= 0.10
    
    # Water / negative values
    water_val = calculate_ndvi(nir=0.02, red=0.08)
    assert water_val < 0.0
    
    # Zero division safeguard
    zero_val = calculate_ndvi(nir=0.0, red=0.0)
    assert zero_val == 0.0


def test_evi_calculation():
    # Healthy canopy: NIR=0.50, RED=0.04, BLUE=0.03
    val = calculate_evi(nir=0.50, red=0.04, blue=0.03)
    assert 0.60 <= val <= 0.85
    
    # Zero division safeguard
    zero_evi = calculate_evi(nir=0.0, red=0.0, blue=0.0)
    assert -1.0 <= zero_evi <= 1.0


def test_gci_calculation():
    # High chlorophyll: NIR=0.50, GREEN=0.08 -> GCI = (0.50 / 0.08) - 1 = 5.25
    val = calculate_gci(nir=0.50, green=0.08)
    assert pytest.approx(val, 0.01) == 5.25
    
    # Low chlorophyll / chlorosis: NIR=0.30, GREEN=0.15 -> GCI = (0.30/0.15)-1 = 1.0
    val_low = calculate_gci(nir=0.30, green=0.15)
    assert pytest.approx(val_low, 0.01) == 1.0
    
    # Zero division safeguard
    zero_gci = calculate_gci(nir=0.5, green=0.0)
    assert zero_gci >= 0.0


def test_ndwi_water_stress_sensitivity():
    # Well-hydrated canopy (High NIR 0.50, Low SWIR 0.15)
    hydrated = calculate_ndwi(nir=0.50, swir=0.15)
    assert 0.45 <= hydrated <= 0.60
    
    # Water-stressed / drought canopy (Lower NIR 0.35, Higher SWIR 0.28)
    stressed = calculate_ndwi(nir=0.35, swir=0.28)
    assert 0.05 <= stressed <= 0.15
    assert hydrated > stressed


def test_numpy_array_index_calculations():
    nir = np.array([0.50, 0.40, 0.10])
    red = np.array([0.05, 0.08, 0.12])
    green = np.array([0.08, 0.10, 0.10])
    blue = np.array([0.03, 0.04, 0.08])
    swir = np.array([0.15, 0.20, 0.25])
    
    res = calculate_all_indices(b2_blue=blue, b3_green=green, b4_red=red, b8_nir=nir, b11_swir=swir)
    
    assert len(res["ndvi"]) == 3
    assert len(res["evi"]) == 3
    assert len(res["gci"]) == 3
    assert len(res["ndwi"]) == 3
    assert res["ndvi"][0] > res["ndvi"][2]
