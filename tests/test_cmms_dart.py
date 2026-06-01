from datetime import date
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fast_api.dependencies import verify_api_key
from fast_api.routers import cmms


class FakeQuerySet(list):
    def all(self):
        return self

    def order_by(self, *args):
        return self

    def select_related(self, *args):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self[0] if self else None


def install_manager(monkeypatch, model_name, rows):
    model = SimpleNamespace(objects=FakeQuerySet(rows))
    monkeypatch.setattr(cmms, model_name, model)


def build_client():
    app = FastAPI()
    app.include_router(cmms.router, prefix="/api")
    return TestClient(app)


def test_cmms_dart_endpoint_requires_api_key():
    client = build_client()

    response = client.get("/api/cmms/dart")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API Key. Please provide the 'X-API-Key' header."


def test_cmms_dart_endpoint_returns_expected_payload(monkeypatch):
    ship = SimpleNamespace(id=301, code="SHP", name="INS Test", universal_id_m_ship="U-SHIP", active_external=True)
    department = SimpleNamespace(id=201, code="ENG", name="Engineering", universal_id_m_department="U-DEPT", active=1)
    equipment_ship = SimpleNamespace(ship=ship)
    defect = SimpleNamespace(
        id=501,
        dart_number="D-ENG-001",
        dart_sr_number="PREV-001",
        dart_date=date(2026, 5, 20),
        rectification_date=date(2026, 5, 25),
        is_closed=True,
        maintenance_period="REFIT",
        dart_occasion="DL II",
        defective_component="Pump",
        defective_discriptions="Seal leakage",
        RHA_defect="No",
        trial_required=True,
        ops_status=False,
        is_guarantee_defect=False,
        cmms_sync_status=False,
        equipment_ship=equipment_ship,
        department_id=department,
    )
    completion = SimpleNamespace(
        dart_details_id=501,
        repair_agency_code_id=11,
        diagnostic_code_id=12,
        repair_code_id=13,
        delay_code_id=14,
        rectified_date=date(2026, 5, 24),
        days_delay=2,
        spares_delay=1,
        other_reasons="Awaiting spare",
        lesson_learnt="Improve spare readiness",
    )

    install_manager(monkeypatch, "M_Diagnostic", [
        SimpleNamespace(DiagnosticId=12, DiagnosticCode="DG", DiagnosticName="Diagnostic", Universal_ID_M_Diagnostic="U-DG", Active=1)
    ])
    install_manager(monkeypatch, "MRefit", [
        SimpleNamespace(refit_id=21, refit_type="MR", universal_id_m_refit="U-REFIT", active=True)
    ])
    install_manager(monkeypatch, "Ship", [ship])
    install_manager(monkeypatch, "Group", [
        SimpleNamespace(id=31, code="GRP", name="Group", active=1)
    ])
    install_manager(monkeypatch, "Department", [department])
    install_manager(monkeypatch, "M_RepairAgency", [
        SimpleNamespace(RepairAgencyID=11, RepairAgencyCode="RA", RepairAgencyName="Yard", Universal_ID_M_RepairAgency="U-RA", Active=1)
    ])
    install_manager(monkeypatch, "M_Delay", [
        SimpleNamespace(DelayID=14, DelayCode="DL", DelayName="Spares", Universal_ID_M_Delay="U-DL", Active=1)
    ])
    install_manager(monkeypatch, "M_Repair", [
        SimpleNamespace(RepairID=13, RepairCode="RP", RepairName="Replace", Universal_ID_M_Repair="U-RP", Active=1)
    ])
    install_manager(monkeypatch, "Section", [
        SimpleNamespace(id=41, code="SEC", name="Section", active=1)
    ])
    install_manager(monkeypatch, "Initiate_Dart", [defect])
    install_manager(monkeypatch, "Complete_defect_dart", [completion])

    client = build_client()
    response = client.get("/api/cmms/dart", headers={"X-API-Key": "dev-secret-key"})

    assert response.status_code == 200
    payload = response.json()
    assert list(payload.keys()) == [
        "M_Diagnostic",
        "M_Refit",
        "M_Ship",
        "M_group",
        "M_department",
        "M_repair agency",
        "M_Delay",
        "M_Repair",
        "M_section",
        "T_DART",
    ]
    assert payload["M_Diagnostic"][0]["universal_id"] == "U-DG"
    assert payload["M_repair agency"][0]["code"] == "RA"
    assert payload["T_DART"][0]["dart_number"] == "D-ENG-001"
    assert payload["T_DART"][0]["universal_id_m_ship"] == "U-SHIP"
    assert payload["T_DART"][0]["diagnostic_id"] == 12
    assert payload["T_DART"][0]["rectified_date"] == "2026-05-24"


def test_get_defects_list(monkeypatch):
    defect = SimpleNamespace(
        id=501,
        dart_number="D-ENG-001",
        dart_sr_number="PREV-001",
        dart_date=date(2026, 5, 20),
        rectification_date=date(2026, 5, 25),
        is_closed=True,
        defective_discriptions="Seal leakage",
        defective_component="Pump",
        maintenance_period="REFIT",
        is_guarantee_defect=False,
        created_date=date(2026, 5, 20),
    )
    install_manager(monkeypatch, "Initiate_Dart", [defect])
    client = build_client()
    response = client.get("/api/cmms/defects", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["dart_number"] == "D-ENG-001"


def test_get_defect_detail(monkeypatch):
    defect = SimpleNamespace(
        id=501,
        dart_number="D-ENG-001",
        dart_sr_number="PREV-001",
        dart_date=date(2026, 5, 20),
        rectification_date=date(2026, 5, 25),
        is_closed=True,
        defective_discriptions="Seal leakage",
        defective_component="Pump",
        maintenance_period="REFIT",
        is_guarantee_defect=False,
        created_date=date(2026, 5, 20),
    )
    
    def mock_get(id):
        if id == 501:
            return defect
        raise Exception("DoesNotExist")
        
    model = SimpleNamespace(objects=SimpleNamespace(get=mock_get))
    monkeypatch.setattr(cmms, "Initiate_Dart", model)
    
    client = build_client()
    response = client.get("/api/cmms/defects/501", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    assert response.json()["id"] == 501


def test_create_defect(monkeypatch):
    mock_ship_equipment = SimpleNamespace(id=101)
    
    class MockObjects:
        def filter(self, *args, **kwargs):
            return FakeQuerySet([mock_ship_equipment])
            
        def create(self, **kwargs):
            kwargs["id"] = 601
            kwargs["is_closed"] = False
            kwargs["created_date"] = date(2026, 5, 30)
            return SimpleNamespace(**kwargs)
            
    monkeypatch.setattr(cmms, "ShipEquipment", SimpleNamespace(objects=MockObjects()))
    monkeypatch.setattr(cmms, "Initiate_Dart", SimpleNamespace(objects=MockObjects()))
    
    payload = {
        "symptom_code_id": 1,
        "severity_code_id": 2,
        "remark_code_id": 3,
        "require_assistance_for_code_id": 4,
        "equipment_ship_id": 101,
        "department_id_id": 12,
        "equipment_ems_id": 5,
        "dart_number": "D-ENG-002",
        "dart_sr_number": "PREV-002",
        "dart_date": "2026-05-30",
        "rectification_date": None,
        "ops_status": True,
        "trial_required": False,
        "defective_discriptions": "High vibration in motor",
        "defective_component": "Motor",
        "RHA_defect": "Yes",
        "maintenance_period": "OPERATIONAL",
        "dart_occasion": "Routine Check",
        "is_guarantee_defect": True
    }
    
    client = build_client()
    response = client.post("/api/cmms/defects", json=payload, headers={"X-API-Key": "dev-secret-key"})
    print("CREATE DEFECT RESPONSE:", response.status_code, response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 601
    assert data["dart_number"] == "D-ENG-002"
    assert data["defective_component"] == "Motor"


def test_rectify_defect(monkeypatch):
    class FakeTransaction:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
            
    monkeypatch.setattr(cmms, "transaction", SimpleNamespace(atomic=lambda: FakeTransaction()))
    
    defect = SimpleNamespace(
        id=501,
        dart_number="D-ENG-001",
        is_closed=False,
        rectification_date=None,
        save=lambda: None
    )
    
    def mock_get(id):
        if id == 501:
            return defect
        raise Exception("DoesNotExist")
        
    created_complete = []
    
    def mock_create(**kwargs):
        created_complete.append(kwargs)
        return SimpleNamespace(**kwargs)
        
    monkeypatch.setattr(cmms, "Initiate_Dart", SimpleNamespace(objects=SimpleNamespace(get=mock_get)))
    monkeypatch.setattr(cmms, "Complete_defect_dart", SimpleNamespace(objects=SimpleNamespace(create=mock_create)))
    
    rectify_payload = {
        "serial_no": "SR-999",
        "rectified_date": "2026-05-26",
        "repair_agency_code_id": 1,
        "diagnostic_code_id": 2,
        "repair_code_id": 3,
        "delay_code_id": 4,
        "days_delay": 3,
        "spares_delay": 0,
        "other_reasons": "Weather",
        "lesson_learnt": "Plan better"
    }
    
    client = build_client()
    response = client.post("/api/cmms/defects/501/rectify", json=rectify_payload, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert defect.is_closed is True
    assert defect.rectification_date == date(2026, 5, 26)
    assert len(created_complete) == 1
    assert created_complete[0]["serial_no"] == "SR-999"

