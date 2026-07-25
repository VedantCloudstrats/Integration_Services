from unittest import TestCase
from unittest.mock import patch
from fastapi.testclient import TestClient
from django.contrib.auth import get_user_model

from integrationservices.main import app
from sfd.models import (
    SFDTransaction,
    ChangeEquipmentRequest,
    RemoveEquipmentRequest,
)
from master.models import (
    CommandMaster,
    CountryMaster,
    DepartmentMaster,
    EquipmentMaster,
    PropulsionMaster,
    ShipCategoryMaster,
    ShipMaster,
    SubDepartmentMaster,
    SupplierMaster,
)
from integrationservices.services import (
    pull_all_masters,
    push_to_cmms,
    run_unified_sync,
)

User = get_user_model()


class IntegrationServicesTests(TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Create or fetch test user
        self.user, _ = User.objects.get_or_create(
            username="testuser",
            defaults={"email": "testuser@example.com"}
        )

        # Create prerequisite master objects for test equipment
        self.ship, _ = ShipMaster.objects.get_or_create(
            universal_id_m_ship="SHIP-U-01",
            defaults={"ship_name": "Test Ship", "ship_code": "TS"}
        )
        self.department, _ = DepartmentMaster.objects.get_or_create(
            universal_id_m_department="DEPT-U-01",
            defaults={"name": "HULL", "code": "HL"}
        )
        self.equipment, _ = EquipmentMaster.objects.get_or_create(
            universal_id_m_equipment="EQ-U-01",
            defaults={"equipment_code": "EQ-001", "equipment_name": "Test Eq", "equipment_model": "Model X"}
        )
        self.supplier, _ = SupplierMaster.objects.get_or_create(
            universal_id_M_supplier="SUP-U-01",
            defaults={"supplier_name": "Supplier A", "email_id": "test@example.com", "active": True, "supplier_manufacture": 1, "city": "Unknown"}
        )
        self.sub_department, _ = SubDepartmentMaster.objects.get_or_create(
            universal_id_m_sub_department="SUBDEPT-U-01",
            defaults={"name": "SubDept A", "universal_id_m_department": "DEPT-U-01", "department": self.department, "active": True}
        )

        # Create dummy ShipEquipment
        self.ship_equipment, _ = SFDTransaction.objects.get_or_create(
            universal_id_t_equipment_ship_detail="SHIP-DET-U-01",
            defaults={
                "ship": self.ship,
                "equipment": self.equipment,
                "nomenclature": "Test Nomenclature",
                "location_code": "1",
                "location_on_board": "Fwd Section",
                "no_of_fits": 2,
                "equipment_sr_no": "SN-9988",
                "oem_part_no": "OEM-XYZ",
                "remark": "Initial Remark",
                "is_synced": 0,
            }
        )

        # Create dummy SFDChangeRequest
        self.change_request, _ = ChangeEquipmentRequest.objects.get_or_create(
            universal_id_t_sfd_change_request="CHANGE-U-01",
            defaults={
                "equipment_ship_id": self.ship_equipment,
                "equipment": "New Equipment",
                "model": "Model Y",
                "supplier": "Supplier Alpha",
                "manufacture": "OEM Beta",
                "active": True,
                "is_synced": 0,
            }
        )

    def test_status_endpoint(self):
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "active")
        self.assertEqual(data["app"], "integrationservices")
        self.assertIn("sync_status", data)

    @patch("integrationservices.services.execute_cmms_query")
    def test_transaction_push_to_cmms(self, mock_execute):
        self.ship_equipment.is_synced = 0
        self.ship_equipment.save()
        res = push_to_cmms()
        self.assertEqual(res["status"], "success")
        self.ship_equipment.refresh_from_db()
        self.assertEqual(self.ship_equipment.is_synced, 2)
        self.assertTrue(mock_execute.called)

    @patch("integrationservices.services.fetch_cmms_table_data")
    def test_pull_masters_success(self, mock_fetch):
        def side_effect(query, params=None):
            if "M_Country" in query:
                return [{"CountryID": 10, "CountryCode": "IND", "CountryName": "India", "Active": True, "Universal_ID_M_Country": "CTRY-U-01"}]
            elif "M_Command" in query:
                return [{"CommandID": 5, "CommandName": "WNC", "CommandCode": "WNC", "Active": True, "Universal_ID_M_Command": "CMD-U-01"}]
            elif "M_ShipCategory" in query:
                return [{"ShipCategoryID": 3, "ShipCategoryName": "Frigate", "Active": True, "Universal_ID_M_ShipCategory": "CAT-U-01"}]
            elif "M_Propulsion" in query:
                return [{"PropulsionID": 1, "PropulsionName": "Diesel", "Active": True, "Universal_ID_M_Propulsion": "PROP-U-01"}]
            elif "Ch_Master_Equipment_Type" in query:
                return [{"Equipment_Type_ID": 44, "Equipment_Desc": "Type Ingest", "Status": 1, "Universal_ID_Ch_Master_Equipment_Type": "EQ-TYPE-U-44"}]
            elif "M_Department" in query:
                return [{"DepartmentID": 88, "Description": "HULL", "DeptCode": "HL", "Active": True, "Universal_ID_M_Department": "DEPT-U-88"}]
            elif "M_Supplier" in query:
                return [{"SupplierID": 66, "SupplierCode": "SUP-66", "SupplierName": "Supplier A", "Active": True, "Universal_ID_M_Supplier": "SUP-U-66"}]
            elif "M_OpsAuthority" in query:
                return [{"AuthorityID": 8, "OpsCode": 100, "OpsAuthority": "FOC", "CommandID": 5, "CommandName": "WN", "Active": True, "Universal_ID_M_OpsAuthority": "AUTH-U-01", "Universal_ID_M_Command": "CMD-U-01", "Address": "Mumbai"}]
            elif "M_Ship" in query:
                return [{"ShipID": 99, "ShipSrNo": "1", "ShipCode": "S99", "ShipName": "Test Ship", "Universal_ID_M_Ship": "SHIP-U-01", "Active": True}]
            elif "M_SubDepartment" in query:
                return [{"SubDepartmentID": 33, "Description": "SubDept", "SubDeptCode": "SDI", "Active": True, "Universal_ID_M_Department": "DEPT-U-88", "Universal_ID_M_SubDepartment": "SUBDEPT-U-01"}]
            elif "M_Equipment" in query:
                return [{"EquipmentID": 77, "EquipmentCode": "EQ-001", "EquipmentName": "Test Eq", "EquipmentModel": "Model X", "Active": True, "Universal_ID_M_Equipment": "EQ-U-01"}]
            return []

        mock_fetch.side_effect = side_effect
        res = pull_all_masters()
        self.assertEqual(res["status"], "success")

        self.assertTrue(CountryMaster.objects.filter(universal_id_m_country="CTRY-U-01").exists())
        self.assertTrue(CommandMaster.objects.filter(universal_id_m_command="CMD-U-01").exists())

    def test_status_summary_endpoint(self):
        SFDTransaction.objects.all().update(is_synced=0)
        ChangeEquipmentRequest.objects.all().update(is_synced=0)
        RemoveEquipmentRequest.objects.all().update(is_synced=0)

        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["sync_status"], "not_synced")

        SFDTransaction.objects.all().update(is_synced=1)
        ChangeEquipmentRequest.objects.all().update(is_synced=1)
        RemoveEquipmentRequest.objects.all().update(is_synced=1)

        response = self.client.get("/status")
        data = response.json()
        self.assertEqual(data["sync_status"], "synced")

    @patch("integrationservices.services.execute_cmms_query")
    @patch("integrationservices.services.fetch_cmms_table_data")
    def test_complete_sync_workflow_via_api(self, mock_fetch, mock_execute):
        from django.core.cache import cache
        cache.delete("cmms_sync_in_progress_lock")

        def side_effect(query, params=None):
            if "M_Country" in query:
                return [{"CountryID": 10, "CountryCode": "IND", "CountryName": "India", "Active": True, "Universal_ID_M_Country": "CTRY-U-01"}]
            elif "M_Command" in query:
                return [{"CommandID": 5, "CommandName": "WNC", "CommandCode": "WNC", "Active": True, "Universal_ID_M_Command": "CMD-U-01"}]
            elif "M_ShipCategory" in query:
                return [{"ShipCategoryID": 3, "ShipCategoryName": "Frigate", "Active": True, "Universal_ID_M_ShipCategory": "CAT-U-01"}]
            elif "M_Propulsion" in query:
                return [{"PropulsionID": 1, "PropulsionName": "Diesel", "Active": True, "Universal_ID_M_Propulsion": "PROP-U-01"}]
            elif "Ch_Master_Equipment_Type" in query:
                return [{"Equipment_Type_ID": 44, "Equipment_Desc": "Type Ingest", "Status": 1, "Universal_ID_Ch_Master_Equipment_Type": "EQ-TYPE-U-44"}]
            elif "M_Department" in query:
                return [{"DepartmentID": 88, "Description": "HULL", "DeptCode": "HL", "Active": True, "Universal_ID_M_Department": "DEPT-U-88"}]
            elif "M_Supplier" in query:
                return [{"SupplierID": 66, "SupplierCode": "SUP-66", "SupplierName": "Supplier A", "Active": True, "Universal_ID_M_Supplier": "SUP-U-66"}]
            elif "M_OpsAuthority" in query:
                return [{"AuthorityID": 8, "OpsCode": 100, "OpsAuthority": "FOC", "CommandID": 5, "CommandName": "WN", "Active": True, "Universal_ID_M_OpsAuthority": "AUTH-U-01", "Universal_ID_M_Command": "CMD-U-01", "Address": "Mumbai"}]
            elif "M_Ship" in query:
                return [{"ShipID": 99, "ShipSrNo": "1", "ShipCode": "S99", "ShipName": "Test Ship", "Universal_ID_M_Ship": "SHIP-U-01", "Active": True}]
            elif "M_SubDepartment" in query:
                return [{"SubDepartmentID": 33, "Description": "SubDept", "SubDeptCode": "SDI", "Active": True, "Universal_ID_M_Department": "DEPT-U-88", "Universal_ID_M_SubDepartment": "SUBDEPT-U-01"}]
            elif "M_Equipment" in query:
                return [{"EquipmentID": 77, "EquipmentCode": "EQ-001", "EquipmentName": "Test Eq", "EquipmentModel": "Model X", "Active": True, "Universal_ID_M_Equipment": "EQ-U-01"}]
            elif "T_EquipmentShipDetail" in query:
                return [{
                    "EquipmentShipID": self.ship_equipment.equipment_ship_id,
                    "NoOfFits": 2,
                    "EquipmentSrNo": "SN-APPROVED",
                    "Status": 1,
                    "Universal_ID_T_EquipmentShipDetail": self.ship_equipment.universal_id_t_equipment_ship_detail,
                    "Universal_ID_M_Ship": "SHIP-U-01",
                    "Universal_ID_M_Equipment": "EQ-U-01",
                }]
            elif "T_SFDChangeRequest" in query:
                return [{
                    "Universal_ID_T_SFDChangeRequest": self.change_request.universal_id_t_sfd_change_request,
                    "EquipmentShipId": self.ship_equipment.equipment_ship_id,
                    "Equipment": "Approved Equipment",
                    "IsSynced": 1,
                }]
            elif "Ch_SFD_Remove_Equipment_Request" in query:
                return []
            return []

        mock_fetch.side_effect = side_effect

        self.ship_equipment.is_synced = 0
        self.ship_equipment.save()
        self.change_request.is_synced = 0
        self.change_request.save()

        response = self.client.post("/sync", json={})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("sync_id", data)
        self.assertIn("steps", data)
        self.assertIn("masters", data["steps"])
        self.assertIn("push", data["steps"])
        self.assertIn("approvals", data["steps"])

        self.ship_equipment.refresh_from_db()
        self.assertEqual(self.ship_equipment.is_synced, 1)

    def test_sync_concurrency_lock(self):
        from django.core.cache import cache
        cache.set("cmms_sync_in_progress_lock", "true", timeout=60)

        response = self.client.post("/sync", json={})
        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertEqual(data["status"], "in_progress")

        cache.delete("cmms_sync_in_progress_lock")
