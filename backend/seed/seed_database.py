"""Database initialization and seeding script for RetailMind AI.

Generates 15 core retail products, shelf zones, initial inventory snapshots,
initial operational alerts, and 90 days of realistic daily POS sales transactions.
"""

import math
import random
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import select
from backend.database import SyncSessionLocal, init_db_sync
from backend.models.product import Product, ShelfZone
from backend.models.inventory import InventorySnapshot
from backend.models.sales import SalesTransaction
from backend.models.alert import Alert
from backend.seed.catalog_data import SEED_PRODUCTS


# Daily baseline sales velocity per SKU (mean units sold per day)
DAILY_BASELINE_VELOCITY = {
    "BEV-COKE-500": 10.0,
    "BEV-PEPSI-500": 8.5,
    "BEV-SPRITE-500": 7.0,
    "BEV-FROOTI-250": 12.0,
    "SNK-LAYS-CLASSIC": 14.0,
    "SNK-LAYS-MASALA": 16.0,
    "SNK-KURKURE-MM": 13.0,
    "SNK-HALDIRAM-BHUJIA": 5.0,
    "FOD-MAGGI-MASALA": 22.0,
    "FOD-YIPPEE-NOODLE": 12.0,
    "BSC-PARLEG-250": 20.0,
    "BSC-GOODDAY-200": 11.0,
    "CHO-DAIRYMILK-50": 15.0,
    "DAI-AMUL-MILK-500": 26.0,
    "DAI-AMUL-BUTTER-100": 6.5,
}

PAYMENT_METHODS = ["UPI", "UPI", "UPI", "UPI", "CASH", "CASH", "CARD"]


def generate_sales_transactions(
    db_session,
    products: List[dict],
    days: int = 90
) -> int:
    """Generate realistic sales transactions over the past `days` days."""
    random.seed(42)  # Deterministic realistic simulation
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    total_txns = 0

    sales_records = []

    for day_offset in range(days):
        current_day = start_date + timedelta(days=day_offset)
        weekday = current_day.weekday()  # 0=Monday, 6=Sunday

        # Weekend rush multiplier (Fri=1.2, Sat=1.35, Sun=1.4)
        weekend_multiplier = 1.0
        if weekday == 4:
            weekend_multiplier = 1.20
        elif weekday == 5:
            weekend_multiplier = 1.35
        elif weekday == 6:
            weekend_multiplier = 1.40

        for item in products:
            sku = item["sku"]
            price = item["price"]
            base_velocity = DAILY_BASELINE_VELOCITY.get(sku, 10.0)

            # Expected demand for this day
            expected_units = base_velocity * weekend_multiplier
            # Slight seasonal sine wave oscillation
            trend_factor = 1.0 + 0.15 * math.sin(day_offset / 12.0)
            target_units = max(1, int(random.gauss(expected_units * trend_factor, 2.5)))

            # Distribute into individual customer basket transactions
            units_remaining = target_units
            while units_remaining > 0:
                # Customer buys 1, 2, 3 or rarely 4 of an item
                basket_qty = min(units_remaining, random.choices([1, 2, 3, 4], weights=[0.55, 0.30, 0.10, 0.05])[0])
                units_remaining -= basket_qty

                # Store shopping hours between 8:30 AM and 10:15 PM
                hour = random.randint(8, 21)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                txn_time = current_day.replace(hour=hour, minute=minute, second=second)

                txn_id = f"TXN-{txn_time.strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
                payment = random.choice(PAYMENT_METHODS)

                sales_records.append(
                    SalesTransaction(
                        transaction_id=txn_id,
                        sku=sku,
                        quantity=basket_qty,
                        unit_price=price,
                        total_amount=round(basket_qty * price, 2),
                        timestamp=txn_time,
                        payment_method=payment,
                    )
                )
                total_txns += 1

                # Batch commit every 1000 records to keep memory lean
                if len(sales_records) >= 1000:
                    db_session.bulk_save_objects(sales_records)
                    db_session.commit()
                    sales_records = []

    if sales_records:
        db_session.bulk_save_objects(sales_records)
        db_session.commit()

    return total_txns


def seed_all() -> dict:
    """Run full synchronous database seeding."""
    print("Initializing database tables...")
    init_db_sync()

    session = SyncSessionLocal()
    try:
        # Check if products already exist
        existing_count = session.query(Product).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} products. Skipping duplicate seeding.")
            return {"status": "already_seeded", "products_count": existing_count}

        print(f"Seeding {len(SEED_PRODUCTS)} core retail SKUs...")
        now = datetime.now(timezone.utc)

        for item in SEED_PRODUCTS:
            product = Product(
                sku=item["sku"],
                name=item["name"],
                brand=item["brand"],
                category=item["category"],
                price=item["price"],
                unit_cost=item["unit_cost"],
                lead_time_days=item["lead_time_days"],
                min_safety_stock=item["min_safety_stock"],
                shelf_capacity=item["shelf_capacity"],
                package_type=item["package_type"],
                barcode=item["barcode"],
                image_url=item["image_url"],
                is_active=True,
            )
            session.add(product)
            session.flush()

            # Create ShelfZone planogram definition
            shelf_zone = ShelfZone(
                zone_code=item["zone_code"],
                camera_id="CAM-01",
                target_sku=item["sku"],
                tier_level=item["tier_level"],
                max_facing_count=item["max_facing"],
                bounding_polygon={
                    "points": [
                        {"x": 100, "y": 100 * item["tier_level"]},
                        {"x": 450, "y": 100 * item["tier_level"]},
                        {"x": 450, "y": 100 * item["tier_level"] + 90},
                        {"x": 100, "y": 100 * item["tier_level"] + 90},
                    ]
                },
            )
            session.add(shelf_zone)

            # Determine initial inventory snapshot status
            vis_qty = item["initial_shelf_qty"]
            book_qty = item["initial_book_qty"]
            backroom_qty = max(0, book_qty - vis_qty)
            discrepancy = 0

            if book_qty == 0 and vis_qty == 0:
                status = "OUT_OF_STOCK"
            elif vis_qty <= 4 and backroom_qty > 10:
                status = "SHELF_RESTOCK_NEEDED"
            elif book_qty <= item["min_safety_stock"]:
                status = "LOW_STOCK"
            else:
                status = "HEALTHY"

            snapshot = InventorySnapshot(
                sku=item["sku"],
                recorded_at=now,
                visible_shelf_qty=vis_qty,
                book_inventory_qty=book_qty,
                estimated_backroom_qty=backroom_qty,
                discrepancy_qty=discrepancy,
                audit_source="SEED_INITIAL",
                status=status,
                confidence_score=1.0,
            )
            session.add(snapshot)

        session.commit()

        # Seed initial operational alerts
        alerts_to_add = [
            Alert(
                alert_type="OUT_OF_STOCK",
                severity="CRITICAL",
                sku="DAI-AMUL-BUTTER-100",
                title="Amul Butter 100g Out of Stock",
                message="Visible shelf and warehouse stock are 0 units. Immediate supplier order recommended.",
                is_resolved=False,
            ),
            Alert(
                alert_type="SHELF_EMPTY",
                severity="HIGH",
                sku="BEV-SPRITE-500",
                title="Sprite 500ml Shelf Empty",
                message="Visible shelf stock is only 4 units, but backroom contains 24 units. Replenish front shelf immediately.",
                is_resolved=False,
            ),
            Alert(
                alert_type="LOW_STOCK",
                severity="HIGH",
                sku="SNK-HALDIRAM-BHUJIA",
                title="Haldiram's Bhujia Sev Below Safety Threshold",
                message="Current total inventory is 5 units (Safety stock threshold: 8 units).",
                is_resolved=False,
            ),
        ]
        session.add_all(alerts_to_add)
        session.commit()

        # Generate 90 days of realistic sales transactions
        print("Generating 90 days of realistic daily POS sales transactions...")
        total_txns = generate_sales_transactions(session, SEED_PRODUCTS, days=90)
        print(f"Generated {total_txns} sales transactions across 90 days.")

        return {
            "status": "success",
            "products_count": len(SEED_PRODUCTS),
            "sales_transactions_count": total_txns,
            "alerts_count": len(alerts_to_add),
        }

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    result = seed_all()
    print("Database seeding completed:", result)
