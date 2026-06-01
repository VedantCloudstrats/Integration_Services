"""
SWMM CMMS Integration - FastAPI Microservice
============================================
Stateless service: handles API routing and request/response validation only.
"""

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError

from app.config import settings
from app.dependencies import verify_api_key
from app.exceptions import (
    AppBaseException,
    app_exception_handler,
    http_exception_handler,
    pydantic_validation_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.routers import (
    cmms_aber,
    cmms_dart,
    cmms_fuss,
    cmms_maintop,
    cmms_opdef,
    cmms_refit,
    cmms_sfd,
    cmms_srar,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_title,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppBaseException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Consolidate all CMMS routers
    api_router = APIRouter()
    api_router.include_router(cmms_dart.router)
    api_router.include_router(cmms_srar.router)
    api_router.include_router(cmms_fuss.router)
    api_router.include_router(cmms_aber.router)
    api_router.include_router(cmms_sfd.router)
    api_router.include_router(cmms_refit.router)
    api_router.include_router(cmms_opdef.router)
    api_router.include_router(cmms_maintop.router)

    # Register under both the versioned /api/v1 and legacy /api prefixes, securing both
    app.include_router(
        api_router,
        prefix="/api/v1",
        dependencies=[Depends(verify_api_key)],
    )
    app.include_router(
        api_router,
        prefix="/api",
        dependencies=[Depends(verify_api_key)],
    )

    @app.get("/", tags=["Health"], dependencies=[Depends(verify_api_key)])
    async def root():
        return {
            "service": settings.app_title,
            "version": settings.app_version,
            "status": "online",
            "mode": "stateless-validation",
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"], dependencies=[Depends(verify_api_key)])
    async def health():
        return {"status": "healthy", "mode": "stateless-validation"}

    return app


app = create_app()

