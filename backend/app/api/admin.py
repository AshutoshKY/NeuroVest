"""
Admin API endpoints for data ingestion.
"""
from fastapi import APIRouter, HTTPException
import logging
from app.services.data_ingestion import data_ingestion_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/ingest")
async def trigger_ingestion():
    """
    Trigger data ingestion from all configured sources.
    
    Returns:
        Ingestion report with results from all sources
    """
    try:
        logger.info("📥 Admin triggered data ingestion")
        
        report = await data_ingestion_service.run_ingestion_pipeline()
        
        return {
            "status": "success",
            "message": "Data ingestion completed",
            "report": report.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
