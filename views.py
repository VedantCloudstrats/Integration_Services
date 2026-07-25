from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from master.models import (
    EquipmentMaster,
    EquipmentTypeMaster,
    ShipMaster,
    SupplierMaster,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from sfd.models import (
    ChangeEquipmentRequest,
    SFDTransaction,
    RemoveEquipmentRequest,
)

from .db_utils import fetch_cmms_table_data
from .serializers import (
    CMMS_T_ChangeEquipmentRequestSerializer,
    CMMS_T_EquipmentShipDetailIngestSerializer,
    CMMS_T_EquipmentShipDetailSerializer,
)


def _resolve_fk(model, uid_field, uid_value, pk_value):
    if uid_value:
        return model.objects.filter(**{uid_field: uid_value}).first()
    if pk_value is not None:
        return model.objects.filter(pk=pk_value).first()
    return None


def _validated(serializer_class, payload):
    serializer = serializer_class(data=payload)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _base_audit_defaults():
    user = get_user_model().objects.order_by("pk").first()
    if not user:
        raise ValueError(
            "At least one user is required before importing master data because created_by and updated_by are mandatory."
        )
    return {"created_by": user, "updated_by": user}


@extend_schema(tags=["Integration Services"])
class IntegrationStatusView(APIView):
    def get(self, request):
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

        return Response(
            {
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
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Integration Services"])
class CMMSSyncView(APIView):
    def post(self, request):
        from .services import run_complete_sync

        result = run_complete_sync()
        if result.get("status") == "success":
            return Response(result, status=status.HTTP_200_OK)
        elif result.get("status") == "in_progress":
            return Response(result, status=status.HTTP_409_CONFLICT)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Integration Services"])
class CMMSMasterSyncView(APIView):
    def post(self, request):
        from .services import pull_all_masters

        result = pull_all_masters()
        if result.get("status") == "success":
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Integration Services"])
class CMMSEquipmentShipDetailSyncView(APIView):
    def get(self, request):
        sync_all = request.query_params.get("all", "false").lower() == "true"
        queryset = (
            SFDTransaction.objects.all()
            if sync_all
            else SFDTransaction.objects.filter(is_synced=0)
        )
        serializer = CMMS_T_EquipmentShipDetailSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        action = request.data.get("action", "sync_status")

        if action == "mark_synced":
            ids = request.data.get("ids", [])
            if not ids:
                return Response(
                    {"error": "List of 'ids' is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            updated_count = SFDTransaction.objects.filter(pk__in=ids).update(
                is_synced=1
            )
            return Response(
                {
                    "status": "success",
                    "message": f"Successfully marked {updated_count} SFDTransaction records as synced.",
                },
                status=status.HTTP_200_OK,
            )

        if action != "upsert":
            return Response(
                {"error": f"Invalid action: {action}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = request.data.get("records", [])
        if not records:
            return Response(
                {"error": "List of 'records' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_count = 0
        updated_count = 0
        errors = []

        for item in records:
            try:
                val = _validated(CMMS_T_EquipmentShipDetailIngestSerializer, item)
                lookup = val.get("universal_id_t_equipment_ship_detail")
                if not lookup:
                    errors.append(
                        {
                            "row": item,
                            "error": "Universal_ID_T_EquipmentShipDetail is missing.",
                        }
                    )
                    continue

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
                    "is_synced": 2 if val.get("status") == 2 else 1,
                }

                _, created = SFDTransaction.objects.update_or_create(
                    universal_id_t_equipment_ship_detail=lookup,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as exc:
                errors.append({"row": item, "error": str(exc)})

        return Response(
            {
                "message": f"Ingestion completed. Created: {created_count}, Updated: {updated_count}.",
                "errors": errors,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Integration Services"])
class CMMSChangeRequestSyncView(APIView):
    def get(self, request):
        sync_all = request.query_params.get("all", "false").lower() == "true"
        queryset = (
            ChangeEquipmentRequest.objects.all()
            if sync_all
            else ChangeEquipmentRequest.objects.filter(is_synced=0)
        )
        serializer = CMMS_T_ChangeEquipmentRequestSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        action = request.data.get("action", "sync_status")

        if action == "mark_synced":
            ids = request.data.get("ids", [])
            if not ids:
                return Response(
                    {"error": "List of 'ids' is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            updated_count = ChangeEquipmentRequest.objects.filter(pk__in=ids).update(
                is_synced=1
            )
            return Response(
                {
                    "message": f"Successfully marked {updated_count} change requests as synced."
                },
                status=status.HTTP_200_OK,
            )

        if action != "upsert":
            return Response(
                {"error": f"Invalid action: {action}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = request.data.get("records", [])
        if not records:
            return Response(
                {"error": "List of 'records' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_count = 0
        updated_count = 0
        errors = []

        for item in records:
            try:
                val = _validated(CMMS_T_ChangeEquipmentRequestSerializer, item)
                lookup = val.get("universal_id_t_sfd_change_request")
                if not lookup:
                    errors.append(
                        {
                            "row": item,
                            "error": "Universal_ID_T_SFDChangeRequest is missing.",
                        }
                    )
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
                    "is_synced": val.get("is_synced", 1),
                }
                _, created = ChangeEquipmentRequest.objects.update_or_create(
                    universal_id_t_sfd_change_request=lookup,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as exc:
                errors.append({"row": item, "error": str(exc)})

        return Response(
            {
                "message": f"Ingestion completed. Created: {created_count}, Updated: {updated_count}.",
                "errors": errors,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Integration Services"])
class CMMSEquipmentShipDetailIngestView(APIView):
    def get(self, request):
        try:
            rows = fetch_cmms_table_data("SELECT * FROM T_EquipmentShipDetail")
            created_count = 0
            updated_count = 0
            errors = []
            upserted = []

            for row in rows:
                try:
                    val = _validated(CMMS_T_EquipmentShipDetailIngestSerializer, row)
                    lookup = val.get("universal_id_t_equipment_ship_detail")
                    if not lookup:
                        errors.append(
                            {
                                "row": row,
                                "error": "Universal_ID_T_EquipmentShipDetail is missing.",
                            }
                        )
                        continue
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
                    obj, created = SFDTransaction.objects.update_or_create(
                        universal_id_t_equipment_ship_detail=lookup,
                        defaults={
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
                            "authority_of_installation": val.get(
                                "authority_of_installation"
                            ),
                            "rh_at_installation": val.get("rh_at_installation"),
                            "insma_remarks": val.get("insma_remarks"),
                            "universal_id_m_ship": val.get("universal_id_m_ship"),
                            "universal_id_m_equipment": val.get(
                                "universal_id_m_equipment"
                            ),
                            "universal_id_m_srar_type": val.get(
                                "universal_id_m_srar_type"
                            ),
                            "universal_id_m_supplier": val.get(
                                "universal_id_m_supplier"
                            ),
                            "universal_id_m_manufacturer": val.get(
                                "universal_id_m_manufacturer"
                            ),
                            "universal_id_m_equipment_parent": val.get(
                                "universal_id_m_equipment_parent"
                            ),
                            "universal_id_m_department": val.get(
                                "universal_id_m_department"
                            ),
                            "universal_id_t_maintop_header": val.get(
                                "universal_id_t_maintop_header"
                            ),
                            "universal_id_ch_master_equipment_type": val.get(
                                "universal_id_ch_master_equipment_type"
                            ),
                            "universal_id_m_sub_department": val.get(
                                "universal_id_m_sub_department"
                            ),
                            "is_synced": 2 if val.get("status") == 2 else 1,
                        },
                    )
                    upserted.append(obj)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as exc:
                    errors.append({"row": row, "error": str(exc)})

            return Response(
                {
                    "status": "success",
                    "message": f"Equipment Ship Details ingestion complete. Created: {created_count}, Updated: {updated_count}.",
                    "errors": errors,
                    "data": CMMS_T_EquipmentShipDetailIngestSerializer(
                        upserted, many=True
                    ).data,
                }
            )
        except Exception as exc:
            return Response(
                {"status": "error", "message": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(tags=["Integration Services"])
class CMMS_Ch_SFD_Remove_Equipment_RequestSyncView(APIView):
    def get(self, request):
        sync_all = request.query_params.get("all", "false").lower() == "true"
        removals = (
            RemoveEquipmentRequest.objects.all()
            if sync_all
            else RemoveEquipmentRequest.objects.filter(is_synced=0)
        )

        data = []

        for removal in removals:
            equipment_detail = removal.universal_id_t_equipment_ship_detail
            data.append(
                {
                    "id": f"remove-{removal.pk}",
                    "Universal_ID_T_EquipmentShipDetail": (
                        equipment_detail.universal_id_t_equipment_ship_detail
                        if equipment_detail
                        else None
                    ),
                    "Universal_ID_Ch_SFD_Remove_Equipment_Request": (
                        removal.universal_id_ch_sfd_remove_equipment_request
                        or f"remove-{removal.pk}"
                    ),
                    "Removal_Date": removal.removal_date,
                    "Removal_Remark": removal.removal_remark,
                    "Authority_Of_Removal": removal.authority_of_removal,
                    "Equipment_Serial_No": (
                        removal.equipment_serial_no
                        or (
                            equipment_detail.equipment_sr_no
                            if equipment_detail
                            else None
                        )
                    ),
                    "Authority_Of_Installation": removal.authority_of_installation,
                    "RH_Of_New_Equipemnt_At_Time_Of_Installation": removal.rh_of_new_equipment_at_time_of_installation,
                    "Request_Type": removal.request_type or 1,
                    "Active": removal.active,
                    "CreatedDate": removal.created_date,
                    "Universal_ID_A_User_Created_By": removal.universal_id_a_user_created_by,
                    "Universal_ID_A_User_Updated_By": removal.universal_id_a_user_updated_by,
                    "UpdatedDate": removal.updated_date,
                    "Approved_Reject": removal.approved_reject,
                    "installationDate": removal.installation_date,
                    "InstallationRemark": removal.installation_remark,
                    "IsSynced": removal.is_synced,
                }
            )

        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        action = request.data.get("action", "sync_status")
        if action != "mark_synced":
            return Response(
                {"error": f"Invalid action: {action}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "List of 'ids' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        removal_ids = []
        for item_id in ids:
            if isinstance(item_id, str) and item_id.startswith("remove-"):
                removal_ids.append(int(item_id.split("-", 1)[1]))

        updated_removals = RemoveEquipmentRequest.objects.filter(
            pk__in=removal_ids
        ).update(is_synced=1)

        return Response(
            {
                "status": "success",
                "message": f"Successfully marked {updated_removals} removals as synced.",
            },
            status=status.HTTP_200_OK,
        )
