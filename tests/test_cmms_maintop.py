from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fast_api.dependencies import verify_api_key
from fast_api.routers import cmms

class FakeTransaction:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class FakeManager:
    def __init__(self, rows=None, callback=None):
        self.rows = rows or []
        self.callback = callback

    def all(self):
        return self.rows

    def filter(self, *args, **kwargs):
        class FilteredList(list):
            def first(self):
                return self[0] if self else None
        return FilteredList(self.rows)

    def update_or_create(self, **kwargs):
        defaults = kwargs.get("defaults", {})
        lookup = {k: v for k, v in kwargs.items() if k != "defaults"}
        lookup_val = list(lookup.values())[0] if lookup else None
        
        if self.callback:
            return self.callback(lookup_val, defaults)
            
        obj = SimpleNamespace(**{**lookup, **defaults})
        self.rows.append(obj)
        return obj, True

def build_client():
    app = FastAPI()
    app.include_router(cmms.router, prefix="/api")
    return TestClient(app)

def test_maintop_auth_missing_key():
    client = build_client()
    response = client.post("/api/cmms/maintop/sync", json={})
    assert response.status_code == 401
    assert "Missing API Key" in response.json()["detail"]

def test_maintop_auth_invalid_key():
    client = build_client()
    response = client.post("/api/cmms/maintop/sync", json={}, headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403
    assert "Invalid API Key" in response.json()["detail"]

def test_maintop_sync_endpoint(monkeypatch):
    headers_created = []
    details_created = []

    def mock_header_callback(uid, defaults):
        defaults["universal_id_t_maintopheader"] = uid
        obj = SimpleNamespace(
            maintop_id=defaults.get("maintop_id"),
            maintop_no=defaults.get("maintop_no"),
            maintop_title=defaults.get("maintop_title"),
            amendment_no=defaults.get("amendment_no"),
            active=defaults.get("active"),
            universal_id_t_maintopheader=uid
        )
        headers_created.append(obj)
        return obj, True

    def mock_detail_callback(uid, defaults):
        defaults["universal_id_t_maintopdetail"] = uid
        obj = SimpleNamespace(
            routine_id=defaults.get("routine_id"),
            universal_id_t_maintopdetail=uid
        )
        details_created.append(obj)
        return obj, True

    monkeypatch.setattr(cmms, "transaction", SimpleNamespace(atomic=lambda: FakeTransaction()))
    monkeypatch.setattr(cmms, "MaintopHeader", SimpleNamespace(objects=FakeManager(callback=mock_header_callback)))
    monkeypatch.setattr(cmms, "MaintopDetail", SimpleNamespace(objects=FakeManager(callback=mock_detail_callback)))

    payload = {
        "T_maintopheader": [
            {
                "MaintopID": 1001,
                "MaintopNo": "MT-ENG-001",
                "MaintopTitle": "Auxiliary Engine Routine Maintenance",
                "AmendmentNo": 0,
                "Active": 1,
                "Universal_ID_T_MaintopHeader": "U-MH-1001"
            }
        ],
        "T_maintopdetail": [
            {
                "RoutineID": 5001,
                "MaintopID": 1001,
                "MaintopNo": "MT-ENG-001",
                "RoutineNo": "R-1",
                "RoutineDescription": "Inspect stator windings for moisture",
                "Frequency": "Monthly",
                "Active": 1,
                "Universal_ID_T_MaintopHeader": "U-MH-1001",
                "Universal_ID_T_MaintopDetail": "U-MD-5001"
            }
        ]
    }

    client = build_client()
    response = client.post(
        "/api/cmms/maintop/sync",
        json=payload,
        headers={"X-API-Key": "dev-secret-key"}
    )

    if response.status_code != 200:
        print("SYNC FAILURE RESPONSE:", response.status_code, response.json())

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] is True
    assert res_data["headers_processed"] == 1
    assert res_data["details_processed"] == 1
    assert len(headers_created) == 1
    assert len(details_created) == 1
    assert headers_created[0].maintop_id == 1001
    assert details_created[0].routine_id == 5001

def test_maintop_jic_endpoint(monkeypatch):
    jics_created = []
    spares_created = []
    tools_created = []
    attachments_created = []

    def mock_jic_callback(uid, defaults):
        obj = SimpleNamespace(**defaults)
        jics_created.append(obj)
        return obj, True

    def mock_spare_callback(uid, defaults):
        obj = SimpleNamespace(**defaults)
        spares_created.append(obj)
        return obj, True

    def mock_tool_callback(uid, defaults):
        obj = SimpleNamespace(**defaults)
        tools_created.append(obj)
        return obj, True

    def mock_attachment_callback(uid, defaults):
        obj = SimpleNamespace(**defaults)
        attachments_created.append(obj)
        return obj, True

    monkeypatch.setattr(cmms, "transaction", SimpleNamespace(atomic=lambda: FakeTransaction()))
    monkeypatch.setattr(cmms, "T_maintopJIC", SimpleNamespace(objects=FakeManager(callback=mock_jic_callback)))
    monkeypatch.setattr(cmms, "T_JICspares", SimpleNamespace(objects=FakeManager(callback=mock_spare_callback)))
    monkeypatch.setattr(cmms, "T_JICtools", SimpleNamespace(objects=FakeManager(callback=mock_tool_callback)))
    monkeypatch.setattr(cmms, "T_JICattachments", SimpleNamespace(objects=FakeManager(callback=mock_attachment_callback)))

    payload = {
        "T_maintopJIC": [
            {
                "JICID": 401,
                "Universal_ID_T_MaintopJIC": "U-JIC-401",
                "Universal_ID_T_MaintopDetail": "U-MD-5001",
                "JobSteps": "1. Disconnect power. 2. Remove stator cover. 3. Perform megger test."
            }
        ],
        "T_JICspares": [
            {
                "JICID": 401,
                "SpareItemCode": "SP-908A",
                "Quantity": 1,
                "Universal_ID_T_JICspares": "U-JS-801"
            }
        ],
        "T_JICtools": [
            {
                "JICID": 401,
                "ToolCode": "TL-MEGGER-01",
                "ToolName": "Megohmmeter 500V",
                "Universal_ID_T_JICtools": "U-JT-901"
            }
        ],
        "T_JICattachments": [
            {
                "JICID": 401,
                "FileName": "megger_test_procedure.pdf",
                "FileUrl": "http://cmms.local/docs/megger.pdf",
                "Universal_ID_T_JICattachments": "U-JA-001"
            }
        ]
    }

    client = build_client()
    response = client.post(
        "/api/cmms/maintop/jic",
        json=payload,
        headers={"X-API-Key": "dev-secret-key"}
    )

    if response.status_code != 200:
        print("JIC FAILURE RESPONSE:", response.status_code, response.json())

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] is True
    assert res_data["jics_processed"] == 1
    assert res_data["spares_processed"] == 1
    assert res_data["tools_processed"] == 1
    assert res_data["attachments_processed"] == 1
    assert len(jics_created) == 1
    assert len(spares_created) == 1
    assert len(tools_created) == 1
    assert len(attachments_created) == 1

def test_maintop_distribution_endpoint(monkeypatch):
    addresses_created = []
    dist_addresses_created = []
    list_dists_created = []
    library_dists_created = []

    def mock_addr_callback(uid, defaults):
        obj = SimpleNamespace(**defaults)
        addresses_created.append(obj)
        return obj, True

    def mock_dist_addr_callback(uid, defaults):
        obj = SimpleNamespace(**defaults)
        dist_addresses_created.append(obj)
        return obj, True

    def mock_list_dist_callback(uid, defaults):
        obj = SimpleNamespace(**defaults)
        list_dists_created.append(obj)
        return obj, True

    def mock_library_dist_callback(uid, defaults):
        obj = SimpleNamespace(**defaults)
        library_dists_created.append(obj)
        return obj, True

    monkeypatch.setattr(cmms, "transaction", SimpleNamespace(atomic=lambda: FakeTransaction()))
    monkeypatch.setattr(cmms, "M_address", SimpleNamespace(objects=FakeManager(callback=mock_addr_callback)))
    monkeypatch.setattr(cmms, "M_distribution_address", SimpleNamespace(objects=FakeManager(callback=mock_dist_addr_callback)))
    monkeypatch.setattr(cmms, "T_maintoplistdist", SimpleNamespace(objects=FakeManager(callback=mock_list_dist_callback)))
    monkeypatch.setattr(cmms, "T_MaintoplibraryDisDef", SimpleNamespace(objects=FakeManager(callback=mock_library_dist_callback)))

    payload = {
        "M_address": [
            {
                "AddressID": 10,
                "AddressName": "Eastern Command Headquarters",
                "Universal_ID_M_Address": "U-ADDR-10"
            }
        ],
        "M_distribution_address": [
            {
                "DistAddressID": 20,
                "AddressID": 10,
                "DistName": "Technical Library Alpha",
                "Universal_ID_M_DistributionAddress": "U-DA-20"
            }
        ],
        "T_maintoplistdist": [
            {
                "MaintopID": 1001,
                "DistAddressID": 20,
                "Active": 1,
                "Universal_ID_T_MaintopListDist": "U-LD-301"
            }
        ],
        "T_MaintoplibraryDisDef": [
            {
                "LibraryID": 1,
                "DefaultAddressID": 10,
                "IsDefaultActive": 1,
                "Universal_ID_T_MaintopLibraryDisDef": "U-LDD-501"
            }
        ]
    }

    client = build_client()
    response = client.post(
        "/api/cmms/maintop/distribution",
        json=payload,
        headers={"X-API-Key": "dev-secret-key"}
    )

    if response.status_code != 200:
        print("DISTRIBUTION FAILURE RESPONSE:", response.status_code, response.json())

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] is True
    assert res_data["addresses_processed"] == 1
    assert res_data["distributions_processed"] == 1
    assert res_data["defaults_processed"] == 1
    assert len(addresses_created) == 1
    assert len(dist_addresses_created) == 1
    assert len(list_dists_created) == 1
    assert len(library_dists_created) == 1
