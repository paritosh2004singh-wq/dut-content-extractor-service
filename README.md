# Intelligent Knowledge Ingestion Platform - Backend

This repository contains the backend service for the Intelligent Knowledge Ingestion Platform, built using FastAPI, Motor (asynchronous MongoDB driver), Pydantic Settings, and Loguru.

The service provides a robust foundation for handling document ingestion, data extraction, and storage with structured logging, configuration management, repository patterns, database migrations/indexing, and testing setups.

## Core Capabilities Implemented (as of now)

### 1. Application Entry Point and Lifecycle Management
* Located at the root main.py, implementing the main FastAPI application.
* Uses an asynchronous lifespan context manager to manage application startup and shutdown tasks.
* Automatically establishes a connection to MongoDB on startup, provisions required collection indexes, and closes connection handles on shutdown.
* Configured with CORS middleware to authorize allowed origins.

### 2. Configuration Management
* Leverages Pydantic Settings for validating and loading configurations from .env files.
* Defines server host, port, application name, debug settings, and database configurations.
* Requires database credentials (MONGO_URI and MONGO_DATABASE) to enforce secure connections.

### 3. Structured Logging System
* Integrates the Loguru framework to handle all system and event logging.
* Suppresses default handlers to output a clean, unified format including timestamp, log level, module, function name, line number, and log message.

### 4. Database Layer (MongoDB)
* Fully asynchronous MongoDB connectivity managed by the MongoDBClient wrapper.
* Supports active connection validation via a ping check.
* Defines individual asynchronous helper functions for all 17 target collections:
  * documents
  * pages
  * blocks
  * semantic_objects
  * question_objects
  * section_objects
  * paragraph_objects
  * table_objects
  * figure_objects
  * equation_objects
  * form_objects
  * processing_jobs
  * graph_sync
  * embeddings_metadata
  * ingestion_logs
  * extracted_entities
  * system_config

### 5. Repository Pattern
* BaseRepository: An abstract, generic base repository providing standard CRUD operations (create, find_one, find_many with pagination, update_one, delete_one, and count) with type annotations.
* DocumentRepository: A concrete repository inheriting from BaseRepository specifically configured for the documents collection.

### 6. Health and Monitoring API
* Exposes a /api/v1/health GET endpoint.
* Verifies live database connectivity using MongoDB's ping command.
* Returns appropriate status codes (200 OK when healthy, 503 Service Unavailable when the database is offline) along with a structured JSON response.

### 7. Testing Infrastructure
* Standardized testing setup using Pytest and pytest-asyncio.
* Configured using pytest.ini to discover tests in the tests directory and run async fixtures natively.
* Fixture conftest.py establishes isolated event loops and provisions test database instances (dropping the databases after execution is complete) to ensure hermetic test execution.

---

## Directory Structure

* main.py: Root entry point containing the FastAPI application setup, middleware, and routers.
* app/: Core application directory.
  * core/: Application configurations, settings, and logging configuration.
  * database/: Client setup, collection helpers, indexes, and repositories.
  * api/: API routers, endpoint controllers, and request/response schemas.
* tests/: Automated test files divided into unit, integration, and e2e scopes.
* pytest.ini: Pytest configuration file.

---

## Configuration and Setup

1. Copy the template .env.example file to .env:
   copy .env.example .env

2. Edit the .env file with your local database parameters:
   MONGO_URI=mongodb://localhost:27017
   MONGO_DATABASE=knowledge_ingestion

---

## Running the Application

To run the application locally:
python main.py

To run the test suite:
python -m pytest
