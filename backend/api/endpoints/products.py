from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.product import Product
from backend.schemas.product import ProductDetailOut, ProductOut

router = APIRouter(prefix="/products", tags=["Products & Catalog"])


@router.get("", response_model=List[ProductOut])
async def list_products(
    category: Optional[str] = Query(None, description="Filter products by category"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve catalog products, optionally filtered by category."""
    query = select(Product).where(Product.is_active.is_(True))
    if category:
        query = query.where(Product.category == category)
    query = query.order_by(Product.category, Product.name)

    result = await db.execute(query)
    products = result.scalars().all()
    return products


@router.get("/categories", response_model=List[str])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """Retrieve unique product categories."""
    query = select(Product.category).distinct().order_by(Product.category)
    result = await db.execute(query)
    return [row[0] for row in result.all()]


@router.get("/{sku}", response_model=ProductDetailOut)
async def get_product(sku: str, db: AsyncSession = Depends(get_db)):
    """Retrieve detailed product information including shelf planogram zones."""
    query = (
        select(Product)
        .options(selectinload(Product.shelf_zones))
        .where(Product.sku == sku)
    )
    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku}' not found")

    return product
