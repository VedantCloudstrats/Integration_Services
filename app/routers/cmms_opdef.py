"""OPDEF Router - Operational Defect endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, status

from app.schemas.all_schemas import (
    GenericSuccessResponse,
    OpdefAnalysisRequest,
    OpdefInitiateRequest,
    OpdefInitiateResponse,
    OpdefPhotoResponse,
    OpdefPriorParamRequest,
    OpdefSpareRequest,
    OpdefSyncPayloadResponse,
    OpdefTrialRequest,
)

router = APIRouter(
    prefix="/cmms",
    tags=["OPDEF - Operational Defect"],
)


@router.get(
    "/opdef", response_model=OpdefSyncPayloadResponse, summary="Full OPDEF sync payload"
)
async def get_opdef_payload():
    """Return an empty OPDEF sync payload."""
    return OpdefSyncPayloadResponse()


@router.post(
    "/opdef",
    response_model=OpdefInitiateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate OPDEF initiation",
)
async def initiate_opdef(payload: OpdefInitiateRequest):
    """Validate an OPDEF initiation payload and return a derived ID."""
    return OpdefInitiateResponse(
        OpdefMainID=0,
        Universal_ID_T_OpdefMain=f"U-OPD-{payload.ship_id}-{payload.fitted_equipment_id}-{payload.opdef_number}",
    )


@router.post(
    "/opdef/{opdef_id}/analysis",
    response_model=GenericSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate defect analysis",
)
async def submit_analysis(opdef_id: int, payload: OpdefAnalysisRequest):
    """Validate an OPDEF analysis payload and acknowledge receipt."""
    return GenericSuccessResponse(
        success=True,
        message="Defect analysis payload validated successfully.",
        data={"opdef_id": opdef_id, "analysis_date": payload.analysis_date},
    )


@router.post(
    "/opdef/{opdef_id}/spares",
    response_model=GenericSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate spare consumption",
)
async def log_spares(opdef_id: int, payload: OpdefSpareRequest):
    """Validate a spare consumption payload and acknowledge receipt."""
    return GenericSuccessResponse(
        success=True,
        message="Spare consumption payload validated successfully.",
        data={"opdef_id": opdef_id, "spare_item_code": payload.spare_item_code},
    )


@router.post(
    "/opdef/{opdef_id}/trials",
    response_model=GenericSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate trial parameters",
)
async def log_trials(opdef_id: int, payload: OpdefTrialRequest):
    """Validate trial conducted parameters and acknowledge receipt."""
    return GenericSuccessResponse(
        success=True,
        message="Trial parameters payload validated successfully.",
        data={"opdef_id": opdef_id, "trial_date": payload.trial_date},
    )


@router.post(
    "/opdef/{opdef_id}/prior-parameters",
    response_model=GenericSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate prior parameters",
)
async def log_prior_params(opdef_id: int, payload: OpdefPriorParamRequest):
    """Validate prior reading parameters and acknowledge receipt."""
    return GenericSuccessResponse(
        success=True,
        message="Prior parameters payload validated successfully.",
        data={"opdef_id": opdef_id, "reading_time": payload.reading_time},
    )


@router.post(
    "/opdef/{opdef_id}/photographs",
    response_model=OpdefPhotoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate photograph association",
)
async def upload_photograph(
    opdef_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
):
    """Validate photograph upload metadata and return a derived file path."""
    file_path = f"/media/opdef_photos/{file.filename}"
    return OpdefPhotoResponse(
        success=True,
        file_path=file_path,
        message=f"Photograph metadata validated at {datetime.now().isoformat()}.",
    )
