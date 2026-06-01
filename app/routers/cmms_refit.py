"""Refit Router - Refit integration endpoints."""

from datetime import date

from fastapi import APIRouter, status

from app.schemas.all_schemas import (
    GenericSuccessResponse,
    RefitCompletionCreate,
    RefitCompletionResponse,
    RefitDelinquencyCreate,
    RefitDryDockingCreate,
    RefitOCRCreate,
    RefitSyncPayloadResponse,
)

router = APIRouter(
    prefix="/cmms",
    tags=["Refit - Refit Integration"],
)


@router.get(
    "/refit", response_model=RefitSyncPayloadResponse, summary="Refit sync payload"
)
async def get_refit_payload():
    """Return an empty refit sync payload."""
    return RefitSyncPayloadResponse()


@router.get("/refit/completions", summary="List refit completions")
async def get_refit_completions():
    """Return an empty refit completions list."""
    return []


@router.post(
    "/refit/completions",
    response_model=RefitCompletionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate refit completion",
)
async def create_refit_completion(payload: RefitCompletionCreate):
    """Validate a refit maintenance period payload and return a derived ID."""
    return RefitCompletionResponse(
        id=0,
        Universal_ID_T_RefComp=f"U-RC-{date.today().isoformat()}-{payload.ship_code}",
    )


@router.post(
    "/refit/completions/{uid}/delinquency",
    response_model=GenericSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate delinquency",
)
async def log_delinquency(uid: str, payload: RefitDelinquencyCreate):
    """Validate a delinquency detail payload and acknowledge receipt."""
    return GenericSuccessResponse(
        success=True,
        message="Delinquency payload validated successfully.",
        data={"refit_uid": uid, "delinquency_code": payload.delinquency_code},
    )


@router.post(
    "/refit/completions/{uid}/drydock",
    response_model=GenericSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate drydocking",
)
async def log_drydock(uid: str, payload: RefitDryDockingCreate):
    """Validate a drydocking payload and acknowledge receipt."""
    return GenericSuccessResponse(
        success=True,
        message="Drydocking payload validated successfully.",
        data={"refit_uid": uid, "dock_entry_date": payload.dock_entry_date},
    )


@router.post(
    "/refit/completions/{uid}/ocr",
    response_model=GenericSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate OCR status",
)
async def log_ocr(uid: str, payload: RefitOCRCreate):
    """Validate an OCR payload and acknowledge receipt."""
    return GenericSuccessResponse(
        success=True,
        message="OCR payload validated successfully.",
        data={"refit_uid": uid, "report_ref_no": payload.report_ref_no},
    )
