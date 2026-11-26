from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.inventory import InventorySnapshot
from backend.models.product import Product
from backend.schemas.inventory import (
    DiscrepancyReportResponse,
    InventoryOverviewResponse,
    InventorySnapshotOut,
    ProductInventoryStatus,
    ReconciliationResult,
    ShelfAuditRequest,
    StockAdjustmentCreate,
    StockAdjustmentOut,
    VisionInventoryFusionRequest,
)
from backend.services.inventory_service import inventory_service

router = APIRouter(prefix="/inventory", tags=["Inventory Intelligence"])


@router.get("/status", response_model=InventoryOverviewResponse)
async def get_inventory_status(db: AsyncSession = Depends(get_db)):
    """Retrieve full store inventory status fusing visible shelf stock with POS book stock."""
    prod_query = select(Product).where(Product.is_active.is_(True)).order_by(Product.category, Product.name)
    prod_result = await db.execute(prod_query)
    products = prod_result.scalars().all()

    items: List[ProductInventoryStatus] = []
    healthy_count = 0
    low_stock_count = 0
    out_of_stock_count = 0
    restock_needed_count = 0
    shrinkage_count = 0
    phantom_stock_count = 0
    discrepancy_count = 0
    total_store_value = 0.0

    for prod in products:
        latest_snap = await inventory_service.get_latest_snapshot(db, prod.sku)

        visible_qty = latest_snap.visible_shelf_qty if latest_snap else 0
        book_qty = latest_snap.book_inventory_qty if latest_snap else 0
        backroom_qty = latest_snap.estimated_backroom_qty if latest_snap else max(0, book_qty - visible_qty)
        discrepancy_qty = latest_snap.discrepancy_qty if latest_snap else 0
        status_val = latest_snap.status if latest_snap else "UNKNOWN"
        last_audit = latest_snap.recorded_at if latest_snap else None

        fill_pct = round((visible_qty / max(1, prod.shelf_capacity)) * 100, 1)
        sku_val = round(book_qty * prod.price, 2)
        total_store_value += sku_val

        if status_val == "HEALTHY":
            healthy_count += 1
        elif status_val == "LOW_STOCK":
            low_stock_count += 1
        elif status_val == "OUT_OF_STOCK":
            out_of_stock_count += 1
        elif status_val == "SHELF_RESTOCK_NEEDED":
            restock_needed_count += 1
            discrepancy_count += 1
        elif status_val in ["POSSIBLE_SHRINKAGE", "SHRINKAGE"]:
            shrinkage_count += 1
            discrepancy_count += 1
        elif status_val == "PHANTOM_STOCK":
            phantom_stock_count += 1
            discrepancy_count += 1
        elif discrepancy_qty != 0 or status_val == "DISCREPANCY":
            discrepancy_count += 1

        items.append(
            ProductInventoryStatus(
                sku=prod.sku,
                name=prod.name,
                category=prod.category,
                price=prod.price,
                shelf_capacity=prod.shelf_capacity,
                threshold=prod.min_safety_stock,
                visible_shelf_qty=visible_qty,
                book_inventory_qty=book_qty,
                estimated_backroom_qty=backroom_qty,
                discrepancy_qty=discrepancy_qty,
                shelf_fill_pct=fill_pct,
                inventory_value=sku_val,
                status=status_val,
                brand=prod.brand,
                image_url=prod.image_url,
                last_checked=last_audit,
                last_audit_time=last_audit,
            )
        )

    return InventoryOverviewResponse(
        total_skus=len(products),
        healthy_count=healthy_count,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        restock_needed_count=restock_needed_count,
        shrinkage_count=shrinkage_count,
        phantom_stock_count=phantom_stock_count,
        discrepancy_count=discrepancy_count,
        inventory_value=round(total_store_value, 2),
        items=items,
    )


@router.post("/reconcile", response_model=List[ReconciliationResult])
async def reconcile_store_inventory(
    sku: Optional[str] = Query(None, description="Optional target SKU to reconcile"),
    db: AsyncSession = Depends(get_db),
):
    """Run full physical-vs-digital inventory reconciliation across the store."""
    results = await inventory_service.reconcile_inventory(db=db, target_sku=sku)
    return results


@router.post("/audit", response_model=ReconciliationResult)
async def submit_shelf_audit(
    payload: ShelfAuditRequest,
    db: AsyncSession = Depends(get_db),
):
    """Conduct physical shelf audit and trigger discrepancy reconciliation."""
    prod_query = select(Product).where(Product.sku == payload.sku)
    product = (await db.execute(prod_query)).scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with SKU '{payload.sku}' not found.",
        )

    result = await inventory_service.reconcile_product(
        db=db,
        product=product,
        visible_qty=payload.visible_shelf_qty,
        audited_backroom_qty=payload.audited_backroom_qty,
        audit_source=payload.audit_source,
    )
    return result


@router.post("/adjust", response_model=StockAdjustmentOut)
async def record_stock_adjustment(
    payload: StockAdjustmentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Record supplier delivery or shrinkage write-off, adjusting digital book inventory."""
    try:
        adjustment = await inventory_service.record_stock_adjustment(db=db, payload=payload)
        return adjustment
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))


@router.get("/discrepancies", response_model=DiscrepancyReportResponse)
async def get_discrepancies(db: AsyncSession = Depends(get_db)):
    """Generate discrepancy intelligence report (shrinkage, phantom stock, shelf restock needs)."""
    return await inventory_service.generate_discrepancy_report(db)


@router.post("/fuse-vision", response_model=List[ReconciliationResult])
async def fuse_vision_counts(
    payload: VisionInventoryFusionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Fuse YOLO object detection counts into store inventory snapshots."""
    results = await inventory_service.fuse_vision_counts(
        db=db,
        class_counts=payload.class_counts,
        zone_code=payload.zone_code,
    )
    return results


@router.get("/history", response_model=List[InventorySnapshotOut])
async def list_inventory_history(
    sku: Optional[str] = Query(None, description="Optional SKU filter"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve paginated inventory audit snapshots, optionally filtered by SKU."""
    query = select(InventorySnapshot)
    if sku:
        query = query.where(InventorySnapshot.sku == sku)
    query = query.order_by(desc(InventorySnapshot.recorded_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/history/{sku}", response_model=List[InventorySnapshotOut])
async def get_inventory_history_by_sku(
    sku: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve historical inventory audit snapshots for a specific SKU."""
    query = (
        select(InventorySnapshot)
        .where(InventorySnapshot.sku == sku)
        .order_by(desc(InventorySnapshot.recorded_at))
        .limit(limit)
    )
    result = await db.execute(query)
    snapshots = result.scalars().all()
    if not snapshots:
        raise HTTPException(status_code=404, detail=f"No inventory snapshots found for SKU '{sku}'")
    return snapshots
