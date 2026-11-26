from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """System health check and database connectivity verification."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "RetailMind AI Engine",
        "version": "0.1.0",
        "database": db_status,
    }
