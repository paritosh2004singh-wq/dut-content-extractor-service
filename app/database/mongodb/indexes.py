from loguru import logger
from app.database.mongodb.collections import documents
import pymongo

async def create_indexes() -> None:
    """Create all required MongoDB indexes."""
    logger.info("Creating MongoDB indexes...")
    
    collection = documents()
    await collection.create_index([("page_id", pymongo.ASCENDING)], name="documents_page_id_idx")
    await collection.create_index([("document_id", pymongo.ASCENDING)], name="documents_document_id_idx")
    await collection.create_index([("status", pymongo.ASCENDING)], name="documents_status_idx")
    await collection.create_index([("created_at", pymongo.ASCENDING)], name="documents_created_at_idx")
    
    logger.info("MongoDB indexes created successfully")
