"""MAINTOP Router - Maintenance Procedure sync endpoints."""

from fastapi import APIRouter, Depends

from app.dependencies import verify_api_key
from app.schemas.all_schemas import (
    MaintopDistributionRequest,
    MaintopDistributionResponse,
    MaintopJICRequest,
    MaintopJICResponse,
    MaintopSyncRequest,
    MaintopSyncResponse,
)

router = APIRouter(
    prefix="/cmms",
    tags=["MAINTOP - Maintenance Procedures"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/maintop/sync", response_model=MaintopSyncResponse, summary="Validate MAINTOP headers and details")
async def sync_maintop(payload: MaintopSyncRequest):
    """Validate MAINTOP headers/details and report received counts."""
    return MaintopSyncResponse(
        status=True,
        headers_processed=len(payload.T_maintopheader),
        details_processed=len(payload.T_maintopdetail),
    )


@router.post("/maintop/jic", response_model=MaintopJICResponse, summary="Validate JIC data")
async def sync_jic(payload: MaintopJICRequest):
    """Validate JIC, spares, tools, and attachments payloads."""
    return MaintopJICResponse(
        status=True,
        jics_processed=len(payload.T_maintopJIC),
        spares_processed=len(payload.T_JICspares),
        tools_processed=len(payload.T_JICtools),
        attachments_processed=len(payload.T_JICattachments),
    )


@router.post("/maintop/distribution", response_model=MaintopDistributionResponse, summary="Validate distribution data")
async def sync_distribution(payload: MaintopDistributionRequest):
    """Validate MAINTOP distribution payloads and report received counts."""
    return MaintopDistributionResponse(
        status=True,
        addresses_processed=len(payload.M_address),
        distributions_processed=len(payload.M_distribution_address),
        defaults_processed=len(payload.T_MaintoplibraryDisDef),
    )
