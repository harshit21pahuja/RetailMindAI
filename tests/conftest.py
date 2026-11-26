import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Force testing configuration
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_retailmind.db"
os.environ["SYNC_DATABASE_URL"] = "sqlite:///./test_retailmind.db"

from backend.database import init_db_sync
from backend.main import app
from backend.seed.seed_database import seed_all


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initializes and seeds the database before tests run."""
    # Ensure fresh test database
    if os.path.exists("./test_retailmind.db"):
        try:
            os.remove("./test_retailmind.db")
        except PermissionError:
            pass

    init_db_sync()
    seed_all()
    yield

    # Clean up after test run
    if os.path.exists("./test_retailmind.db"):
        try:
            os.remove("./test_retailmind.db")
        except PermissionError:
            pass


@pytest_asyncio.fixture
async def async_client():
    """Yields an async HTTP client connected to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
