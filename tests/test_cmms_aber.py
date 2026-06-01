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


def test_aber_endpoint_requires_api_key():
    client = build_client()
    response = client.get("/api/cmms/aber")
    assert response.status_code == 401


def test_get_aber_due_list(monkeypatch):
    ship = SimpleNamespace(id=301, name="INS Test", universal_id_m_ship="U-SHIP-1", active_external=True)
    equipment = SimpleNamespace(id=10, equipment_code="EQ-100", active=1)
    
    # Fitted equipment details older than 6 years (e.g. installed in 2018)
    eq_fit = SimpleNamespace(
        id=101,
        nomenclature="Main Stator",
        equipment=equipment,
        installation_date=date(2018, 5, 20),
        ship=ship
    )

    install_manager(monkeypatch, "ShipEquipment", [eq_fit])

    client = build_client()
    response = client.get("/api/cmms/aber", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nomenclature"] == "Main Stator"
    assert data[0]["age_years"] >= 6.0


def test_submit_aber_estimate(monkeypatch):
    created_objs = []
    def mock_create(**kwargs):
        kwargs["ABERID"] = 55
        kwargs["Universal_ID_T_ABER"] = "U-ABER-55"
        obj = SimpleNamespace(**kwargs)
        created_objs.append(obj)
        return obj

    monkeypatch.setattr(cmms.T_ABER.objects, "create", mock_create)

    payload = {
        "ship_id": 301,
        "fitted_equipment_id": 101,
        "budget_year": 2026,
        "estimate_cost": 75000.0,
        "currency": "INR",
        "aber_authority": "NAVY-ABER-2026-90",
        "repair_agency_id": 1,
        "remarks": "Overhaul"
    }

    client = build_client()
    response = client.post("/api/cmms/aber/submit", json=payload, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 201
    assert response.json()["Universal_ID_T_ABER"] == "U-ABER-55"
    assert len(created_objs) == 1
    assert float(created_objs[0].EstimateCost) == 75000.0


def test_get_aber_history(monkeypatch):
    estimate = SimpleNamespace(
        ABERID=55,
        Universal_ID_M_Ship="301",
        Universal_ID_T_EquipmentShipDetail="101",
        BudgetYear=2026,
        EstimateCost=75000.0,
        Currency="INR",
        ABERAuthority="NAVY-ABER-2026-90",
        RepairAgencyID=1,
        Remarks="Overhaul",
        Universal_ID_T_ABER="U-ABER-55"
    )

    install_manager(monkeypatch, "T_ABER", [estimate])

    client = build_client()
    response = client.get("/api/cmms/aber/history?ship_id=301&year=2026", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["Universal_ID_T_ABER"] == "U-ABER-55"
