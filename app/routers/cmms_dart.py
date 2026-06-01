"""DART Router - Defect tracking endpoints."""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.dependencies import verify_api_key
from app.schemas.all_schemas import (
    CmmsDartPayloadResponse,
    CompletedRoutineCreate,
    CompletedRoutineResponse,
    DefectCreate,
    DefectRectifyRequest,
    DefectResponse,
    GenericSuccessResponse,
)

router = APIRouter(
    prefix="/cmms",
    tags=["DART - Defect Tracking"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("/dart", response_model=CmmsDartPayloadResponse, summary="Full DART sync payload")
async def get_dart_payload():
    """Return an empty DART sync payload."""
    return CmmsDartPayloadResponse()


@router.get("/defects", response_model=List[DefectResponse], summary="List all defects")
async def get_defects(
    is_closed: Optional[bool] = None,
    is_operational: Optional[bool] = None,
    equipment_code: Optional[str] = None,
):
    """Return an empty defects list. Query params are still validated."""
    return []


@router.get("/defects/{defect_id}", response_model=DefectResponse, summary="Get defect by ID")
async def get_defect(defect_id: int):
    """Return a validation-only defect representation for the requested ID."""
    return DefectResponse(id=defect_id)


@router.post(
    "/defects",
    response_model=DefectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate a defect",
)
async def create_defect(payload: DefectCreate):
    """Validate a DART defect payload and return a response-shaped object."""
    return DefectResponse(
        id=0,
        dart_number=payload.dart_number,
        dart_sr_number=payload.dart_sr_number,
        dart_date=payload.dart_date,
        rectification_date=payload.rectification_date,
        is_closed=False,
        defective_discriptions=payload.defective_discriptions,
        defective_component=payload.defective_component,
        maintenance_period=payload.maintenance_period,
        is_guarantee_defect=bool(payload.is_guarantee_defect),
        created_date=date.today(),
    )


@router.post("/defects/{defect_id}/rectify", response_model=GenericSuccessResponse, summary="Validate defect rectification")
async def rectify_defect(defect_id: int, payload: DefectRectifyRequest):
    """Validate a defect rectification payload and acknowledge receipt."""
    return GenericSuccessResponse(
        success=True,
        message="Defect rectification payload validated successfully.",
        data={"defect_id": defect_id, "rectified_date": payload.rectified_date},
    )


@router.get("/routines/completed", response_model=List[CompletedRoutineResponse], summary="List completed routines")
async def get_completed_routines():
    """Return an empty completed routines list."""
    return []


@router.post(
    "/routines/complete",
    response_model=GenericSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate routine completion",
)
async def complete_routine(payload: CompletedRoutineCreate):
    """Validate a completed maintenance routine payload and acknowledge receipt."""
    return GenericSuccessResponse(
        success=True,
        message="Routine completion payload validated successfully.",
        data={"routine_id": payload.routine_id},
    )
