from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.alert import Alert
from backend.schemas.alert import AlertOut, AlertResolve

router = APIRouter(prefix="/alerts", tags=["Store Alerts"])


@router.get("/active", response_model=List[AlertOut])
async def list_active_alerts(db: AsyncSession = Depends(get_db)):
    """Retrieve active unresolved store alerts (out-of-stock, empty shelves, discrepancies)."""
    query = (
        select(Alert)
        .where(Alert.is_resolved.is_(False))
        .order_by(desc(Alert.created_at))
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{alert_id}/resolve", response_model=AlertOut)
async def resolve_alert(
    alert_id: int,
    payload: AlertResolve,
    db: AsyncSession = Depends(get_db),
):
    """Mark an alert as resolved after shelf restocking or physical inventory audit."""
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found")

    alert.is_resolved = payload.is_resolved
    await db.commit()
    await db.refresh(alert)
    return alert
