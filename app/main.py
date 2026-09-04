"""FastAPI Application entry point for Agent 1 Runtime."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.analytics import router as analytics_router
from api.documents import router as documents_router
from api.query import router as query_router
from api.upload import router as upload_router
from config import settings
from core.runtime import AgentRuntime
from exceptions import BaseAgentException
from logger import logger

runtime = AgentRuntime()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and shutdown hooks."""
    logger.info(
        "Starting up %s in %s environment...",
        settings.APP_NAME,
        settings.APP_ENV,
    )
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Register CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(upload_router)
app.include_router(documents_router)
app.include_router(query_router)
app.include_router(analytics_router)


@app.exception_handler(BaseAgentException)
async def agent_domain_exception_handler(
    request: Request, exc: BaseAgentException
) -> JSONResponse:
    """Handles domain-specific exceptions safely without leaking internal stack traces."""
    logger.error(
        "Domain exception encountered on %s: %s",
        request.url.path,
        exc.message,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An internal runtime error occurred. Please consult system logs."
        },
    )


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Fallback handler for unhandled exceptions ensuring safe responses."""
    logger.critical(
        "Unhandled exception on %s: %s",
        request.url.path,
        str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected error occurred."},
    )


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}

for route in app.routes:
    logger.info(
        "REGISTERED ROUTE: %s %s",
        getattr(route, "methods", None),
        getattr(route, "path", None),
    )