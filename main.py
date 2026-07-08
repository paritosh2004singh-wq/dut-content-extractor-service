from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.settings import settings
from app.database.mongodb.client import mongodb
from app.database.mongodb.indexes import create_indexes
from app.api.routers.health import router as health_router
import app.core.logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application Started")
    try:
        await mongodb.connect()
        await create_indexes()
        yield
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise
    finally:
        await mongodb.disconnect()
        logger.info("Application Shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Knowledge Ingestion Platform API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_PREFIX, tags=["Health"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
    
