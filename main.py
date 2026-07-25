import os
import sys
import django

# Resolve path to backend project so we can bootstrap Django settings and use Django models/serializers
backend_path = os.environ.get(
    "SWMM_BACKEND_DIR",
    "C:/Users/vedantrbhosale/Desktop/cs_swmm_v1/backend/backend_drf"
)
if backend_path not in sys.path:
    sys.path.append(backend_path)

# Add integrationservices's parent directory to path so integrationservices is a package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Set the settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swmm.settings")
django.setup()

from fastapi import FastAPI, Body, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import services
from integrationservices.services import run_unified_sync
from sfd.models import SFDTransaction, ChangeEquipmentRequest, RemoveEquipmentRequest

app = FastAPI(
    title="SWMM Integration Services API",
    description="Unified Synchronization API for SWMM–CMMS integration.",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status", summary="Check Integration & Synchronization Status")
def get_status():
    """
    Returns health status and current count of unsynced / in-progress records in SWMM.
    """
    unsynced_tx = SFDTransaction.objects.filter(is_synced=0).count()
    unsynced_cr = ChangeEquipmentRequest.objects.filter(is_synced=0).count()
    unsynced_rr = RemoveEquipmentRequest.objects.filter(is_synced=0).count()

    in_progress_tx = SFDTransaction.objects.filter(is_synced=2).count()
    in_progress_cr = ChangeEquipmentRequest.objects.filter(is_synced=2).count()
    in_progress_rr = RemoveEquipmentRequest.objects.filter(is_synced=2).count()

    total_unsynced = unsynced_tx + unsynced_cr + unsynced_rr
    total_in_progress = in_progress_tx + in_progress_cr + in_progress_rr

    sync_status = "synced"
    if total_in_progress > 0:
        sync_status = "in_progress"
    elif total_unsynced > 0:
        sync_status = "not_synced"

    return {
        "status": "active",
        "message": "Integration Services is up and running.",
        "app": "integrationservices",
        "sync_status": sync_status,
        "unsynced_counts": {
            "T_EquipmentShipDetail": unsynced_tx,
            "T_SFDChangeRequest": unsynced_cr,
            "Ch_SFD_Remove_Equipment_Request": unsynced_rr,
        },
        "in_progress_counts": {
            "T_EquipmentShipDetail": in_progress_tx,
            "T_SFDChangeRequest": in_progress_cr,
            "Ch_SFD_Remove_Equipment_Request": in_progress_rr,
        },
        "total_unsynced": total_unsynced,
        "total_in_progress": total_in_progress,
    }


@app.post("/sync", summary="Unified SWMM–CMMS Synchronization API")
def unified_sync(payload: dict = Body(default={})):
    """
    Single primary Unified Synchronization API endpoint.

    Executes the complete SWMM–CMMS synchronization workflow in sequence:
      1. Master Data Synchronization   — Pulls master/reference data from CMMS → SWMM
      2. Transaction Synchronization   — Pushes all pending SWMM transactions → CMMS
      3. Approval & Status Sync        — Pulls approval decisions & status changes from CMMS → SWMM

    Rejects duplicate execution if a synchronization session is already in progress.

    Optional Body:
      { "steps": ["masters", "push", "approvals"] }
    Omitting `steps` executes all three synchronization phases in sequence.
    """
    requested_steps = payload.get("steps") if payload else None
    result = run_unified_sync(steps=requested_steps)

    sync_status = result.get("status")
    if sync_status == "in_progress":
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=result)
    elif sync_status == "failed":
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=result)
    elif sync_status == "partial":
        return JSONResponse(status_code=status.HTTP_207_MULTI_STATUS, content=result)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
