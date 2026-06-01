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


def test_refit_endpoint_requires_api_key():
    client = build_client()
    response = client.get("/api/cmms/refit")
    assert response.status_code == 401


def test_refit_sync_payload(monkeypatch):
    delinquency = SimpleNamespace(
        DelinqueryID=1,
        DelinqueryCode="DQ-001",
        DelinqueryName="Delays",
        Active=True,
        Universal_ID_M_Delinquery="U-DQ-001"
    )
    detail = SimpleNamespace(
        RefComDelinqueryDetailID=10,
        Universal_ID_T_RefComp="U-RC-101",
        DelinqueryCode="DQ-001",
        Description="Spare shortage",
        DaysDelayed=5,
        Remarks="None",
        Universal_ID_T_RefComDelinqueryDetail="U-RCD-10"
    )
    refit_category = SimpleNamespace(refit_category_id=1, refit_category_name="Short Refit")
    refit = SimpleNamespace(
        refit_id=2,
        refit_type="SR",
        description="Short Refit Details",
        universal_id_m_refit="U-RF-002",
        active=True,
        refit_category_f_key=refit_category
    )
    drydock = SimpleNamespace(
        DryDockingID=20,
        Universal_ID_T_RefComp="U-RC-101",
        DockEntryDate=date(2026, 6, 5),
        DockUndockDate=date(2026, 6, 10),
        YardDockName="Dock 1",
        HullInspectionStatus="Passed",
        Universal_ID_T_DryDocking="U-DD-20"
    )
    ocr = SimpleNamespace(
        OCRID=30,
        Universal_ID_T_RefComp="U-RC-101",
        ReportRefNo="OCR-88",
        ClearanceStatus="Passed",
        TrialOutcome="Satisfactory",
        ReportDate=date(2026, 6, 14),
        Universal_ID_M_OCR="U-OCR-30"
    )
    refcomp = SimpleNamespace(
        id=101,
        name="SR",
        maintenance_period="Refit",
        occasion="Refit",
        plan_start_date=date(2026, 6, 1),
        plan_end_date=date(2026, 6, 15),
        actual_start_date=date(2026, 6, 2),
        actual_end_date=None,
        Universal_ID_T_RefComp="U-RC-101",
        Universal_ID_M_Command="CMD-1",
        Universal_ID_M_Ship="U-SHIP-1",
        Universal_ID_M_Refit="U-RF-002",
        Universal_ID_M_RefitPlace="Dockyard",
        ship_universal_f_key=SimpleNamespace(universal_id_m_ship="U-SHIP-1"),
        universal_m_refit=refit,
        refit_category_f_key=refit_category
    )

    install_manager(monkeypatch, "M_Delinquery", [delinquency])
    install_manager(monkeypatch, "T_RefComDelinqueryDetail", [detail])
    install_manager(monkeypatch, "MRefit", [refit])
    install_manager(monkeypatch, "T_DryDocking", [drydock])
    install_manager(monkeypatch, "M_OCR", [ocr])
    install_manager(monkeypatch, "RefitMaintenancePeriod", [refcomp])

    client = build_client()
    response = client.get("/api/cmms/refit", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    payload = response.json()
    assert list(payload.keys()) == [
        "M_Delinquery",
        "T_RefComDelinquery Detail",
        "M_Refit",
        "T_DryDocking",
        "M-OCR",
        "T_Refcomp"
    ]
    assert payload["M_Delinquery"][0]["code"] == "DQ-001"
    assert payload["T_Refcomp"][0]["universal_id_t_refcomp"] == "U-RC-101"


def test_get_refit_completions(monkeypatch):
    refcomp = SimpleNamespace(
        id=101,
        name="SR",
        maintenance_period="Refit",
        occasion="Refit",
        plan_start_date=date(2026, 6, 1),
        plan_end_date=date(2026, 6, 15),
        actual_start_date=date(2026, 6, 2),
        actual_end_date=None,
        Universal_ID_T_RefComp="U-RC-101",
        Universal_ID_M_Command="CMD-1",
        Universal_ID_M_Ship="U-SHIP-1",
        Universal_ID_M_Refit="U-RF-002",
        Universal_ID_M_RefitPlace="Dockyard",
    )
    install_manager(monkeypatch, "RefitMaintenancePeriod", [refcomp])

    client = build_client()
    response = client.get("/api/cmms/refit/completions", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_create_refit_completion(monkeypatch):
    ship = SimpleNamespace(id=1, universal_id_m_ship="SHP-001")
    refit_category = SimpleNamespace(refit_category_id=1)
    refit = SimpleNamespace(refit_id=2, refit_type="SHORT", universal_id_m_refit="U-RF-002", refit_category_f_key=refit_category)

    monkeypatch.setattr(cmms.Ship.objects, "filter", lambda **k: FakeQuerySet([ship]))
    monkeypatch.setattr(cmms.MRefit.objects, "filter", lambda **k: FakeQuerySet([refit]))
    monkeypatch.setattr(cmms.MRefitCategory.objects, "filter", lambda **k: FakeQuerySet([refit_category]))

    created_objs = []
    def mock_create(**kwargs):
        kwargs["id"] = 701
        kwargs["Universal_ID_T_RefComp"] = "U-RC-CREATED"
        obj = SimpleNamespace(**kwargs)
        created_objs.append(obj)
        return obj

    monkeypatch.setattr(cmms.RefitMaintenancePeriod.objects, "create", mock_create)

    payload = {
        "ship_code": "SHP-001",
        "refit_type": "SHORT",
        "planned_start_date": "2026-06-01",
        "planned_end_date": "2026-06-15",
        "actual_start_date": "2026-06-02",
        "actual_end_date": None,
        "refit_place": "Dockyard Alpha",
        "universal_id_m_command": "CMD-101"
    }

    client = build_client()
    response = client.post("/api/cmms/refit/completions", json=payload, headers={"X-API-Key": "dev-secret-key"})
    print("CREATE REFIT COMPLETION RESP:", response.status_code, response.json())
    assert response.status_code == 201
    assert response.json()["Universal_ID_T_RefComp"] == "U-RC-CREATED"


def test_log_refit_delinquency(monkeypatch):
    created_objs = []
    def mock_create(**kwargs):
        kwargs["RefComDelinqueryDetailID"] = 12
        obj = SimpleNamespace(**kwargs)
        created_objs.append(obj)
        return obj

    monkeypatch.setattr(cmms.T_RefComDelinqueryDetail.objects, "create", mock_create)

    payload = {
        "delinquency_code": "DLQ-201",
        "description": "Delay in provisioning",
        "days_delayed": 5,
        "remarks": "None"
    }

    client = build_client()
    response = client.post("/api/cmms/refit/completions/U-RC-101/delinquency", json=payload, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(created_objs) == 1
    assert created_objs[0].DelinqueryCode == "DLQ-201"


def test_log_refit_drydock(monkeypatch):
    created_objs = []
    def mock_create(**kwargs):
        kwargs["DryDockingID"] = 22
        obj = SimpleNamespace(**kwargs)
        created_objs.append(obj)
        return obj

    monkeypatch.setattr(cmms.T_DryDocking.objects, "create", mock_create)

    payload = {
        "dock_entry_date": "2026-06-05",
        "dock_undock_date": "2026-06-10",
        "yard_dock_name": "Dry Dock #2",
        "hull_inspection_status": "Passed"
    }

    client = build_client()
    response = client.post("/api/cmms/refit/completions/U-RC-101/drydock", json=payload, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(created_objs) == 1
    assert created_objs[0].YardDockName == "Dry Dock #2"


def test_log_refit_ocr(monkeypatch):
    created_objs = []
    def mock_create(**kwargs):
        kwargs["OCRID"] = 32
        obj = SimpleNamespace(**kwargs)
        created_objs.append(obj)
        return obj

    monkeypatch.setattr(cmms.M_OCR.objects, "create", mock_create)

    payload = {
        "report_ref_no": "OCR/2026/ENG/88",
        "clearance_status": "Fully Cleared",
        "trial_outcome": "Sea trial successful",
        "report_date": "2026-06-14"
    }

    client = build_client()
    response = client.post("/api/cmms/refit/completions/U-RC-101/ocr", json=payload, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(created_objs) == 1
    assert created_objs[0].ReportRefNo == "OCR/2026/ENG/88"
