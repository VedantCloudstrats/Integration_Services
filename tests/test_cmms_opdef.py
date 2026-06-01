from datetime import date, datetime
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


def test_opdef_endpoint_requires_api_key():
    client = build_client()
    response = client.get("/api/cmms/opdef")
    assert response.status_code == 401


def test_get_opdef_payload_sync(monkeypatch):
    opdef_main = SimpleNamespace(
        OpdefMainID=801,
        Universal_ID_M_Ship="U-SHIP-301",
        Universal_ID_T_EquipmentShipDetail="U-EQ-101",
        OpdefNumber="OPD-ENG-2026-004",
        OpdefDate=date(2026, 5, 30),
        DepartmentID=12,
        DefectDescription="Excessive overheating in stator coils",
        Universal_ID_T_OpdefMain="U-OPD-801"
    )
    gen_info = SimpleNamespace(
        OpdefGeneratInfoID=901,
        Universal_ID_T_OpdefMain="U-OPD-801",
        OperationalImpact="Loss of auxiliary propulsion capacity",
        Universal_ID_T_OpdefGeneratInfo="U-OPDG-901"
    )
    analysis = SimpleNamespace(
        DefectAnalysisID=201,
        Universal_ID_T_OpdefMain="U-OPD-801",
        AnalysisDate=date(2026, 5, 30),
        FailureCause="Insulation breakdown",
        RectificationMethodProposed="Rewind stator",
        AnalysedBy="Senior Engineer",
        Universal_ID_T_DefectAnalysis="U-OPDA-201"
    )
    spare = SimpleNamespace(
        MajorSpareConsumerID=301,
        Universal_ID_T_OpdefMain="U-OPD-801",
        SpareItemCode="SP-7712-A",
        Nomenclature="Stator Coil Assembly",
        QuantityConsumed=1,
        UnitCost=23500.0,
        Remarks="Replaced completely",
        Universal_ID_T_MajorSpareConsumer="U-OPDS-301"
    )
    trial = SimpleNamespace(
        TrialConductedParameterID=401,
        Universal_ID_T_OpdefMain="U-OPD-801",
        TrialDate=date(2026, 5, 31),
        RPMReading=1200,
        TemperatureCelsius=68.5,
        VibrationVelocityMMS=1.8,
        Status="Satisfactory",
        Universal_ID_T_TrialConductedParameter="U-OPDT-401"
    )
    prior_param = SimpleNamespace(
        OpdefPriorParameterID=501,
        Universal_ID_T_OpdefMain="U-OPD-801",
        ReadingTime=datetime(2026, 5, 30, 10, 15, 0),
        RPMReading=1150,
        TemperatureCelsius=98.2,
        VibrationVelocityMMS=4.5,
        Remarks="Temperature spiked",
        Universal_ID_T_OpdefPriorParameter="U-OPDP-501"
    )
    photo = SimpleNamespace(
        PhotographID=601,
        Universal_ID_T_OpdefMain="U-OPD-801",
        FilePath="/media/opdef_photos/stator_burn_801.jpg",
        Description="Burned coils",
        UploadedDate=datetime(2026, 5, 30, 11, 0, 0),
        Universal_ID_T_Photograph="U-OPDPH-601"
    )

    install_manager(monkeypatch, "T_OpdefMain", [opdef_main])
    install_manager(monkeypatch, "T_opdefgeneratinfo", [gen_info])
    install_manager(monkeypatch, "T_DefectAnalysis", [analysis])
    install_manager(monkeypatch, "T_MajorSpareconsumer", [spare])
    install_manager(monkeypatch, "T_trailconductedParameter", [trial])
    install_manager(monkeypatch, "T_opdefpriorparameter", [prior_param])
    install_manager(monkeypatch, "T_photograph", [photo])

    client = build_client()
    response = client.get("/api/cmms/opdef", headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    payload = response.json()
    assert "T_OpdefMain" in payload
    assert "T_opdefgeneratinfo" in payload
    assert len(payload["T_OpdefMain"]) == 1
    assert payload["T_OpdefMain"][0]["OpdefNumber"] == "OPD-ENG-2026-004"


def test_initiate_opdef(monkeypatch):
    created_main = []
    created_gen = []

    def mock_create_main(**kwargs):
        kwargs["OpdefMainID"] = 801
        kwargs["Universal_ID_T_OpdefMain"] = "U-OPD-801"
        obj = SimpleNamespace(**kwargs)
        created_main.append(obj)
        return obj

    def mock_create_gen(**kwargs):
        kwargs["OpdefGeneratInfoID"] = 901
        kwargs["Universal_ID_T_OpdefGeneratInfo"] = "U-OPDG-901"
        obj = SimpleNamespace(**kwargs)
        created_gen.append(obj)
        return obj

    class FakeTransaction:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr(cmms, "transaction", SimpleNamespace(atomic=lambda: FakeTransaction()))
    monkeypatch.setattr(cmms.T_OpdefMain.objects, "create", mock_create_main)
    monkeypatch.setattr(cmms.T_opdefgeneratinfo.objects, "create", mock_create_gen)

    payload = {
        "ship_id": 301,
        "fitted_equipment_id": 101,
        "opdef_number": "OPD-ENG-2026-004",
        "opdef_date": "2026-05-30",
        "operational_impact": "Loss of auxiliary propulsion capacity",
        "department_id": 12,
        "defect_description": "Excessive overheating in stator coils"
    }

    client = build_client()
    response = client.post("/api/cmms/opdef", json=payload, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 201
    res = response.json()
    assert res["Universal_ID_T_OpdefMain"] == "U-OPD-801"
    assert len(created_main) == 1
    assert len(created_gen) == 1
    assert created_gen[0].OperationalImpact == "Loss of auxiliary propulsion capacity"


def test_submit_defect_analysis(monkeypatch):
    created_objs = []
    def mock_create(**kwargs):
        kwargs["DefectAnalysisID"] = 201
        kwargs["Universal_ID_T_DefectAnalysis"] = "U-OPDA-201"
        obj = SimpleNamespace(**kwargs)
        created_objs.append(obj)
        return obj

    monkeypatch.setattr(cmms.T_DefectAnalysis.objects, "create", mock_create)
    # mock T_OpdefMain.objects.get to return a dummy main opdef
    dummy_opdef = SimpleNamespace(Universal_ID_T_OpdefMain="U-OPD-801")
    monkeypatch.setattr(cmms.T_OpdefMain.objects, "get", lambda **k: dummy_opdef)

    payload = {
        "analysis_date": "2026-05-30",
        "failure_cause": "Insulation breakdown due to moisture ingress",
        "rectification_method_proposed": "Rewind stator and improve seals",
        "analysed_by": "Senior Engineer (Electrical)"
    }

    client = build_client()
    response = client.post("/api/cmms/opdef/801/analysis", json=payload, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(created_objs) == 1
    assert created_objs[0].Universal_ID_T_OpdefMain == "U-OPD-801"


def test_log_major_spares_consumed(monkeypatch):
    created_objs = []
    def mock_create(**kwargs):
        kwargs["MajorSpareConsumerID"] = 301
        kwargs["Universal_ID_T_MajorSpareConsumer"] = "U-OPDS-301"
        obj = SimpleNamespace(**kwargs)
        created_objs.append(obj)
        return obj

    monkeypatch.setattr(cmms.T_MajorSpareconsumer.objects, "create", mock_create)
    dummy_opdef = SimpleNamespace(Universal_ID_T_OpdefMain="U-OPD-801")
    monkeypatch.setattr(cmms.T_OpdefMain.objects, "get", lambda **k: dummy_opdef)

    payload = {
        "spare_item_code": "SP-7712-A",
        "nomenclature": "Stator Coil Assembly",
        "quantity_consumed": 1,
        "unit_cost": 23500.0,
        "remarks": "Replaced completely"
    }

    client = build_client()
    response = client.post("/api/cmms/opdef/801/spares", json=payload, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(created_objs) == 1
    assert created_objs[0].SpareItemCode == "SP-7712-A"


def test_log_trial_parameters(monkeypatch):
    created_objs = []
    def mock_create(**kwargs):
        kwargs["TrialConductedParameterID"] = 401
        kwargs["Universal_ID_T_TrialConductedParameter"] = "U-OPDT-401"
        obj = SimpleNamespace(**kwargs)
        created_objs.append(obj)
        return obj

    monkeypatch.setattr(cmms.T_trailconductedParameter.objects, "create", mock_create)
    dummy_opdef = SimpleNamespace(Universal_ID_T_OpdefMain="U-OPD-801")
    monkeypatch.setattr(cmms.T_OpdefMain.objects, "get", lambda **k: dummy_opdef)

    payload = {
        "trial_date": "2026-05-31",
        "rpm_reading": 1200,
        "temperature_celsius": 68.5,
        "vibration_velocity_mms": 1.8,
        "status": "Satisfactory"
    }

    client = build_client()
    response = client.post("/api/cmms/opdef/801/trials", json=payload, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(created_objs) == 1
    assert created_objs[0].RPMReading == 1200


def test_record_pre_failure_parameters(monkeypatch):
    created_objs = []
    def mock_create(**kwargs):
        kwargs["OpdefPriorParameterID"] = 501
        kwargs["Universal_ID_T_OpdefPriorParameter"] = "U-OPDP-501"
        obj = SimpleNamespace(**kwargs)
        created_objs.append(obj)
        return obj

    monkeypatch.setattr(cmms.T_opdefpriorparameter.objects, "create", mock_create)
    dummy_opdef = SimpleNamespace(Universal_ID_T_OpdefMain="U-OPD-801")
    monkeypatch.setattr(cmms.T_OpdefMain.objects, "get", lambda **k: dummy_opdef)

    payload = {
        "reading_time": "2026-05-30T10:15:00",
        "rpm_reading": 1150,
        "temperature_celsius": 98.2,
        "vibration_velocity_mms": 4.5,
        "remarks": "Temperature spiked quickly shortly before tripping"
    }

    client = build_client()
    response = client.post("/api/cmms/opdef/801/prior-parameters", json=payload, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(created_objs) == 1
    assert float(created_objs[0].TemperatureCelsius) == 98.2


def test_upload_photograph(monkeypatch):
    created_objs = []
    def mock_create(**kwargs):
        kwargs["PhotographID"] = 601
        kwargs["Universal_ID_T_Photograph"] = "U-OPDPH-601"
        obj = SimpleNamespace(**kwargs)
        created_objs.append(obj)
        return obj

    monkeypatch.setattr(cmms.T_photograph.objects, "create", mock_create)
    dummy_opdef = SimpleNamespace(Universal_ID_T_OpdefMain="U-OPD-801")
    monkeypatch.setattr(cmms.T_OpdefMain.objects, "get", lambda **k: dummy_opdef)

    client = build_client()
    files = {"file": ("stator_burn_801.jpg", b"fake_jpeg_content", "image/jpeg")}
    data = {"description": "Burned coils"}
    response = client.post("/api/cmms/opdef/801/photographs", files=files, data=data, headers={"X-API-Key": "dev-secret-key"})
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert "associated successfully" in res["message"]
    assert len(created_objs) == 1
    assert created_objs[0].Description == "Burned coils"
