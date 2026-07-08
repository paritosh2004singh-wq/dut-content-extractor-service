from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from loguru import logger
from typing import Optional

from app.core.settings import settings


class MongoDBClient:
    """
    Handles MongoDB connection lifecycle.
    """

    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None

    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            raise RuntimeError("MongoDB client is not connected.")
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise RuntimeError("MongoDB database is not connected.")
        return self._database

    async def connect(self):
        logger.info("Connecting to MongoDB...")
        self._client = AsyncIOMotorClient(settings.MONGO_URI)
        self._database = self._client[settings.MONGO_DATABASE]
        logger.info("MongoDB Connected")

    async def disconnect(self):
        if self._client:
            self._client.close()
            logger.info("MongoDB Disconnected")

    async def ping(self) -> bool:
        if self._client is None:
            return False
        try:
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False


mongodb = MongoDBClient()