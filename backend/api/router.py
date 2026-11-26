from fastapi import APIRouter
from backend.api.endpoints import alerts, cctv, forecast, health, inventory, products, sales, vision

api_router = APIRouter()

# Register core endpoint sub-routers
api_router.include_router(health.router)
api_router.include_router(products.router)
api_router.include_router(inventory.router)
api_router.include_router(sales.router)
api_router.include_router(alerts.router)
api_router.include_router(vision.router)
api_router.include_router(forecast.router)
api_router.include_router(cctv.router)
