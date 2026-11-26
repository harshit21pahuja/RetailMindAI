import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.alert import Alert
from backend.models.inventory import InventorySnapshot, StockAdjustment
from backend.models.product import Product, ShelfZone
from backend.models.sales import SalesTransaction
from backend.schemas.inventory import (
    DiscrepancyItem,
    DiscrepancyReportResponse,
    ReconciliationResult,
    ShelfAuditRequest,
    StockAdjustmentCreate,
    StockAdjustmentOut,
)


class InventoryFusionService:
    """Core Engine for Physical-vs-Digital Inventory Fusion & Discrepancy Reconciliation.

    Distinguishes:
      - S_vis: Visible shelf stock (observed by YOLO computer vision or shelf audit).
      - S_book: Digital inventory from POS sales and stock adjustment ledger.
      - S_back: Estimated backroom reserve: max(0, S_book - S_vis) or audited count.

    Statuses:
      - HEALTHY
      - LOW_STOCK
      - OUT_OF_STOCK
      - SHELF_RESTOCK_NEEDED
      - DISCREPANCY
      - POSSIBLE_SHRINKAGE
      - PHANTOM_STOCK
    """

    async def get_latest_snapshot(self, db: AsyncSession, sku: str) -> Optional[InventorySnapshot]:
        """Fetch the most recent inventory snapshot for a given SKU."""
        query = (
            select(InventorySnapshot)
            .where(InventorySnapshot.sku == sku)
            .order_by(desc(InventorySnapshot.recorded_at))
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def calculate_book_inventory(self, db: AsyncSession, sku: str) -> int:
        """Calculate digital book inventory based on latest snapshot and recent ledger deltas."""
        snap = await self.get_latest_snapshot(db, sku)
        if snap:
            return snap.book_inventory_qty

        # Fallback: if no snapshot exists, return 0
        return 0

    def calculate_backroom_inventory(
        self,
        book_qty: int,
        visible_qty: int,
        audited_backroom: Optional[int] = None,
    ) -> int:
        """Calculate backroom stock: S_back = max(0, S_book - S_vis) unless physically audited."""
        if audited_backroom is not None:
            return audited_backroom
        return max(0, book_qty - visible_qty)

    def calculate_discrepancy(
        self,
        visible_qty: int,
        book_qty: int,
        audited_backroom: Optional[int] = None,
    ) -> int:
        """Calculate discrepancy between physical observations and digital ledger."""
        if audited_backroom is not None:
            physical_total = visible_qty + audited_backroom
            return physical_total - book_qty
        
        # When only visible shelf is scanned
        if visible_qty > book_qty:
            return visible_qty - book_qty
        return 0

    async def get_recent_sales_velocity(
        self,
        db: AsyncSession,
        sku: str,
        days: int = 7,
    ) -> Tuple[float, int]:
        """Calculate recent sales velocity and unit volume."""
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = (
            select(
                func.coalesce(func.sum(SalesTransaction.quantity), 0).label("units_sold"),
                func.count(SalesTransaction.id).label("txn_count"),
            )
            .where(
                SalesTransaction.sku == sku,
                SalesTransaction.timestamp >= since_date,
            )
        )
        result = await db.execute(query)
        row = result.one()
        units_sold = row.units_sold
        daily_velocity = round(units_sold / max(1, days), 2)
        return daily_velocity, units_sold

    def classify_inventory_status(
        self,
        product: Product,
        visible_qty: int,
        book_qty: int,
        backroom_qty: int,
        discrepancy_qty: int,
        sales_last_3_days: int = 1,
    ) -> Tuple[str, Optional[Tuple[str, str, str, str]]]:
        """Determine inventory classification status and potential alert payload.

        Returns:
            (status_string, alert_tuple or None)
            where alert_tuple = (alert_type, severity, title, message)
        """
        # Threshold for low shelf occupancy
        shelf_threshold = max(3, int(product.shelf_capacity * 0.20))

        # 1. Total Out of Stock: Both visible shelf and book inventory are depleted
        if visible_qty == 0 and book_qty == 0:
            return (
                "OUT_OF_STOCK",
                (
                    "OUT_OF_STOCK",
                    "CRITICAL",
                    f"Out of Stock: {product.name}",
                    f"{product.name} is completely out of stock on shelves and in backroom.",
                ),
            )

        # 2. Phantom Stock / Ghost Inventory
        # Digital ledger indicates stock exists, but visible shelf is 0 with no reserve stock found
        if book_qty > 0 and visible_qty == 0 and backroom_qty == 0:
            return (
                "PHANTOM_STOCK",
                (
                    "PHANTOM_STOCK",
                    "CRITICAL",
                    f"Possible Phantom Stock Detected: {product.name}",
                    (
                        f"POS ledger indicates {book_qty} units in stock, but visible shelf is 0 "
                        f"with no reserve stock found. Possible shrinkage or unrecorded loss."
                    ),
                ),
            )

        # 3. Possible Shrinkage / Unrecorded Loss
        # Physical audit is strictly less than digital ledger
        if discrepancy_qty < 0:
            loss_units = abs(discrepancy_qty)
            est_financial_loss = round(loss_units * product.price, 2)
            return (
                "POSSIBLE_SHRINKAGE",
                (
                    "POSSIBLE_SHRINKAGE",
                    "CRITICAL",
                    f"Possible Inventory Shrinkage: {product.name}",
                    (
                        f"Physical count ({visible_qty + backroom_qty} units) is "
                        f"{loss_units} units below POS book inventory ({book_qty} units). "
                        f"Requires manual audit. Estimated potential loss: Rs. {est_financial_loss}."
                    ),
                ),
            )

        # 4. Low Stock: Total store stock at or below safety stock threshold
        if book_qty <= product.min_safety_stock:
            return (
                "LOW_STOCK",
                (
                    "LOW_STOCK",
                    "HIGH",
                    f"Low Stock Alert: {product.name}",
                    (
                        f"Total inventory ({book_qty} units) is at or below safety threshold "
                        f"({product.min_safety_stock} units)."
                    ),
                ),
            )

        # 5. Shelf Restock Needed: Overall store stock is adequate, but front shelf is depleted
        if visible_qty <= shelf_threshold and backroom_qty >= 3:
            return (
                "SHELF_RESTOCK_NEEDED",
                (
                    "SHELF_RESTOCK_NEEDED",
                    "HIGH",
                    f"Front Shelf Restock Needed: {product.name}",
                    (
                        f"Visible shelf has only {visible_qty} units (Capacity: {product.shelf_capacity}), "
                        f"while {backroom_qty} units are estimated in backroom storage."
                    ),
                ),
            )

        # 6. Unrecorded Overage / Discrepancy
        if discrepancy_qty > 0:
            return (
                "DISCREPANCY",
                (
                    "DISCREPANCY",
                    "MEDIUM",
                    f"Inventory Discrepancy Detected: {product.name}",
                    f"Physical count exceeds digital ledger by {discrepancy_qty} units. Inventory overage requires review.",
                ),
            )

        # 7. Healthy
        return ("HEALTHY", None)

    async def _create_alert_if_not_duplicate(
        self,
        db: AsyncSession,
        alert_type: str,
        severity: str,
        sku: str,
        title: str,
        message: str,
    ) -> bool:
        """Create alert only if an unresolved alert of the same type does not already exist."""
        existing_query = (
            select(Alert)
            .where(
                Alert.sku == sku,
                Alert.alert_type == alert_type,
                Alert.is_resolved.is_(False),
            )
            .limit(1)
        )
        existing = (await db.execute(existing_query)).scalar_one_or_none()
        if existing:
            return False  # Deduplicated

        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            sku=sku,
            title=title,
            message=message,
            is_resolved=False,
        )
        db.add(alert)
        return True

    async def create_inventory_snapshot(
        self,
        db: AsyncSession,
        sku: str,
        visible_qty: int,
        book_qty: int,
        backroom_qty: int,
        discrepancy_qty: int,
        status: str,
        audit_source: str = "MANUAL_AUDIT",
        confidence_score: float = 1.0,
    ) -> InventorySnapshot:
        """Persist an inventory audit snapshot."""
        now = datetime.now(timezone.utc)
        snapshot = InventorySnapshot(
            sku=sku,
            recorded_at=now,
            visible_shelf_qty=visible_qty,
            book_inventory_qty=book_qty,
            estimated_backroom_qty=backroom_qty,
            discrepancy_qty=discrepancy_qty,
            audit_source=audit_source,
            status=status,
            confidence_score=confidence_score,
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        return snapshot

    async def reconcile_product(
        self,
        db: AsyncSession,
        product: Product,
        visible_qty: int,
        audited_backroom_qty: Optional[int] = None,
        audit_source: str = "MANUAL_AUDIT",
    ) -> ReconciliationResult:
        """Run fusion analysis on an individual product, create snapshot & dispatch alerts."""
        current_book_qty = await self.calculate_book_inventory(db, product.sku)
        backroom_qty = self.calculate_backroom_inventory(current_book_qty, visible_qty, audited_backroom_qty)
        discrepancy_qty = self.calculate_discrepancy(visible_qty, current_book_qty, audited_backroom_qty)

        # Recent sales velocity for phantom stock check
        _, sales_last_3_days = await self.get_recent_sales_velocity(db, product.sku, days=3)

        status, alert_info = self.classify_inventory_status(
            product=product,
            visible_qty=visible_qty,
            book_qty=current_book_qty,
            backroom_qty=backroom_qty,
            discrepancy_qty=discrepancy_qty,
            sales_last_3_days=sales_last_3_days,
        )

        alerts_triggered: List[str] = []
        if alert_info:
            alert_type, severity, title, message = alert_info
            created = await self._create_alert_if_not_duplicate(
                db=db,
                alert_type=alert_type,
                severity=severity,
                sku=product.sku,
                title=title,
                message=message,
            )
            if created:
                alerts_triggered.append(alert_type)

        # Auto-resolve previous alerts if product is now Healthy and well stocked
        if status == "HEALTHY" and visible_qty >= int(product.shelf_capacity * 0.5):
            res_query = (
                select(Alert)
                .where(
                    Alert.sku == product.sku,
                    Alert.alert_type.in_(["SHELF_RESTOCK_NEEDED", "SHELF_EMPTY", "OUT_OF_STOCK"]),
                    Alert.is_resolved.is_(False),
                )
            )
            prev_alerts = (await db.execute(res_query)).scalars().all()
            for prev in prev_alerts:
                prev.is_resolved = True

        # Save Snapshot
        await self.create_inventory_snapshot(
            db=db,
            sku=product.sku,
            visible_qty=visible_qty,
            book_qty=current_book_qty,
            backroom_qty=backroom_qty,
            discrepancy_qty=discrepancy_qty,
            status=status,
            audit_source=audit_source,
        )

        return ReconciliationResult(
            sku=product.sku,
            product_name=product.name,
            visible_shelf_qty=visible_qty,
            book_inventory_qty=current_book_qty,
            estimated_backroom_qty=backroom_qty,
            discrepancy_qty=discrepancy_qty,
            status=status,
            alerts_triggered=alerts_triggered,
        )

    async def reconcile_inventory(
        self,
        db: AsyncSession,
        target_sku: Optional[str] = None,
    ) -> List[ReconciliationResult]:
        """Perform full store or SKU-specific inventory reconciliation."""
        query = select(Product).where(Product.is_active.is_(True))
        if target_sku:
            query = query.where(Product.sku == target_sku)
        query = query.order_by(Product.category, Product.name)

        products = (await db.execute(query)).scalars().all()
        results: List[ReconciliationResult] = []

        for prod in products:
            latest_snap = await self.get_latest_snapshot(db, prod.sku)
            visible_qty = latest_snap.visible_shelf_qty if latest_snap else 0
            
            res = await self.reconcile_product(
                db=db,
                product=prod,
                visible_qty=visible_qty,
                audit_source="STORE_RECONCILIATION",
            )
            results.append(res)

        return results

    async def record_stock_adjustment(
        self,
        db: AsyncSession,
        payload: StockAdjustmentCreate,
    ) -> StockAdjustmentOut:
        """Process stock adjustments (supplier deliveries, damaged items, write-offs)."""
        prod_query = select(Product).where(Product.sku == payload.sku)
        product = (await db.execute(prod_query)).scalar_one_or_none()
        if not product:
            raise ValueError(f"Product with SKU '{payload.sku}' not found.")

        # Create adjustment record
        adjustment = StockAdjustment(
            sku=payload.sku,
            adjustment_qty=payload.adjustment_qty,
            adjustment_type=payload.adjustment_type,
            reason=payload.reason,
            performed_by=payload.performed_by,
        )
        db.add(adjustment)

        latest_snap = await self.get_latest_snapshot(db, payload.sku)
        prev_book = latest_snap.book_inventory_qty if latest_snap else 0
        prev_vis = latest_snap.visible_shelf_qty if latest_snap else 0

        new_book = max(0, prev_book + payload.adjustment_qty)
        new_backroom = max(0, new_book - prev_vis)

        status, _ = self.classify_inventory_status(
            product=product,
            visible_qty=prev_vis,
            book_qty=new_book,
            backroom_qty=new_backroom,
            discrepancy_qty=0,
        )

        await self.create_inventory_snapshot(
            db=db,
            sku=payload.sku,
            visible_qty=prev_vis,
            book_qty=new_book,
            backroom_qty=new_backroom,
            discrepancy_qty=0,
            status=status,
            audit_source=f"ADJUSTMENT_{payload.adjustment_type}",
        )

        await db.refresh(adjustment)
        return StockAdjustmentOut.model_validate(adjustment)

    async def generate_discrepancy_report(self, db: AsyncSession) -> DiscrepancyReportResponse:
        """Generate actionable discrepancy intelligence report across the store."""
        prod_query = select(Product).where(Product.is_active.is_(True)).order_by(Product.category, Product.name)
        products = (await db.execute(prod_query)).scalars().all()

        items: List[DiscrepancyItem] = []
        shelf_restock_count = 0
        shrinkage_count = 0
        phantom_stock_count = 0
        total_potential_loss = 0.0

        for prod in products:
            snap = await self.get_latest_snapshot(db, prod.sku)
            if not snap:
                continue

            vis = snap.visible_shelf_qty
            book = snap.book_inventory_qty
            backroom = snap.estimated_backroom_qty
            disc = snap.discrepancy_qty
            status = snap.status

            if status == "SHELF_RESTOCK_NEEDED":
                shelf_restock_count += 1
                items.append(
                    DiscrepancyItem(
                        sku=prod.sku,
                        name=prod.name,
                        category=prod.category,
                        discrepancy_type="SHELF_RESTOCK_NEEDED",
                        severity="HIGH",
                        visible_shelf_qty=vis,
                        book_inventory_qty=book,
                        estimated_backroom_qty=backroom,
                        discrepancy_qty=0,
                        estimated_financial_loss=0.0,
                        explanation=f"Visible shelf has only {vis} units, but {backroom} units are stored in backroom.",
                        recommended_action=f"Dispatch floor staff to restock {min(backroom, prod.shelf_capacity - vis)} units from backroom to shelf.",
                    )
                )

            elif status in ["POSSIBLE_SHRINKAGE", "SHRINKAGE"] or disc < 0:
                shrinkage_count += 1
                loss_val = round(abs(disc) * prod.price, 2)
                total_potential_loss += loss_val
                items.append(
                    DiscrepancyItem(
                        sku=prod.sku,
                        name=prod.name,
                        category=prod.category,
                        discrepancy_type="POSSIBLE_SHRINKAGE",
                        severity="CRITICAL",
                        visible_shelf_qty=vis,
                        book_inventory_qty=book,
                        estimated_backroom_qty=backroom,
                        discrepancy_qty=disc,
                        estimated_financial_loss=loss_val,
                        explanation=f"Possible shrinkage: {abs(disc)} units missing between POS ledger and physical audit. Requires manual audit.",
                        recommended_action="Conduct recount, review security logs, and record shrinkage write-off if unrecovered.",
                    )
                )

            elif status == "PHANTOM_STOCK":
                phantom_stock_count += 1
                loss_val = round(book * prod.price, 2)
                total_potential_loss += loss_val
                items.append(
                    DiscrepancyItem(
                        sku=prod.sku,
                        name=prod.name,
                        category=prod.category,
                        discrepancy_type="PHANTOM_STOCK",
                        severity="CRITICAL",
                        visible_shelf_qty=vis,
                        book_inventory_qty=book,
                        estimated_backroom_qty=backroom,
                        discrepancy_qty=-book,
                        estimated_financial_loss=loss_val,
                        explanation=f"Possible phantom stock: Book ledger shows {book} units, but visible shelf is 0 and recent sales halted.",
                        recommended_action="Inspect backroom storage and adjust book inventory to 0 to unblock supplier replenishment orders.",
                    )
                )

        return DiscrepancyReportResponse(
            total_discrepancies=len(items),
            shelf_restock_count=shelf_restock_count,
            shrinkage_count=shrinkage_count,
            phantom_stock_count=phantom_stock_count,
            total_potential_loss=round(total_potential_loss, 2),
            items=items,
        )

    async def fuse_vision_counts(
        self,
        db: AsyncSession,
        class_counts: Dict[str, int],
        zone_code: Optional[str] = None,
    ) -> List[ReconciliationResult]:
        """Map YOLO detection counts to retail SKUs and update store inventory snapshots."""
        results: List[ReconciliationResult] = []

        if zone_code:
            zone_query = select(ShelfZone).where(ShelfZone.zone_code == zone_code)
            zone = (await db.execute(zone_query)).scalar_one_or_none()
            if zone:
                prod_query = select(Product).where(Product.sku == zone.target_sku)
                prod = (await db.execute(prod_query)).scalar_one_or_none()
                if prod:
                    detected_units = sum(class_counts.values())
                    res = await self.reconcile_product(
                        db=db,
                        product=prod,
                        visible_qty=detected_units,
                        audit_source="VISION_YOLO_ZONE",
                    )
                    results.append(res)
                    return results

        prod_query = select(Product).where(Product.is_active.is_(True))
        all_prods = (await db.execute(prod_query)).scalars().all()

        for prod in all_prods:
            matched_count = None
            for detected_class, count in class_counts.items():
                cls_lower = detected_class.lower()
                if (
                    cls_lower in prod.name.lower()
                    or cls_lower in prod.brand.lower()
                    or cls_lower in prod.sku.lower()
                ):
                    matched_count = count
                    break

            if matched_count is not None:
                res = await self.reconcile_product(
                    db=db,
                    product=prod,
                    visible_qty=matched_count,
                    audit_source="VISION_YOLO_DETECTION",
                )
                results.append(res)

        return results


inventory_service = InventoryFusionService()
