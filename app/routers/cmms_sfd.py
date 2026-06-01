"""SFD Router - Ship Fit Database endpoints."""

from typing import List, Optional

from fastapi import APIRouter

from app.schemas.all_schemas import (
    ShipEquipmentResponse,
    SfdShipResponse,
    SfdSyncPayloadResponse,
)

router = APIRouter(
    prefix="/cmms",
    tags=["SFD - Ship Fit Database"],
)


@router.get(
    "/sfd", response_model=List[ShipEquipmentResponse], summary="List ship equipment"
)
async def get_sfd_equipments(ship_id: Optional[int] = None):
    """Return an empty equipment list. Query params are still validated by FastAPI."""
    return []


@router.get("/sfd/ships", response_model=List[SfdShipResponse], summary="List ships")
async def get_sfd_ships():
    """Return an empty ship list. This service does not read from a database."""
    return []


@router.get(
    "/sfd/payload",
    response_model=SfdSyncPayloadResponse,
    summary="Full SFD sync payload",
)
async def get_sfd_payload():
    """Return an empty SFD sync payload."""
    return SfdSyncPayloadResponse()
