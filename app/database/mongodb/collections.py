from motor.motor_asyncio import AsyncIOMotorCollection
from app.database.mongodb.client import mongodb


def get_database():
    return mongodb.database


def documents() -> AsyncIOMotorCollection:
    """Get the documents collection."""
    return get_database()["documents"]


def pages() -> AsyncIOMotorCollection:
    """Get the pages collection."""
    return get_database()["pages"]


def blocks() -> AsyncIOMotorCollection:
    """Get the blocks collection."""
    return get_database()["blocks"]


def semantic_objects() -> AsyncIOMotorCollection:
    """Get the semantic_objects collection."""
    return get_database()["semantic_objects"]


def question_objects() -> AsyncIOMotorCollection:
    """Get the question_objects collection."""
    return get_database()["question_objects"]


def section_objects() -> AsyncIOMotorCollection:
    """Get the section_objects collection."""
    return get_database()["section_objects"]


def paragraph_objects() -> AsyncIOMotorCollection:
    """Get the paragraph_objects collection."""
    return get_database()["paragraph_objects"]


def table_objects() -> AsyncIOMotorCollection:
    """Get the table_objects collection."""
    return get_database()["table_objects"]


def figure_objects() -> AsyncIOMotorCollection:
    """Get the figure_objects collection."""
    return get_database()["figure_objects"]


def equation_objects() -> AsyncIOMotorCollection:
    """Get the equation_objects collection."""
    return get_database()["equation_objects"]


def form_objects() -> AsyncIOMotorCollection:
    """Get the form_objects collection."""
    return get_database()["form_objects"]


def processing_jobs() -> AsyncIOMotorCollection:
    """Get the processing_jobs collection."""
    return get_database()["processing_jobs"]


def graph_sync() -> AsyncIOMotorCollection:
    """Get the graph_sync collection."""
    return get_database()["graph_sync"]


def embeddings_metadata() -> AsyncIOMotorCollection:
    """Get the embeddings_metadata collection."""
    return get_database()["embeddings_metadata"]


def ingestion_logs() -> AsyncIOMotorCollection:
    """Get the ingestion_logs collection."""
    return get_database()["ingestion_logs"]


def extracted_entities() -> AsyncIOMotorCollection:
    """Get the extracted_entities collection."""
    return get_database()["extracted_entities"]


def system_config() -> AsyncIOMotorCollection:
    """Get the system_config collection."""
    return get_database()["system_config"]

def compiler_telemetry() -> AsyncIOMotorCollection:
    """Get the compiler_telemetry collection for region compiler state tracking."""
    return get_database()["compiler_telemetry"]

def canonical_documents() -> AsyncIOMotorCollection:
    """Get the canonical_documents collection for compiled output."""
    return get_database()["canonical_documents"]