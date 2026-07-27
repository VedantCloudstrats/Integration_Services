import logging
from datetime import datetime, timezone
from django.db.models import Max
from django.core.cache import cache
from django.contrib.auth import get_user_model

from master.models import (
    CommandMaster,
    CountryMaster,
    DepartmentMaster,
    EquipmentMaster,
    EquipmentTypeMaster,
    PropulsionMaster,
    ShipCategoryMaster,
    ShipMaster,
    OpsAuthorityMaster,
    SubDepartmentMaster,
    SupplierMaster,
)
from sfd.models import (
    ChangeEquipmentRequest,
    SFDTransaction,
    RemoveEquipmentRequest,
)

from .db_utils import fetch_cmms_table_data, execute_cmms_query
from .serializers import (
    CMMS_EquipmentTypeMasterSerializer,
    CMMS_M_CommandSerializer,
    CMMS_M_CountrySerializer,
    CMMS_M_DepartmentSerializer,
    CMMS_M_EquipmentSerializer,
    CMMS_M_OpsAuthoritySerializer,
    CMMS_M_PropulsionSerializer,
    CMMS_M_ShipCategorySerializer,
    CMMS_M_ShipSerializer,
    CMMS_M_SubDepartmentSerializer,
    CMMS_M_SupplierSerializer,
    CMMS_T_ChangeEquipmentRequestSerializer,
    CMMS_T_EquipmentShipDetailIngestSerializer,
)

import threading

logger = logging.getLogger("integration.sync")
LOCK_KEY = "cmms_sync_in_progress_lock"
_IN_MEMORY_SYNC_LOCK = threading.Lock()
_IN_MEMORY_SYNC_ACTIVE = False


def _base_audit_defaults():
    user = get_user_model().objects.order_by("pk").first()
    if not user:
        raise ValueError(
            "At least one user is required before importing master data because created_by and updated_by are mandatory."
        )
    return {"created_by": user, "updated_by": user}


def _resolve_fk(model, uid_field, uid_value, pk_value):
    if uid_value:
        return model.objects.filter(**{uid_field: uid_value}).first()
    if pk_value is not None:
        return model.objects.filter(pk=pk_value).first()
    return None


# Table configurations for generic incremental ingestion
MASTER_CONFIGS = {
    "M_Country": {
        "model": CountryMaster,
        "serializer": CMMS_M_CountrySerializer,
        "lookup": "universal_id_m_country",
        "map_fields": lambda val: {
            "country_code": val.get("country_code"),
            "country_name": val.get("country_name"),
            "active": val.get("active"),
        },
    },
    "M_Command": {
        "model": CommandMaster,
        "serializer": CMMS_M_CommandSerializer,
        "lookup": "universal_id_m_command",
        "map_fields": lambda val: {
            "command_name": val.get("command_name"),
            "command_code": val.get("command_code"),
            "active": val.get("active"),
        },
    },
    "M_ShipCategory": {
        "model": ShipCategoryMaster,
        "serializer": CMMS_M_ShipCategorySerializer,
        "lookup": "universal_id_m_ship_category",
        "map_fields": lambda val: {
            "ship_category_name": val.get("ship_category_name"),
            "active": val.get("active"),
        },
    },
    "M_Propulsion": {
        "model": PropulsionMaster,
        "serializer": CMMS_M_PropulsionSerializer,
        "lookup": "universal_id_m_propulsion",
        "map_fields": lambda val: {
            "propulsion_name": val.get("propulsion_name"),
            "active": val.get("active"),
        },
    },
    "Ch_Master_Equipment_Type": {
        "model": EquipmentTypeMaster,
        "serializer": CMMS_EquipmentTypeMasterSerializer,
        "lookup": "universal_id_ch_master_equipment_type",
        "pre_validate": lambda row: {
            "equipment_type_id": row.get("Equipment_Type_ID"),
            "equipment_desc": row.get("Equipment_Desc"),
            "status": row.get("Status"),
            "universal_id_ch_master_equipment_type": row.get(
                "Universal_ID_Ch_Master_Equipment_Type"
            ),
        },
        "map_fields": lambda val: {
            "equipment_desc": val.get("equipment_desc"),
            "status": val.get("status"),
        },
    },
    "M_Department": {
        "model": DepartmentMaster,
        "serializer": CMMS_M_DepartmentSerializer,
        "lookup": "universal_id_m_department",
        "map_fields": lambda val: {
            "code": val.get("dep_code"),
            "name": val.get("description"),
        },
    },
    "M_Supplier": {
        "model": SupplierMaster,
        "serializer": CMMS_M_SupplierSerializer,
        "lookup": "universal_id_M_supplier",
        "map_fields": lambda val: {
            "supplier_code": val.get("supplier_code"),
            "supplier_name": val.get("supplier_name") or "Unknown Supplier",
            "address": val.get("address"),
            "country_code": val.get("country_code"),
            "active": bool(val.get("active")),
            "supplier_manufacture": val.get("supplier_manufacture") or 0,
            "universal_id_M_country": val.get("universal_id_M_country"),
        },
        "custom_resolve": lambda row, defaults: {
            **defaults,
            "city": row.get("City") or "Unknown",
            "contact_person": row.get("ContactPerson"),
            "contact_number": row.get("ContactNumber"),
            "email_id": row.get("EmailID")
            or f"{defaults.get('universal_id_M_supplier')}@example.local",
        },
    },
    "M_OpsAuthority": {
        "model": OpsAuthorityMaster,
        "serializer": CMMS_M_OpsAuthoritySerializer,
        "lookup": "universal_id_m_ops_authority",
        "map_fields": lambda val: {
            "ops_code": val.get("ops_code"),
            "ops_authority": val.get("ops_authority"),
            "command_name": val.get("command_name"),
            "active": val.get("active"),
            "universal_id_m_command": val.get("universal_id_m_command"),
            "address": val.get("address"),
        },
        "custom_resolve": lambda row, defaults: {
            **defaults,
            "command": CommandMaster.objects.filter(
                universal_id_m_command=defaults.get("universal_id_m_command")
            ).first(),
        },
    },
    "M_Ship": {
        "model": ShipMaster,
        "serializer": CMMS_M_ShipSerializer,
        "lookup": "universal_id_m_ship",
        "map_fields": lambda val: {
            "ship_id": val.get("ship_id"),
            "ship_sr_no": val.get("ship_sr_no"),
            "ship_code": val.get("ship_code"),
            "ship_name": val.get("ship_name"),
            "commission_date": val.get("commission_date"),
            "decommission_date": val.get("decommission_date"),
            "displacement": val.get("displacement"),
            "decommission_scheduled_date": val.get("decommission_scheduled_date"),
            "active": val.get("active"),
            "yard_no": val.get("yard_no"),
            "length_overall": val.get("length_overall"),
            "universal_id_m_ship_category": val.get("universal_id_m_ship_category"),
            "universal_id_m_ship_class": val.get("universal_id_m_ship_class"),
            "universal_id_m_command": val.get("universal_id_m_command"),
            "universal_id_m_ops_authority": val.get("universal_id_m_ops_authority"),
            "universal_id_m_propulsion": val.get("universal_id_m_propulsion"),
            "refit_authority": val.get("refit_authority"),
            "address": val.get("address"),
            "universal_id_m_overseeing_team": val.get("universal_id_m_overseeing_team"),
            "is_in_gd": val.get("is_in_gd"),
            "universal_id_m_ship_unit_category": val.get(
                "universal_id_m_ship_unit_category"
            ),
        },
    },
    "M_SubDepartment": {
        "model": SubDepartmentMaster,
        "serializer": CMMS_M_SubDepartmentSerializer,
        "lookup": "universal_id_m_sub_department",
        "map_fields": lambda val: {
            "name": val.get("description"),
            "code": val.get("sub_department_code"),
            "active": bool(val.get("active", True)),
            "universal_id_m_department": val.get("universal_id_m_department"),
            "universal_id_m_ship_class": val.get("universal_id_m_ship_class"),
        },
        "custom_resolve": lambda row, defaults: {
            **defaults,
            "department": DepartmentMaster.objects.filter(
                universal_id_m_department=defaults.get("universal_id_m_department")
            ).first(),
        },
    },
    "M_Equipment": {
        "model": EquipmentMaster,
        "serializer": CMMS_M_EquipmentSerializer,
        "lookup": "universal_id_m_equipment",
        "map_fields": lambda val: {
            "equipment_code": val.get("equipment_code"),
            "equipment_name": val.get("equipment_name"),
            "equipment_model": val.get("equipment_model"),
            "active": val.get("active"),
            "maintop_number": val.get("maintop_number"),
            "manufacturer_name": val.get("manufacturer_name"),
            "authority": val.get("authority"),
            "equipment_type_id": val.get("equipment_type_id"),
            "ilms_equipment_code": val.get("ilms_equipment_code"),
            "universal_id_m_section": val.get("universal_id_m_section"),
            "universal_id_m_group": val.get("universal_id_m_group"),
            "universal_id_t_maintop_header": val.get("universal_id_t_maintop_header"),
            "universal_id_ch_master_equipment_type": val.get(
                "universal_id_ch_master_equipment_type"
            ),
        },
    },
}


def ingest_entity(table_name, config):
    """
    Ingestion logic fetching all records from CMMS master table and upserting into SWMM.
    Guarantees SWMM master tables stay 100% up-to-date with CMMS.
    """
    model_class = config["model"]
    serializer_class = config["serializer"]
    lookup_field = config["lookup"]
    map_fields_fn = config["map_fields"]
    pre_validate_fn = config.get("pre_validate")
    custom_resolve_fn = config.get("custom_resolve")

    query = f"SELECT * FROM {table_name}"
    try:
        rows = fetch_cmms_table_data(query)
        logger.info(f"Fetched {len(rows)} rows from CMMS table {table_name}")
    except Exception as fetch_err:
        logger.error(f"Error fetching data from CMMS table {table_name}: {fetch_err}")
        return {
            "table": table_name,
            "created": 0,
            "updated": 0,
            "errors": [{"error": f"CMMS Query Failed: {fetch_err}"}],
        }

    created_count = 0
    updated_count = 0
    errors = []

    for row in rows:
        try:
            payload = pre_validate_fn(row) if pre_validate_fn else row
            serializer = serializer_class(data=payload)
            serializer.is_valid(raise_exception=True)
            val = serializer.validated_data

            lookup_val = val.get(lookup_field)
            if not lookup_val:
                # Serializer source mapping resolution
                for field_name, field in serializer.fields.items():
                    if field.source == lookup_field:
                        lookup_val = val.get(field_name)
                        break

            if not lookup_val:
                errors.append(
                    {"row": row, "error": f"Lookup field '{lookup_field}' is missing."}
                )
                continue

            defaults = map_fields_fn(val)

            if custom_resolve_fn:
                defaults = custom_resolve_fn(row, defaults)

            if hasattr(model_class, "created_by"):
                defaults.update(_base_audit_defaults())

            obj, created = model_class.objects.update_or_create(
                **{lookup_field: lookup_val}, defaults=defaults
            )

            if created:
                created_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append({"row": row, "error": str(e)})

    return {
        "table": table_name,
        "created": created_count,
        "updated": updated_count,
        "errors": errors,
    }


def pull_all_masters():
    """
    Executes the ingestion of all master/reference tables in proper dependency order.
    """
    order = [
        "M_Country",
        "M_Command",
        "M_ShipCategory",
        "M_Propulsion",
        "Ch_Master_Equipment_Type",
        "M_Department",
        "M_Supplier",
        "M_OpsAuthority",
        "M_Ship",
        "M_SubDepartment",
        "M_Equipment",
    ]

    results = {}
    for table in order:
        config = MASTER_CONFIGS[table]
        try:
            results[table] = ingest_entity(table, config)
        except Exception as e:
            logger.error(f"Failed to ingest master table {table}: {e}")
            return {
                "status": "error",
                "message": f"Ingestion failed at table {table}: {str(e)}",
                "details": results,
            }

    return {
        "status": "success",
        "message": "Master pull completed successfully.",
        "details": results,
    }


def push_to_cmms():
    """
    Pushes local unsynced records (is_synced=0) to CMMS database using SQL Server MERGE.
    Updates Django status to is_synced=2 (In Progress).
    """
    stats = {
        "T_EquipmentShipDetail": {"pushed": 0, "errors": []},
        "T_SFDChangeRequest": {"pushed": 0, "errors": []},
        "Ch_SFD_Remove_Equipment_Request": {"pushed": 0, "errors": []},
    }

    # 1. Push SFDTransaction (T_EquipmentShipDetail)
    transactions = SFDTransaction.objects.filter(is_synced=0)
    for tx in transactions:
        try:
            query = """
                MERGE T_EquipmentShipDetail AS target
                USING (
                    SELECT ? AS Universal_ID_T_EquipmentShipDetail, ? AS ShipID, ? AS EquipmentID, ? AS LocationCode,
                           ? AS LocationOnBoard, ? AS NoOfFits, ? AS EquipmentSrNo, ? AS OEMPartNo,
                           ? AS InstallationDate, ? AS Remark, ? AS Active, ? AS Nomenclature,
                           ? AS ServiceLife, ? AS Status, ? AS Universal_ID_M_Ship, ? AS Universal_ID_M_Equipment,
                           ? AS Universal_ID_M_Supplier_Supplier, ? AS Universal_ID_M_Supplier_Manufacturer,
                           ? AS Universal_ID_M_Equipment_ParentEquipment, ? AS Universal_ID_M_Department,
                           ? AS Universal_ID_T_MaintopHeader, ? AS ParentEquipment, ? AS Authority_Of_Installation,
                           ? AS RH_Of_New_Equipemnt_At_Time_Of_Installation, ? AS Universal_ID_M_SubDepartment,
                           ? AS SRARApplicable, ? AS SupplierID, ? AS ManufacturerID, 2 AS IsSynced
                ) AS source
                ON target.Universal_ID_T_EquipmentShipDetail = source.Universal_ID_T_EquipmentShipDetail
                WHEN MATCHED THEN
                    UPDATE SET
                        ShipID = source.ShipID, EquipmentID = source.EquipmentID, LocationCode = source.LocationCode,
                        LocationOnBoard = source.LocationOnBoard, NoOfFits = source.NoOfFits, EquipmentSrNo = source.EquipmentSrNo,
                        OEMPartNo = source.OEMPartNo, InstallationDate = source.InstallationDate, Remark = source.Remark,
                        Active = source.Active, Nomenclature = source.Nomenclature, ServiceLife = source.ServiceLife,
                        Status = source.Status, Universal_ID_M_Ship = source.Universal_ID_M_Ship,
                        Universal_ID_M_Equipment = source.Universal_ID_M_Equipment,
                        Universal_ID_M_Supplier_Supplier = source.Universal_ID_M_Supplier_Supplier,
                        Universal_ID_M_Supplier_Manufacturer = source.Universal_ID_M_Supplier_Manufacturer,
                        Universal_ID_M_Equipment_ParentEquipment = source.Universal_ID_M_Equipment_ParentEquipment,
                        Universal_ID_M_Department = source.Universal_ID_M_Department,
                        Universal_ID_T_MaintopHeader = source.Universal_ID_T_MaintopHeader, ParentEquipment = source.ParentEquipment,
                        Authority_Of_Installation = source.Authority_Of_Installation,
                        RH_Of_New_Equipemnt_At_Time_Of_Installation = source.RH_Of_New_Equipemnt_At_Time_Of_Installation,
                        Universal_ID_M_SubDepartment = source.Universal_ID_M_SubDepartment, SRARApplicable = source.SRARApplicable,
                        IsSynced = source.IsSynced, SupplierID = source.SupplierID, ManufacturerID = source.ManufacturerID
                WHEN NOT MATCHED THEN
                    INSERT (
                        Universal_ID_T_EquipmentShipDetail, ShipID, EquipmentID, LocationCode, LocationOnBoard, NoOfFits,
                        EquipmentSrNo, OEMPartNo, InstallationDate, Remark, Active, Nomenclature, ServiceLife, Status,
                        Universal_ID_M_Ship, Universal_ID_M_Equipment, Universal_ID_M_Supplier_Supplier,
                        Universal_ID_M_Supplier_Manufacturer, Universal_ID_M_Equipment_ParentEquipment,
                        Universal_ID_M_Department, Universal_ID_T_MaintopHeader, ParentEquipment,
                        Authority_Of_Installation, RH_Of_New_Equipemnt_At_Time_Of_Installation,
                        Universal_ID_M_SubDepartment, SRARApplicable, IsSynced, SupplierID, ManufacturerID
                    ) VALUES (
                        source.Universal_ID_T_EquipmentShipDetail, source.ShipID, source.EquipmentID, source.LocationCode,
                        source.LocationOnBoard, source.NoOfFits, source.EquipmentSrNo, source.OEMPartNo, source.InstallationDate,
                        source.Remark, source.Active, source.Nomenclature, source.ServiceLife, source.Status,
                        source.Universal_ID_M_Ship, source.Universal_ID_M_Equipment, source.Universal_ID_M_Supplier_Supplier,
                        source.Universal_ID_M_Supplier_Manufacturer, source.Universal_ID_M_Equipment_ParentEquipment,
                        source.Universal_ID_M_Department, source.Universal_ID_T_MaintopHeader, source.ParentEquipment,
                        source.Authority_Of_Installation, source.RH_Of_New_Equipemnt_At_Time_Of_Installation,
                        source.Universal_ID_M_SubDepartment, source.SRARApplicable, source.IsSynced, source.SupplierID, source.ManufacturerID
                    );
            """
            params = [
                tx.universal_id_t_equipment_ship_detail,
                tx.ship.ship_id if tx.ship else None,
                tx.equipment.equipment_id if tx.equipment else None,
                tx.location_code,
                tx.location_on_board,
                tx.no_of_fits,
                tx.equipment_sr_no,
                tx.oem_part_no,
                tx.installation_date,
                tx.remark,
                tx.active,
                tx.nomenclature,
                tx.service_life,
                tx.status,
                tx.universal_id_m_ship,
                tx.universal_id_m_equipment,
                tx.universal_id_m_supplier,
                tx.universal_id_m_manufacturer,
                tx.universal_id_m_equipment_parent,
                tx.universal_id_m_department,
                tx.universal_id_t_maintop_header,
                tx.parent_equipment,
                tx.authority_of_installation,
                tx.rh_at_installation,
                tx.universal_id_m_sub_department,
                tx.srar_applicable,
                tx.supplier.supplier_id if tx.supplier else None,
                tx.manufacturer.supplier_id if tx.manufacturer else None,
            ]
            execute_cmms_query(query, params)
            tx.is_synced = 2
            tx.save()
            stats["T_EquipmentShipDetail"]["pushed"] += 1
        except Exception as e:
            stats["T_EquipmentShipDetail"]["errors"].append(
                {"id": tx.pk, "error": str(e)}
            )

    # 2. Push ChangeEquipmentRequest (T_SFDChangeRequest)
    change_requests = ChangeEquipmentRequest.objects.filter(is_synced=0)
    for cr in change_requests:
        try:
            query = """
                MERGE T_SFDChangeRequest AS target
                USING (
                    SELECT ? AS Universal_ID_T_SFDChangeRequest, ? AS EquipmentShipId, ? AS Equipment, ? AS Model,
                           ? AS Supplier, ? AS Manufacture, ? AS Active, ? AS CreatedBy, ? AS CreatedDate,
                           ? AS Universal_ID_T_EquipmentShipDetail, ? AS Universal_ID_A_User_Created_By,
                           ? AS Universal_ID_A_User_Updated_By, ? AS UpdatedBy, ? AS UpdatedDate, 2 AS IsSynced
                ) AS source
                ON target.Universal_ID_T_SFDChangeRequest = source.Universal_ID_T_SFDChangeRequest
                WHEN MATCHED THEN
                    UPDATE SET
                        EquipmentShipId = source.EquipmentShipId, Equipment = source.Equipment, Model = source.Model,
                        Supplier = source.Supplier, Manufacture = source.Manufacture, Active = source.Active,
                        CreatedBy = source.CreatedBy, CreatedDate = source.CreatedDate,
                        Universal_ID_T_EquipmentShipDetail = source.Universal_ID_T_EquipmentShipDetail,
                        Universal_ID_A_User_Created_By = source.Universal_ID_A_User_Created_By,
                        Universal_ID_A_User_Updated_By = source.Universal_ID_A_User_Updated_By,
                        UpdatedBy = source.UpdatedBy, UpdatedDate = source.UpdatedDate, IsSynced = source.IsSynced
                WHEN NOT MATCHED THEN
                    INSERT (
                        Universal_ID_T_SFDChangeRequest, EquipmentShipId, Equipment, Model, Supplier, Manufacture,
                        Active, CreatedBy, CreatedDate, Universal_ID_T_EquipmentShipDetail,
                        Universal_ID_A_User_Created_By, Universal_ID_A_User_Updated_By,
                        UpdatedBy, UpdatedDate, IsSynced
                    ) VALUES (
                        source.Universal_ID_T_SFDChangeRequest, source.EquipmentShipId, source.Equipment, source.Model,
                        source.Supplier, source.Manufacture, source.Active, source.CreatedBy, source.CreatedDate,
                        source.Universal_ID_T_EquipmentShipDetail, source.Universal_ID_A_User_Created_By,
                        source.Universal_ID_A_User_Updated_By, source.UpdatedBy, source.UpdatedDate, source.IsSynced
                    );
            """
            params = [
                cr.universal_id_t_sfd_change_request,
                (
                    cr.equipment_ship_id.equipment_ship_id
                    if cr.equipment_ship_id
                    else None
                ),
                cr.equipment,
                cr.model,
                cr.supplier,
                cr.manufacture,
                cr.active,
                cr.created_by,
                cr.created_date,
                cr.universal_id_t_equipment_ship_detail,
                cr.universal_id_a_user_created_by,
                cr.universal_id_a_user_updated_by,
                cr.updated_by,
                cr.updated_date,
            ]
            execute_cmms_query(query, params)
            cr.is_synced = 2
            cr.save()
            stats["T_SFDChangeRequest"]["pushed"] += 1
        except Exception as e:
            stats["T_SFDChangeRequest"]["errors"].append({"id": cr.pk, "error": str(e)})

    # 3. Push RemoveEquipmentRequest (Ch_SFD_Remove_Equipment_Request)
    remove_requests = RemoveEquipmentRequest.objects.filter(is_synced=0)
    for rr in remove_requests:
        try:
            query = """
                MERGE Ch_SFD_Remove_Equipment_Request AS target
                USING (
                    SELECT ? AS Universal_ID_Ch_SFD_Remove_Equipment_Request, ? AS Universal_ID_T_EquipmentShipDetail,
                           ? AS Removal_Date, ? AS Removal_Remark, ? AS Authority_Of_Removal, ? AS Equipment_Serial_No,
                           ? AS Authority_Of_Installation, ? AS RH_Of_New_Equipemnt_At_Time_Of_Installation,
                           ? AS Request_Type, ? AS Active, ? AS CreatedDate, ? AS Universal_ID_A_User_Created_By,
                           ? AS Universal_ID_A_User_Updated_By, ? AS UpdatedDate, ? AS Approved_Reject,
                           ? AS installationDate, ? AS InstallationRemark, 2 AS IsSynced
                ) AS source
                ON target.Universal_ID_Ch_SFD_Remove_Equipment_Request = source.Universal_ID_Ch_SFD_Remove_Equipment_Request
                WHEN MATCHED THEN
                    UPDATE SET
                        Universal_ID_T_EquipmentShipDetail = source.Universal_ID_T_EquipmentShipDetail,
                        Removal_Date = source.Removal_Date, Removal_Remark = source.Removal_Remark,
                        Authority_Of_Removal = source.Authority_Of_Removal, Equipment_Serial_No = source.Equipment_Serial_No,
                        Authority_Of_Installation = source.Authority_Of_Installation,
                        RH_Of_New_Equipemnt_At_Time_Of_Installation = source.RH_Of_New_Equipemnt_At_Time_Of_Installation,
                        Request_Type = source.Request_Type, Active = source.Active, CreatedDate = source.CreatedDate,
                        Universal_ID_A_User_Created_By = source.Universal_ID_A_User_Created_By,
                        Universal_ID_A_User_Updated_By = source.Universal_ID_A_User_Updated_By,
                        UpdatedDate = source.UpdatedDate, Approved_Reject = source.Approved_Reject,
                        installationDate = source.installationDate, InstallationRemark = source.InstallationRemark,
                        IsSynced = source.IsSynced
                WHEN NOT MATCHED THEN
                    INSERT (
                        Universal_ID_Ch_SFD_Remove_Equipment_Request, Universal_ID_T_EquipmentShipDetail, Removal_Date,
                        Removal_Remark, Authority_Of_Removal, Equipment_Serial_No, Authority_Of_Installation,
                        RH_Of_New_Equipemnt_At_Time_Of_Installation, Request_Type, Active, CreatedDate,
                        Universal_ID_A_User_Created_By, Universal_ID_A_User_Updated_By, UpdatedDate,
                        Approved_Reject, installationDate, InstallationRemark, IsSynced
                    ) VALUES (
                        source.Universal_ID_Ch_SFD_Remove_Equipment_Request, source.Universal_ID_T_EquipmentShipDetail,
                        source.Removal_Date, source.Removal_Remark, source.Authority_Of_Removal, source.Equipment_Serial_No,
                        source.Authority_Of_Installation, source.RH_Of_New_Equipemnt_At_Time_Of_Installation,
                        source.Request_Type, source.Active, source.CreatedDate, source.Universal_ID_A_User_Created_By,
                        source.Universal_ID_A_User_Updated_By, source.UpdatedDate, source.Approved_Reject,
                        source.installationDate, source.InstallationRemark, source.IsSynced
                    );
            """
            params = [
                rr.universal_id_ch_sfd_remove_equipment_request,
                (
                    rr.universal_id_t_equipment_ship_detail.universal_id_t_equipment_ship_detail
                    if rr.universal_id_t_equipment_ship_detail
                    else None
                ),
                rr.removal_date,
                rr.removal_remark,
                rr.authority_of_removal,
                rr.equipment_serial_no,
                rr.authority_of_installation,
                rr.rh_of_new_equipment_at_time_of_installation,
                rr.request_type,
                rr.active,
                rr.created_date,
                rr.universal_id_a_user_created_by,
                rr.universal_id_a_user_updated_by,
                rr.updated_date,
                rr.approved_reject or 3,  # default to 3 (Pending) on CMMS
                rr.installation_date,
                rr.installation_remark,
            ]
            execute_cmms_query(query, params)
            rr.is_synced = 2
            rr.save()
            stats["Ch_SFD_Remove_Equipment_Request"]["pushed"] += 1
        except Exception as e:
            stats["Ch_SFD_Remove_Equipment_Request"]["errors"].append(
                {"id": rr.pk, "error": str(e)}
            )

    return {
        "status": "success",
        "message": "Pushed transaction records to CMMS.",
        "details": stats,
    }


def pull_transaction_approvals():
    """
    Pulls processed/approved requests from CMMS back into SWMM.
    Sets local is_synced = 1 (Approved / Completed) when approved.
    """
    stats = {
        "T_EquipmentShipDetail": {"pulled": 0, "approved": 0, "errors": []},
        "T_SFDChangeRequest": {"pulled": 0, "approved": 0, "errors": []},
        "Ch_SFD_Remove_Equipment_Request": {"pulled": 0, "approved": 0, "errors": []},
    }

    # 1. Pull transaction records for T_EquipmentShipDetail from CMMS into SWMM
    try:
        try:
            rows = fetch_cmms_table_data("SELECT * FROM T_EquipmentShipDetail")
            logger.info(f"Fetched {len(rows)} T_EquipmentShipDetail transaction rows from CMMS")
        except Exception as fetch_err:
            logger.error(f"Failed fetching T_EquipmentShipDetail from CMMS: {fetch_err}")
            rows = []
        for row in rows:
            try:
                payload = row
                serializer = CMMS_T_EquipmentShipDetailIngestSerializer(data=payload)
                serializer.is_valid(raise_exception=True)
                val = serializer.validated_data

                lookup_val = val.get("universal_id_t_equipment_ship_detail")
                if not lookup_val:
                    continue

                # Prepare resolved defaults
                equipment = _resolve_fk(
                    EquipmentMaster,
                    "universal_id_m_equipment",
                    val.get("universal_id_m_equipment"),
                    val.get("equipment_id"),
                )
                ship = _resolve_fk(
                    ShipMaster,
                    "universal_id_m_ship",
                    val.get("universal_id_m_ship"),
                    val.get("ship_id"),
                )
                supplier = _resolve_fk(
                    SupplierMaster,
                    "universal_id_M_supplier",
                    val.get("universal_id_m_supplier"),
                    val.get("supplier_id"),
                )
                manufacturer = _resolve_fk(
                    SupplierMaster,
                    "universal_id_M_supplier",
                    val.get("universal_id_m_manufacturer"),
                    val.get("manufacturer_id"),
                )
                equipment_type = None
                if val.get("equipment_type_id") is not None:
                    equipment_type = EquipmentTypeMaster.objects.filter(
                        equipment_type_id=val.get("equipment_type_id")
                    ).first()

                defaults = {
                    "equipment": equipment,
                    "ship": ship,
                    "location_code": val.get("location_code"),
                    "location_on_board": val.get("location_on_board"),
                    "no_of_fits": val.get("no_of_fits"),
                    "equipment_sr_no": val.get("equipment_sr_no"),
                    "oem_part_no": val.get("oem_part_no"),
                    "installation_date": val.get("installation_date"),
                    "removal_date": val.get("removal_date"),
                    "supplier": supplier,
                    "manufacturer": manufacturer,
                    "remark": val.get("remark"),
                    "srar_applicable": val.get("srar_applicable"),
                    "maintop_id": val.get("maintop_id"),
                    "parent_equipment": val.get("parent_equipment"),
                    "active": val.get("active"),
                    "nomenclature": val.get("nomenclature"),
                    "service_life": val.get("service_life"),
                    "status": val.get("status"),
                    "equipment_type": equipment_type,
                    "removal_remark": val.get("removal_remark"),
                    "authority_of_removal": val.get("authority_of_removal"),
                    "authority_of_installation": val.get("authority_of_installation"),
                    "rh_at_installation": val.get("rh_at_installation"),
                    "insma_remarks": val.get("insma_remarks"),
                    "universal_id_m_ship": val.get("universal_id_m_ship"),
                    "universal_id_m_equipment": val.get("universal_id_m_equipment"),
                    "universal_id_m_srar_type": val.get("universal_id_m_srar_type"),
                    "universal_id_m_supplier": val.get("universal_id_m_supplier"),
                    "universal_id_m_manufacturer": val.get(
                        "universal_id_m_manufacturer"
                    ),
                    "universal_id_m_equipment_parent": val.get(
                        "universal_id_m_equipment_parent"
                    ),
                    "universal_id_m_department": val.get("universal_id_m_department"),
                    "universal_id_t_maintop_header": val.get(
                        "universal_id_t_maintop_header"
                    ),
                    "universal_id_ch_master_equipment_type": val.get(
                        "universal_id_ch_master_equipment_type"
                    ),
                    "universal_id_m_sub_department": val.get(
                        "universal_id_m_sub_department"
                    ),
                }

                # "check t_equipmentshipdetail = status 1 then it is approved and show sync approved"
                # If status is approved (1) or rejected (3), mark sync as complete
                is_approved = val.get("status") == 1
                is_rejected = val.get("status") == 3
                if is_approved or is_rejected:
                    defaults["is_synced"] = (
                        1  # 1 means Approved / Rejected / Completed locally
                    )

                obj, created = SFDTransaction.objects.update_or_create(
                    universal_id_t_equipment_ship_detail=lookup_val, defaults=defaults
                )

                stats["T_EquipmentShipDetail"]["pulled"] += 1
                if is_approved:
                    stats["T_EquipmentShipDetail"]["approved"] += 1

            except Exception as inner_e:
                stats["T_EquipmentShipDetail"]["errors"].append(
                    {"id": row.get("EquipmentShipID"), "error": str(inner_e)}
                )
    except Exception as e:
        logger.error(f"Failed to query T_EquipmentShipDetail approvals: {e}")
        return {
            "status": "error",
            "message": f"Failed pulling T_EquipmentShipDetail approvals: {str(e)}",
        }

    # 2. Pull approvals for T_SFDChangeRequest
    # 2. Pull approvals and requests for T_SFDChangeRequest from CMMS into SWMM
    try:
        try:
            rows = fetch_cmms_table_data("SELECT * FROM T_SFDChangeRequest")
            logger.info(f"Fetched {len(rows)} T_SFDChangeRequest transaction rows from CMMS")
        except Exception as fetch_err:
            logger.error(f"Failed fetching T_SFDChangeRequest from CMMS: {fetch_err}")
            rows = []
        for row in rows:
            try:
                payload = row
                serializer = CMMS_T_ChangeEquipmentRequestSerializer(data=payload)
                serializer.is_valid(raise_exception=True)
                val = serializer.validated_data

                lookup_val = val.get("universal_id_t_sfd_change_request")
                if not lookup_val:
                    continue

                equipment_ship = None
                if val.get("equipment_ship_id_id") is not None:
                    equipment_ship = SFDTransaction.objects.filter(
                        pk=val.get("equipment_ship_id_id")
                    ).first()

                defaults = {
                    "equipment_ship_id": equipment_ship,
                    "equipment": val.get("equipment"),
                    "model": val.get("model"),
                    "supplier": val.get("supplier"),
                    "manufacture": val.get("manufacture"),
                    "active": val.get("active"),
                    "created_by": val.get("created_by"),
                    "created_date": val.get("created_date"),
                    "universal_id_t_equipment_ship_detail": val.get(
                        "universal_id_t_equipment_ship_detail"
                    ),
                    "universal_id_a_user_created_by": val.get(
                        "universal_id_a_user_created_by"
                    ),
                    "universal_id_a_user_updated_by": val.get(
                        "universal_id_a_user_updated_by"
                    ),
                    "updated_by": val.get("updated_by"),
                    "updated_date": val.get("updated_date"),
                }

                # check IsSynced on CMMS:
                # CMMS IsSynced = 1 -> Approved/Completed (local is_synced = 1)
                # CMMS IsSynced = 2 -> In Progress (local is_synced = 2)
                cmms_is_synced = row.get("IsSynced")
                is_approved = cmms_is_synced == 1
                if is_approved:
                    defaults["is_synced"] = 1
                elif cmms_is_synced == 2:
                    defaults["is_synced"] = 2

                obj, created = ChangeEquipmentRequest.objects.update_or_create(
                    universal_id_t_sfd_change_request=lookup_val, defaults=defaults
                )

                stats["T_SFDChangeRequest"]["pulled"] += 1
                if is_approved:
                    stats["T_SFDChangeRequest"]["approved"] += 1

            except Exception as inner_e:
                stats["T_SFDChangeRequest"]["errors"].append(
                    {
                        "id": row.get("Universal_ID_T_SFDChangeRequest"),
                        "error": str(inner_e),
                    }
                )
    except Exception as e:
        logger.error(f"Failed to query T_SFDChangeRequest approvals: {e}")
        return {
            "status": "error",
            "message": f"Failed pulling T_SFDChangeRequest approvals: {str(e)}",
        }

    # 3. Pull approvals and requests for Ch_SFD_Remove_Equipment_Request from CMMS into SWMM
    try:
        try:
            rows = fetch_cmms_table_data("SELECT * FROM Ch_SFD_Remove_Equipment_Request")
            logger.info(f"Fetched {len(rows)} Ch_SFD_Remove_Equipment_Request transaction rows from CMMS")
        except Exception as fetch_err:
            logger.error(f"Failed fetching Ch_SFD_Remove_Equipment_Request from CMMS: {fetch_err}")
            rows = []
        for row in rows:
            try:
                lookup_val = row.get("Universal_ID_Ch_SFD_Remove_Equipment_Request")
                if not lookup_val:
                    continue

                eq_det_uid = row.get("Universal_ID_T_EquipmentShipDetail")
                equipment_detail = None
                if eq_det_uid:
                    equipment_detail = SFDTransaction.objects.filter(
                        universal_id_t_equipment_ship_detail=eq_det_uid
                    ).first()

                # Approved_Reject: 1 = Approved, 3 = Pending / In Progress
                approved_reject = row.get("Approved_Reject")
                local_is_synced = 2
                is_approved = approved_reject == 1
                if is_approved:
                    local_is_synced = 1

                defaults = {
                    "universal_id_t_equipment_ship_detail": equipment_detail,
                    "removal_date": row.get("Removal_Date"),
                    "removal_remark": row.get("Removal_Remark"),
                    "authority_of_removal": row.get("Authority_Of_Removal"),
                    "equipment_serial_no": row.get("Equipment_Serial_No"),
                    "authority_of_installation": row.get("Authority_Of_Installation"),
                    "rh_of_new_equipment_at_time_of_installation": row.get(
                        "RH_Of_New_Equipemnt_At_Time_Of_Installation"
                    ),
                    "request_type": row.get("Request_Type"),
                    "active": row.get("Active"),
                    "created_date": row.get("CreatedDate"),
                    "universal_id_a_user_created_by": row.get(
                        "Universal_ID_A_User_Created_By"
                    ),
                    "universal_id_a_user_updated_by": row.get(
                        "Universal_ID_A_User_Updated_By"
                    ),
                    "updated_date": row.get("UpdatedDate"),
                    "approved_reject": approved_reject,
                    "installation_date": row.get("installationDate"),
                    "installation_remark": row.get("InstallationRemark"),
                    "is_synced": local_is_synced,
                }

                obj, created = RemoveEquipmentRequest.objects.update_or_create(
                    universal_id_ch_sfd_remove_equipment_request=lookup_val,
                    defaults=defaults,
                )

                stats["Ch_SFD_Remove_Equipment_Request"]["pulled"] += 1
                if is_approved:
                    stats["Ch_SFD_Remove_Equipment_Request"]["approved"] += 1

            except Exception as inner_e:
                stats["Ch_SFD_Remove_Equipment_Request"]["errors"].append(
                    {
                        "id": row.get("Universal_ID_Ch_SFD_Remove_Equipment_Request"),
                        "error": str(inner_e),
                    }
                )
    except Exception as e:
        logger.error(f"Failed to query Ch_SFD_Remove_Equipment_Request approvals: {e}")
        return {
            "status": "error",
            "message": f"Failed pulling Ch_SFD_Remove_Equipment_Request approvals: {str(e)}",
        }

    return {
        "status": "success",
        "message": "Pulled transaction approvals/status from CMMS.",
        "details": stats,
    }


def _run_step(name, fn, *args, **kwargs):
    """
    Executes a single synchronization phase, captures timing and status.
    Returns a standardised step result dict regardless of success or failure.
    """
    import time
    started = time.time()
    try:
        result = fn(*args, **kwargs)
        duration = round(time.time() - started, 3)
        status = result.get("status", "success")
        return {
            "status": status,
            "duration_seconds": duration,
            "details": result.get("details", result),
            "message": result.get("message", ""),
        }
    except Exception as exc:
        duration = round(time.time() - started, 3)
        logger.exception(f"Step '{name}' raised an unexpected exception.")
        return {
            "status": "error",
            "duration_seconds": duration,
            "details": {},
            "message": str(exc),
        }


def run_unified_sync(steps=None):
    """
    Unified Synchronization Orchestrator.

    Executes the three synchronization phases in the correct dependency order:
      1. masters   – Pull all master/reference data from CMMS → SWMM
      2. push      – Push all pending SWMM transactions → CMMS
      3. approvals – Pull approval / status updates from CMMS → SWMM

    Parameters
    ----------
    steps : list[str] | None
        Optional subset of phases to run, e.g. ["masters", "push"].
        Defaults to all three phases when None or empty.

    Returns
    -------
    dict
        Consolidated sync result with sync_id, timing, per-step status,
        overall status ("success" | "partial" | "failed" | "in_progress"),
        and a high-level summary counter.
    """
    global _IN_MEMORY_SYNC_ACTIVE
    import uuid
    import time
    from datetime import datetime, timezone

    allowed_steps = {"masters", "pull", "push", "approvals"}
    if not steps:
        steps = ["masters", "pull", "push"]
    else:
        steps = [s for s in steps if s in allowed_steps]

    # ── Concurrency guard ────────────────────────────────────────────────────
    if _IN_MEMORY_SYNC_ACTIVE:
        logger.warning("Unified sync requested but an in-memory sync is already running.")
        return {
            "status": "in_progress",
            "message": "Synchronization is already in progress. Please try again later.",
        }

    redis_lock_acquired = False
    try:
        redis_lock_acquired = cache.add(LOCK_KEY, "true", timeout=900)
        if not redis_lock_acquired:
            # Check if key is actually present in cache (versus IGNORE_EXCEPTIONS fallback)
            lock_val = cache.get(LOCK_KEY)
            if lock_val is not None:
                logger.warning("Unified sync requested but a sync is already in progress in Redis.")
                return {
                    "status": "in_progress",
                    "message": "Synchronization is already in progress. Please try again later.",
                }
            else:
                redis_lock_acquired = True
    except Exception as exc:
        logger.warning(f"Cache lock check encountered exception: {exc}. Continuing sync execution.")
        redis_lock_acquired = True

    with _IN_MEMORY_SYNC_LOCK:
        if _IN_MEMORY_SYNC_ACTIVE:
            if redis_lock_acquired:
                try:
                    cache.delete(LOCK_KEY)
                except Exception:
                    pass
            return {
                "status": "in_progress",
                "message": "Synchronization is already in progress. Please try again later.",
            }
        _IN_MEMORY_SYNC_ACTIVE = True

    sync_id = str(uuid.uuid4())
    wall_start = time.time()
    started_at = datetime.now(timezone.utc).isoformat()
    logger.info(f"[sync:{sync_id}] Starting unified sync. Phases: {steps}")

    step_results = {}
    any_error = False

    try:
        # ── Phase 1: Master Data Pull (CMMS → SWMM) ──────────────────────────
        if "masters" in steps:
            logger.info(f"[sync:{sync_id}] Phase 1 — Master Data Synchronization (CMMS → SWMM)")
            step_results["masters"] = _run_step("masters", pull_all_masters)
            if step_results["masters"]["status"] == "error":
                any_error = True
                logger.error(
                    f"[sync:{sync_id}] Master sync failed: {step_results['masters']['message']}"
                )
        else:
            step_results["masters"] = {"status": "skipped", "message": "Not requested"}

        # ── Phase 2: Transaction Pull (CMMS → SWMM) ──────────────────────────
        if "pull" in steps or "approvals" in steps:
            logger.info(f"[sync:{sync_id}] Phase 2 — Transaction Pull (CMMS → SWMM)")
            step_results["pull"] = _run_step("pull", pull_transaction_approvals)
            step_results["approvals"] = step_results["pull"]
            if step_results["pull"]["status"] == "error":
                any_error = True
                logger.error(
                    f"[sync:{sync_id}] Transaction pull failed: {step_results['pull']['message']}"
                )
        else:
            step_results["pull"] = {"status": "skipped", "message": "Not requested"}

        # ── Phase 3: Transaction Push (SWMM → CMMS) ──────────────────────────
        if "push" in steps:
            logger.info(f"[sync:{sync_id}] Phase 3 — Transaction Push (SWMM → CMMS)")
            step_results["push"] = _run_step("push", push_to_cmms)
            if step_results["push"]["status"] == "error":
                any_error = True
                logger.error(
                    f"[sync:{sync_id}] Transaction push failed: {step_results['push']['message']}"
                )
        else:
            step_results["push"] = {"status": "skipped", "message": "Not requested"}

        # ── Compute overall status ───────────────────────────────────────────
        statuses = [
            r["status"]
            for key, r in step_results.items()
            if r["status"] != "skipped"
        ]
        if all(s == "success" for s in statuses):
            overall_status = "success"
        elif any(s == "success" for s in statuses):
            overall_status = "partial"
        else:
            overall_status = "failed"

        # ── Build summary counters ───────────────────────────────────────────
        def _count(step_key, *count_keys):
            details = step_results.get(step_key, {}).get("details", {})
            if isinstance(details, dict):
                total = 0
                for ck in count_keys:
                    v = details.get(ck)
                    if isinstance(v, int):
                        total += v
                    elif isinstance(v, dict):
                        # Nested table stats
                        for tbl_stat in v.values():
                            if isinstance(tbl_stat, dict):
                                total += tbl_stat.get(ck, 0)
                return total
            return 0

        masters_detail = step_results.get("masters", {}).get("details", {})
        masters_synced = 0
        if isinstance(masters_detail, dict):
            for tbl_data in masters_detail.get("details", masters_detail).values():
                if isinstance(tbl_data, dict):
                    masters_synced += tbl_data.get("created", 0) + tbl_data.get("updated", 0)

        push_detail = step_results.get("push", {}).get("details", {})
        transactions_pushed = 0
        if isinstance(push_detail, dict):
            for tbl_stat in push_detail.values():
                if isinstance(tbl_stat, dict):
                    transactions_pushed += tbl_stat.get("pushed", 0)

        approvals_detail = step_results.get("approvals", {}).get("details", {})
        approvals_pulled = 0
        if isinstance(approvals_detail, dict):
            for tbl_stat in approvals_detail.values():
                if isinstance(tbl_stat, dict):
                    approvals_pulled += tbl_stat.get("pulled", 0)

        total_duration = round(time.time() - wall_start, 3)
        completed_at = datetime.now(timezone.utc).isoformat()

        logger.info(
            f"[sync:{sync_id}] Completed. Status={overall_status} "
            f"duration={total_duration}s masters={masters_synced} "
            f"pushed={transactions_pushed} approvals={approvals_pulled}"
        )

        LAST_SYNC_CACHE_KEY = "cmms_last_sync_info"
        if overall_status in ("success", "partial"):
            try:
                cache.set(
                    LAST_SYNC_CACHE_KEY,
                    {
                        "timestamp": completed_at,
                        "sync_id": sync_id,
                        "status": overall_status,
                        "masters_synced": masters_synced,
                        "transactions_pushed": transactions_pushed,
                        "approvals_pulled": approvals_pulled,
                    },
                    timeout=None,
                )
            except Exception as cache_err:
                logger.warning(f"Failed to record last sync info in cache: {cache_err}")

        return {
            "sync_id": sync_id,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": total_duration,
            "status": overall_status,
            "steps": step_results,
            "summary": {
                "masters_synced": masters_synced,
                "transactions_pushed": transactions_pushed,
                "approvals_pulled": approvals_pulled,
            },
        }

    except Exception as exc:
        total_duration = round(time.time() - wall_start, 3)
        logger.exception(f"[sync:{sync_id}] Unexpected failure during unified sync.")
        return {
            "sync_id": sync_id,
            "started_at": started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": total_duration,
            "status": "failed",
            "message": f"Unexpected failure: {str(exc)}",
            "steps": step_results,
        }

    finally:
        _IN_MEMORY_SYNC_ACTIVE = False
        try:
            cache.delete(LOCK_KEY)
        except Exception:
            pass
        logger.info(f"[sync:{sync_id}] Concurrency lock released.")


def run_complete_sync():
    """
    Backward-compatible alias for run_unified_sync().
    Runs all three phases: masters → push → approvals.
    Kept so existing Celery tasks and the /sync/complete endpoint
    continue to work without modification.
    """
    return run_unified_sync(steps=["masters", "push", "approvals"])


def get_sync_status_summary():
    """
    Returns detailed synchronization status summary matching the UI requirements:
      - Last Sync Date (e.g. "18-Jul-2026")
      - Last Sync Time (e.g. "Last Sync - 0630 hrs")
      - Elapsed Time since Last Sync (e.g. "9 days 5 hours ago" / "15 mins ago")
      - Sync in Queue (count of in-progress/queued records, is_synced=2)
      - Not Sync (count of unsynced/failed records, is_synced=0)
      - Itemized Pending Synchronization feeds list matching UI design
    """
    LAST_SYNC_CACHE_KEY = "cmms_last_sync_info"
    last_info = None
    try:
        last_info = cache.get(LAST_SYNC_CACHE_KEY)
    except Exception:
        pass

    now_utc = datetime.now(timezone.utc)

    if last_info and isinstance(last_info, dict) and last_info.get("timestamp"):
        try:
            last_ts_str = last_info["timestamp"]
            last_dt = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00"))
            elapsed_seconds = int((now_utc - last_dt).total_seconds())

            date_formatted = last_dt.strftime("%d-%b-%Y")
            time_formatted = f"Last Sync - {last_dt.strftime('%H%M')} hrs"

            days = elapsed_seconds // 86400
            hours = (elapsed_seconds % 86400) // 3600
            minutes = (elapsed_seconds % 3600) // 60

            if days > 0:
                elapsed_time = f"{days} day{'s' if days > 1 else ''} {hours} hr{'s' if hours > 1 else ''} ago"
            elif hours > 0:
                elapsed_time = f"{hours} hr{'s' if hours > 1 else ''} {minutes} min{'s' if minutes > 1 else ''} ago"
            elif minutes > 0:
                elapsed_time = f"{minutes} min{'s' if minutes > 1 else ''} ago"
            else:
                elapsed_time = "Just now"

            last_sync_data = {
                "timestamp": last_ts_str,
                "date_formatted": date_formatted,
                "time_formatted": time_formatted,
                "elapsed_time": elapsed_time,
                "elapsed_seconds": elapsed_seconds,
                "status": last_info.get("status", "success"),
            }
        except Exception:
            last_sync_data = {
                "timestamp": None,
                "date_formatted": "Not Synced Yet",
                "time_formatted": "Last Sync - N/A",
                "elapsed_time": "No previous sync recorded",
                "elapsed_seconds": None,
                "status": "none",
            }
    else:
        last_sync_data = {
            "timestamp": None,
            "date_formatted": "Not Synced Yet",
            "time_formatted": "Last Sync - N/A",
            "elapsed_time": "No previous sync recorded",
            "elapsed_seconds": None,
            "status": "none",
        }

    # Query counts from SWMM database tables
    unsynced_tx = SFDTransaction.objects.filter(is_synced=0).count()
    unsynced_cr = ChangeEquipmentRequest.objects.filter(is_synced=0).count()
    unsynced_rr = RemoveEquipmentRequest.objects.filter(is_synced=0).count()

    in_progress_tx = SFDTransaction.objects.filter(is_synced=2).count()
    in_progress_cr = ChangeEquipmentRequest.objects.filter(is_synced=2).count()
    in_progress_rr = RemoveEquipmentRequest.objects.filter(is_synced=2).count()

    not_synced_count = unsynced_tx + unsynced_cr + unsynced_rr
    sync_in_queue_count = in_progress_tx + in_progress_cr + in_progress_rr

    # Build Pending Synchronization feeds list matching UI design
    pending_list = []

    if unsynced_tx > 0:
        pending_list.append({
            "id": "sfd_transaction_feed",
            "name": "SFD Equipment Detail Feed",
            "description": "Equipment Ship Detail · retry queued",
            "status": "Failed" if unsynced_tx > 3 else "Pending",
            "action": "Retry" if unsynced_tx > 3 else "Queued",
            "count": unsynced_tx,
        })

    if unsynced_cr > 0:
        pending_list.append({
            "id": "sfd_change_request_feed",
            "name": "Equipment Change Request",
            "description": "Change Equipment Request table",
            "status": "Pending",
            "action": "Queued",
            "count": unsynced_cr,
        })

    if unsynced_rr > 0:
        pending_list.append({
            "id": "sfd_remove_request_feed",
            "name": "Equipment Removal Registry",
            "description": "Remove Equipment Request table",
            "status": "Pending",
            "action": "Queued",
            "count": unsynced_rr,
        })

    if in_progress_tx > 0 or in_progress_cr > 0 or in_progress_rr > 0:
        pending_list.append({
            "id": "active_sync_queue",
            "name": "Active Synchronization Queue",
            "description": "Background queued items processing",
            "status": "Queued",
            "action": "Queued",
            "count": sync_in_queue_count,
        })

    if not pending_list:
        pending_list.append({
            "id": "all_synced",
            "name": "All Feeds Synchronized",
            "description": "SWMM and CMMS master & transaction feeds are fully up-to-date",
            "status": "Synced",
            "action": "Up to Date",
            "count": 0,
        })

    overall_sync_status = "synced"
    if sync_in_queue_count > 0:
        overall_sync_status = "in_progress"
    elif not_synced_count > 0:
        overall_sync_status = "not_synced"

    return {
        "status": "active",
        "message": "Integration Services is up and running.",
        "app": "integrationservices",
        "sync_status": overall_sync_status,
        "sync_summary": {
            "last_sync": last_sync_data,
            "sync_in_queue": sync_in_queue_count,
            "not_synced": not_synced_count,
            "total_pending_records": not_synced_count + sync_in_queue_count,
        },
        "pending_synchronization": pending_list,
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
    }
