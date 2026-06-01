"""ABER Router - Annual Budget Estimate of Repair endpoints."""

from typing import List, Optional

from fastapi import APIRouter, status

from app.schemas.all_schemas import (
    AberEquipmentResponse,
    AberSubmitRequest,
    AberSubmitResponse,
)

router = APIRouter(
    prefix="/cmms",
    tags=["ABER - Annual Budget Estimate"],
)


@router.get(
    "/aber",
    response_model=List[AberEquipmentResponse],
    summary="Equipment eligible for ABER",
)
async def get_aber_equipment():
    """Return an empty ABER equipment list."""
    return []


@router.post(
    "/aber/submit",
    response_model=AberSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate ABER estimate",
)
async def submit_aber_estimate(payload: AberSubmitRequest):
    """Validate an ABER estimate payload and return derived identifiers."""
    return AberSubmitResponse(
        ABERID=0,
        Universal_ID_T_ABER=f"U-ABER-{payload.ship_id}-{payload.fitted_equipment_id}-{payload.budget_year}",
        Universal_ID_M_Ship=f"U-SHIP-{payload.ship_id}",
        BudgetYear=payload.budget_year,
        EstimateCost=payload.estimate_cost,
        Currency=payload.currency,
        ABERAuthority=payload.aber_authority,
        RepairAgencyID=payload.repair_agency_id,
        Remarks=payload.remarks,
    )


@router.get(
    "/aber/history",
    response_model=List[AberSubmitResponse],
    summary="ABER estimate history",
)
async def get_aber_history(ship_id: Optional[str] = None, year: Optional[int] = None):
    """Return an empty ABER history list. Query params are still validated."""
    return []
