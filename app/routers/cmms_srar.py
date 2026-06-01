"""SRAR Router - Ship Running Assessment Report endpoints."""

from typing import List

from fastapi import APIRouter, status

from app.schemas.all_schemas import (
    GenericSuccessResponse,
    SRARBulkCreate,
    SRARDetailResponse,
)

router = APIRouter(
    prefix="/cmms",
    tags=["SRAR - Ship Running Assessment"],
)


@router.get(
    "/srar", response_model=List[SRARDetailResponse], summary="List all SRAR reports"
)
async def get_srar_list():
    """Return an empty SRAR list. This service does not read from a database."""
    return []


@router.post(
    "/srar",
    response_model=GenericSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate SRAR report",
)
async def create_srar(payload: SRARBulkCreate):
    """Validate a SRAR payload and acknowledge receipt without persistence."""
    return GenericSuccessResponse(
        success=True,
        message="SRAR report payload validated successfully.",
        data={
            "ship_id": payload.header.ship_id,
            "srar_month": payload.header.srar_month,
            "srar_year": payload.header.srar_year,
            "exploitations_received": len(payload.exploitations),
        },
    )
