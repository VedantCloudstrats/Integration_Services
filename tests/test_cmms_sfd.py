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


def test_sfd_endpoint_requires_api_key():
    client = build_client()
    response = client.get("/api/cmms/sfd/payload")
    assert response.status_code == 401


def test_get_sfd_payload(monkeypatch):
    # Setup mocks for all 19 entities (or empty collections/SimpleNamespace mocks)
    install_manager(monkeypatch, "GenericSpecification", [SimpleNamespace(id=1, name="Specs")])
    install_manager(monkeypatch, "Group", [SimpleNamespace(id=1, name="Grp")])
    install_manager(monkeypatch, "Section", [SimpleNamespace(id=1, name="Sec")])
    install_manager(monkeypatch, "Equipment", [SimpleNamespace(id=1, equipment_code="EQ-1")])
    install_manager(monkeypatch, "Ship", [SimpleNamespace(id=1, name="Ship-1", universal_id_m_ship="U-SHIP-1")])
    install_manager(monkeypatch, "Generic", [SimpleNamespace(id=1, code="GEN-1")])
    install_manager(monkeypatch, "Command", [SimpleNamespace(id=1, name="Cmd-1")])
    install_manager(monkeypatch, "OpsAuthority", [SimpleNamespace(id=1, name="Ops-1")])
    install_manager(monkeypatch, "EquipmentSpecification", [SimpleNamespace(id=1, name="Eq-Spec")])
    install_manager(monkeypatch, "ShipEquipment", [SimpleNamespace(id=1, nomenclature="Pump")])
    install_manager(monkeypatch, "SFDHierarchy", [SimpleNamespace(id=1, name="Hier")])
    install_manager(monkeypatch, "Propulsion", [SimpleNamespace(id=1, name="Prop")])
    install_manager(monkeypatch, "EquipmentPolicy", [SimpleNamespace(id=1, policy="Pol")])
    install_manager(monkeypatch, "Country", [SimpleNamespace(id=1, name="Country-1")])
    install_manager(monkeypatch, "ShipClass", [SimpleNamespace(id=1, hull_code="C-1")])
    install_manager(monkeypatch, "Supplier", [SimpleNamespace(id=1, SupplierName="Sup-1")])

    client = build_client()
    response = client.get("/api/cmms/sfd/payload", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    payload = response.json()
    assert "T_genericspecification" in payload
    assert "M_group" in payload
    assert "T_EquipmentShipDetail" in payload
    assert len(payload["T_EquipmentShipDetail"]) == 1


def test_sync_sfd_only_update_new_additions(monkeypatch):
    # Scenario 1: Pre-existing synced record 201 (is_synced = True)
    existing_record = SimpleNamespace(id=201, nomenclature="Original Propulsion Motor", is_synced=True, save=lambda: None)
    
    # Store saved states to verify
    saved_records = []
    created_records = []

    def mock_filter(**kwargs):
        # If looking up 201, return existing. If looking up 202, return empty
        if kwargs.get("id") == 201:
            return FakeQuerySet([existing_record])
        return FakeQuerySet([])

    def mock_create(**kwargs):
        created_records.append(kwargs)
        return SimpleNamespace(**kwargs)

    monkeypatch.setattr(cmms.ShipEquipment.objects, "filter", mock_filter)
    monkeypatch.setattr(cmms.ShipEquipment.objects, "create", mock_create)

    # Let's mock existing_record.save
    def mock_save():
        saved_records.append(existing_record)
    existing_record.save = mock_save

    client = build_client()

    # Scenario 1 payload (should ignore since is_synced is True locally)
    payload_ignore = {
        "T_EquipmentShipDetail": [
            {
                "id": 201,
                "nomenclature": "Updated Propulsion Motor Name",
                "is_synced": True
            }
        ]
    }
    response = client.post("/api/cmms/sfd/sync", json=payload_ignore, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    res = response.json()
    assert res["processed"] == 0
    assert res["ignored"] == 1
    assert res["message"] == "No new records to sync."
    assert len(saved_records) == 0
    assert existing_record.nomenclature == "Original Propulsion Motor"

    # Scenario 2: Newly added record 202 (should insert/update)
    payload_insert = {
        "T_EquipmentShipDetail": [
            {
                "id": 202,
                "nomenclature": "New Auxiliary Pump",
                "is_synced": False
            }
        ]
    }
    response = client.post("/api/cmms/sfd/sync", json=payload_insert, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    res = response.json()
    assert res["processed"] == 1
    assert res["ignored"] == 0
    assert res["message"] == "Sync completed successfully."
    assert len(created_records) == 1
    assert created_records[0]["id"] == 202
    assert created_records[0]["nomenclature"] == "New Auxiliary Pump"


def test_get_sfd_ships(monkeypatch):
    ship = SimpleNamespace(
        id=301,
        name="INS Test",
        code="SHP-301",
        universal_id_m_ship="U-SHIP-301",
        class_code="C-301",
        command=SimpleNamespace(CommandName="Navy Command"),
        authority=SimpleNamespace(OpsAuthority="Navy Authority")
    )
    install_manager(monkeypatch, "Ship", [ship])

    client = build_client()
    response = client.get("/api/cmms/sfd/ships", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "INS Test"
    assert data[0]["command_name"] == "Navy Command"
