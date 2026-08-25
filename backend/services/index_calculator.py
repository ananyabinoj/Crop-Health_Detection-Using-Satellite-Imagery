"""
CropVision - Satellite Multispectral Index Calculation Engine

This module implements the mathematical calculation of essential vegetation and moisture
indices derived from Sentinel-2 MSI (MultiSpectral Instrument) Level-2A surface reflectance data.

Sentinel-2 Band Reference:
- Band 2 (Blue): 490 nm, 10m resolution (Atmospheric scattering reference)
- Band 3 (Green): 560 nm, 10m resolution (Vegetation peak reflectance in visible spectrum)
- Band 4 (Red): 665 nm, 10m resolution (Maximum chlorophyll absorption)
- Band 8 (NIR - Near Infrared): 842 nm, 10m resolution (High reflectance from leaf mesophyll structure)
- Band 11 (SWIR - Short-Wave Infrared): 1610 nm, 20m resolution (Strong liquid water absorption)

Formulas:
1. NDVI = (NIR - RED) / (NIR + RED)
   - Function: General biomass, photosynthetic activity, canopy density.
   - Sentinel-2: (B8 - B4) / (B8 + B4)
2. EVI = 2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1.0))
   - Function: Canopy structure, resistant to soil background and atmospheric haze.
   - Sentinel-2: 2.5 * ((B8 - B4) / (B8 + 6.0 * B4 - 7.5 * B2 + 1.0))
3. GCI = (NIR / GREEN) - 1.0
   - Function: Chlorophyll content, early nitrogen & nutrient deficiency indicator.
   - Sentinel-2: (B8 / B3) - 1.0
4. NDWI (Gao NDWI) = (NIR - SWIR) / (NIR + SWIR)
   - Function: Plant canopy liquid water content, cellular hydration, drought/irrigation stress.
   - Sentinel-2: (B8 - B11) / (B8 + B11)
"""

from typing import Union, Dict, Any
import numpy as np


def calculate_ndvi(nir: Union[float, np.ndarray], red: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Calculate Normalized Difference Vegetation Index (NDVI).
    
    Formula: (NIR - RED) / (NIR + RED)
    Sentinel-2 Bands: (B8 - B4) / (B8 + B4)
    
    Agronomic Significance:
    Healthy chlorophyll absorbs red light (~665nm) for photosynthesis while cell walls
    in healthy mesophyll tissue strongly reflect Near-Infrared (~842nm). NDVI quantifies
    this difference to evaluate overall canopy greenness, ground cover, and vigor.
    
    Range: [-1.0, 1.0]. Bare soil ~0.1-0.2; Sparse vegetation ~0.2-0.5; Dense canopy >0.6.
    """
    nir_arr = np.asarray(nir, dtype=np.float64)
    red_arr = np.asarray(red, dtype=np.float64)
    
    denominator = nir_arr + red_arr
    # Avoid zero division and negative non-physical noise
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = np.where(denominator > 1e-6, (nir_arr - red_arr) / denominator, 0.0)
    
    # Clip to valid mathematical bounds
    ndvi = np.clip(ndvi, -1.0, 1.0)
    if isinstance(nir, (int, float)) and isinstance(red, (int, float)):
        return float(ndvi.item())
    return ndvi


def calculate_evi(
    nir: Union[float, np.ndarray],
    red: Union[float, np.ndarray],
    blue: Union[float, np.ndarray],
    g: float = 2.5,
    c1: float = 6.0,
    c2: float = 7.5,
    l: float = 1.0,
) -> Union[float, np.ndarray]:
    """
    Calculate Enhanced Vegetation Index (EVI).
    
    Formula: G * ((NIR - RED) / (NIR + C1 * RED - C2 * BLUE + L))
    Sentinel-2 Bands: 2.5 * ((B8 - B4) / (B8 + 6.0 * B4 - 7.5 * B2 + 1.0))
    
    Agronomic Significance:
    EVI optimizes the vegetation signal with improved sensitivity in high biomass regions
    and improved vegetation monitoring through a de-coupling of the canopy background signal
    and a reduction in atmospheric aerosol influences using the Blue band.
    
    Range: [-1.0, 1.0] (typically 0.1 to 0.85 in agricultural fields).
    """
    nir_arr = np.asarray(nir, dtype=np.float64)
    red_arr = np.asarray(red, dtype=np.float64)
    blue_arr = np.asarray(blue, dtype=np.float64)
    
    denom = nir_arr + (c1 * red_arr) - (c2 * blue_arr) + l
    with np.errstate(divide="ignore", invalid="ignore"):
        evi = np.where(np.abs(denom) > 1e-6, g * ((nir_arr - red_arr) / denom), 0.0)
    
    evi = np.clip(evi, -1.0, 1.0)
    if isinstance(nir, (int, float)) and isinstance(red, (int, float)) and isinstance(blue, (int, float)):
        return float(evi.item())
    return evi


def calculate_gci(nir: Union[float, np.ndarray], green: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Calculate Green Chlorophyll Index (GCI).
    
    Formula: (NIR / GREEN) - 1.0
    Sentinel-2 Bands: (B8 / B3) - 1.0
    
    Agronomic Significance:
    Green reflectance (B3, 560nm) is inversely proportional to total chlorophyll concentration
    in leaves. GCI is highly sensitive to nitrogen status, leaf longevity, and subtle chlorosis
    well before visible symptoms appear to the human eye.
    
    Range: [0.0, 10.0+]. Stressed/low chlorophyll ~0.5-1.5; Healthy lush canopy ~3.0-7.0+.
    """
    nir_arr = np.asarray(nir, dtype=np.float64)
    green_arr = np.asarray(green, dtype=np.float64)
    
    with np.errstate(divide="ignore", invalid="ignore"):
        gci = np.where(green_arr > 1e-6, (nir_arr / green_arr) - 1.0, 0.0)
    
    # GCI can be negative in non-vegetated surfaces; clip lower bound at 0 for scoring
    gci = np.clip(gci, -1.0, 15.0)
    if isinstance(nir, (int, float)) and isinstance(green, (int, float)):
        return float(gci.item())
    return gci


def calculate_ndwi(nir: Union[float, np.ndarray], swir: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Calculate Normalized Difference Water Index (NDWI / Gao NDWI - Canopy Moisture).
    
    Formula: (NIR - SWIR) / (NIR + SWIR)
    Sentinel-2 Bands: (B8 - B11) / (B8 + B11)
    
    Agronomic Significance:
    Near-infrared reflectance is influenced by internal leaf structure, whereas shortwave
    infrared (SWIR, 1610nm) is strongly absorbed by liquid water in leaf cell vacuoles.
    NDWI directly reflects canopy water thickness and transpiration stress, making it the
    primary index for detecting irrigation deficits and drought vulnerability.
    
    Range: [-1.0, 1.0]. Dry/wilted canopy < 0.1; Adequately hydrated canopy ~0.2-0.55.
    """
    nir_arr = np.asarray(nir, dtype=np.float64)
    swir_arr = np.asarray(swir, dtype=np.float64)
    
    denominator = nir_arr + swir_arr
    with np.errstate(divide="ignore", invalid="ignore"):
        ndwi = np.where(denominator > 1e-6, (nir_arr - swir_arr) / denominator, 0.0)
    
    ndwi = np.clip(ndwi, -1.0, 1.0)
    if isinstance(nir, (int, float)) and isinstance(swir, (int, float)):
        return float(ndwi.item())
    return ndwi


def calculate_all_indices(
    b2_blue: Union[float, np.ndarray],
    b3_green: Union[float, np.ndarray],
    b4_red: Union[float, np.ndarray],
    b8_nir: Union[float, np.ndarray],
    b11_swir: Union[float, np.ndarray],
) -> Dict[str, Union[float, np.ndarray]]:
    """
    Compute all 4 core Sentinel-2 agricultural indices in a single pass.
    """
    return {
        "ndvi": calculate_ndvi(nir=b8_nir, red=b4_red),
        "evi": calculate_evi(nir=b8_nir, red=b4_red, blue=b2_blue),
        "gci": calculate_gci(nir=b8_nir, green=b3_green),
        "ndwi": calculate_ndwi(nir=b8_nir, swir=b11_swir),
    }
