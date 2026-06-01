"""FUSS Router - Deferment endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, status

from app.dependencies import verify_api_key
from app.schemas.all_schemas import (
    FussMastersResponse,
    FussRaiseRequest,
    FussSyncPayloadResponse,
    GenericSuccessResponse,
)

router = APIRouter(
    prefix="/cmms",
    tags=["FUSS - Deferment"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("/fuss", response_model=FussSyncPayloadResponse, summary="FUSS sync payload")
async def get_fuss_sync_payload():
    """Return an empty FUSS sync payload."""
    return FussSyncPayloadResponse()


@router.post(
    "/fuss",
    response_model=GenericSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate a deferment",
)
async def raise_deferment(payload: FussRaiseRequest):
    """Validate a FUSS deferment payload and acknowledge receipt."""
    serial_no = f"FUSS-{date.today().year}-{payload.routine_description_id}"
    return GenericSuccessResponse(
        success=True,
        message="Deferment payload validated successfully.",
        data={"serial_no": serial_no},
    )


@router.get("/fuss/masters", response_model=FussMastersResponse, summary="FUSS master tables")
async def get_fuss_masters():
    """Return empty FUSS master lookup tables."""
    return FussMastersResponse()
