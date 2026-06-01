from datetime import date
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fast_api.dependencies import verify_api_key
from fast_api.routers import cmms
from fast_api.tests.test_cmms_dart import FakeQuerySet, install_manager


def build_client():
    app = FastAPI()
    app.include_router(cmms.router, prefix="/api")
    return TestClient(app)


def test_fuss_endpoint_requires_api_key():
    client = build_client()
    response = client.get("/api/cmms/fuss")
    assert response.status_code == 401


def test_get_fuss_payload_sync(monkeypatch):
    fuss_req = SimpleNamespace(
        id=12,
        isclosed_fuss=False,
        serial_no="FUSS-2026-001",
        routine_description_id=201,
        fuss_date=date(2026, 5, 30),
        last_undertaken=date(2026, 4, 30),
        due_date=date(2026, 5, 30),
        schedule_date=date(2026, 6, 30),
        equipment="Main Generator #1",
        location_on_board="Engine Room Starboard",
        maintop_no="MT-8802",
        frequency="monthly"
    )

    deferment = SimpleNamespace(
        DefermentID=1,
        DefermentCode="DEF-01",
        Description="Spare Parts Non-availability",
        Active=True,
        Universal_ID_M_Deferment="U-DEF-01"
    )
    reason = SimpleNamespace(
        ReasonID=2,
        ReasonCode="RSN-02",
        Description="Operational Commitment",
        Active=True,
        Universal_ID_M_Reason="U-RSN-02"
    )
    inability = SimpleNamespace(
        InabilityID=3,
        InabilityCode="INAB-03",
        Description="Material Failure",
        Active=True,
        Universal_ID_M_Inability="U-INAB-03"
    )

    install_manager(monkeypatch, "FussRaiseDetails", [fuss_req])
    install_manager(monkeypatch, "M_Deferment", [deferment])
    install_manager(monkeypatch, "M_Reason", [reason])
    install_manager(monkeypatch, "M_Inability", [inability])

    client = build_client()
    response = client.get("/api/cmms/fuss", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    payload = response.json()
    assert "T_fuss" in payload
    assert "M_Deferment" in payload
    assert len(payload["T_fuss"]) == 1
    assert payload["T_fuss"][0]["serial_no"] == "FUSS-2026-001"
    assert payload["M_Deferment"][0]["DefermentCode"] == "DEF-01"


def test_raise_deferment(monkeypatch):
    created_objs = []
    def mock_create(**kwargs):
        kwargs["id"] = 12
        kwargs["isclosed_fuss"] = False
        kwargs["serial_no"] = f"FUSS-2026-{kwargs['routine_description_id']}"
        obj = SimpleNamespace(**kwargs)
        created_objs.append(obj)
        return obj

    monkeypatch.setattr(cmms.FussRaiseDetails.objects, "create", mock_create)

    payload = {
        "routine_description_id": 201,
        "fuss_date": "2026-05-30",
        "last_undertaken": "2026-04-30",
        "due_date": "2026-05-30",
        "schedule_date": "2026-06-30",
        "equipment": "Main Generator #1",
        "location_on_board": "Engine Room Starboard",
        "maintop_no": "MT-8802",
        "frequency": "monthly"
    }

    client = build_client()
    response = client.post("/api/cmms/fuss", json=payload, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(created_objs) == 1
    assert created_objs[0].equipment == "Main Generator #1"


def test_get_deferment_masters(monkeypatch):
    deferment = SimpleNamespace(
        DefermentID=1,
        DefermentCode="DEF-01",
        Description="Spare Parts Non-availability",
        Active=True,
        Universal_ID_M_Deferment="U-DEF-01"
    )
    reason = SimpleNamespace(
        ReasonID=2,
        ReasonCode="RSN-02",
        Description="Operational Commitment",
        Active=True,
        Universal_ID_M_Reason="U-RSN-02"
    )
    inability = SimpleNamespace(
        InabilityID=3,
        InabilityCode="INAB-03",
        Description="Material Failure",
        Active=True,
        Universal_ID_M_Inability="U-INAB-03"
    )

    install_manager(monkeypatch, "M_Deferment", [deferment])
    install_manager(monkeypatch, "M_Reason", [reason])
    install_manager(monkeypatch, "M_Inability", [inability])

    client = build_client()
    response = client.get("/api/cmms/fuss/masters", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    payload = response.json()
    assert "M_deferment" in payload
    assert "M_reason" in payload
    assert payload["M_deferment"][0]["DefermentCode"] == "DEF-01"
    assert payload["M_reason"][0]["ReasonCode"] == "RSN-02"
    assert payload["M_inability"][0]["InabilityCode"] == "INAB-03"
