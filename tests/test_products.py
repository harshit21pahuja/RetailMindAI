import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_products(async_client: AsyncClient):
    """Test listing seeded catalog products."""
    response = await async_client.get("/api/v1/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 15
    skus = [p["sku"] for p in products]
    assert "BEV-COKE-500" in skus
    assert "DAI-AMUL-MILK-500" in skus
    assert "SNK-KURKURE-MM" in skus


@pytest.mark.asyncio
async def test_filter_products_by_category(async_client: AsyncClient):
    """Test category filtering."""
    response = await async_client.get("/api/v1/products?category=Beverages")
    assert response.status_code == 200
    beverages = response.json()
    assert len(beverages) == 4
    for b in beverages:
        assert b["category"] == "Beverages"


@pytest.mark.asyncio
async def test_get_categories(async_client: AsyncClient):
    """Test retrieving unique category list."""
    response = await async_client.get("/api/v1/products/categories")
    assert response.status_code == 200
    categories = response.json()
    assert "Beverages" in categories
    assert "Snacks" in categories
    assert "Dairy" in categories
    assert "Instant Foods" in categories


@pytest.mark.asyncio
async def test_get_single_product_detail(async_client: AsyncClient):
    """Test fetching a specific SKU with its shelf zones."""
    response = await async_client.get("/api/v1/products/BEV-COKE-500")
    assert response.status_code == 200
    product = response.json()
    assert product["sku"] == "BEV-COKE-500"
    assert product["brand"] == "Coca-Cola"
    assert len(product["shelf_zones"]) >= 1
    assert product["shelf_zones"][0]["zone_code"] == "SHELF-A1-TIER1"
