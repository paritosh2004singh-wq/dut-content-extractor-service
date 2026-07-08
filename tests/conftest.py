import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.settings import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_db():
    """Provide an isolated test database and clean it up after each test."""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db_name = f"{settings.MONGO_DATABASE}_test"
    db = client[db_name]
    
    yield db
    
    # Cleanup after test
    await client.drop_database(db_name)
    client.close()
