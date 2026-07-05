"""
lab_features.py — API Router for feature research and score analyzer.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.lab.feature_analyzer import (
    permutation_importance,
    correlation_matrix,
    mutual_information,
    variance_inflation_factor,
    shap_proxy,
    feature_drift,
    feature_redundancy,
    feature_stability,
    full_feature_analysis,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab/features", tags=["lab-features"])


@router.get("/importance")
async def get_importance():
    """Retrieve permutation feature importance across pre-computed scores."""
    try:
        return permutation_importance()
    except Exception as e:
        logger.error(f"Error calculating feature importance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlation")
async def get_correlation():
    """Retrieve pairwise Pearson correlation matrix for all features and composite target."""
    try:
        return correlation_matrix()
    except Exception as e:
        logger.error(f"Error calculating correlation matrix: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mutual-information")
async def get_mutual_information():
    """Retrieve mutual information scores using histogram binning."""
    try:
        return mutual_information()
    except Exception as e:
        logger.error(f"Error calculating mutual information: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vif")
async def get_vif():
    """Retrieve Variance Inflation Factor (VIF) scores to detect multicollinearity."""
    try:
        return variance_inflation_factor()
    except Exception as e:
        logger.error(f"Error calculating VIF scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shap-proxy")
async def get_shap_proxy():
    """Retrieve SHAP approximation using linear marginal contribution."""
    try:
        return shap_proxy()
    except Exception as e:
        logger.error(f"Error calculating SHAP proxy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift")
async def get_drift():
    """Track mean/std score shifts over historical analysis times."""
    try:
        return feature_drift()
    except Exception as e:
        logger.error(f"Error calculating feature drift: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/redundancy")
async def get_redundancy():
    """Cluster features into redundancy groups where absolute correlation >= 0.85."""
    try:
        return feature_redundancy()
    except Exception as e:
        logger.error(f"Error clustering feature redundancy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stability")
async def get_stability():
    """Get coefficient of variation (CV) stability metrics for feature columns."""
    try:
        return feature_stability()
    except Exception as e:
        logger.error(f"Error calculating feature stability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/full-analysis")
async def get_full_analysis():
    """Get consolidated full feature analysis result containing all metrics."""
    try:
        return full_feature_analysis()
    except Exception as e:
        logger.error(f"Error executing full feature analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

