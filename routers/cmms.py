from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import List, Optional
from asgiref.sync import sync_to_async
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from fast_api.schemas import (
    DefectCreate, DefectResponse, DefectRectifyRequest, GenericSuccessResponse,
    SRARMonthlyHeaderCreate, SrarEquipmentExploitationCreate, SRARDetailResponse,
    CompletedRoutineCreate, CompletedRoutineResponse, CmmsDartPayloadResponse,
    FussRaiseRequest, FussRaiseResponse, AberEquipmentResponse, ShipEquipmentResponse,
    RefitSyncPayloadResponse, RefitCompletionCreate, RefitCompletionResponse,
    RefitDelinquencyCreate, RefitDryDockingCreate, RefitOCRCreate,
    AberSubmitRequest, AberSubmitResponse,
    OpdefSyncPayloadResponse, OpdefInitiateRequest, OpdefInitiateResponse,
    OpdefAnalysisRequest, OpdefSpareRequest, OpdefTrialRequest,
    OpdefPriorParamRequest, OpdefPhotoResponse,
    FussSyncPayloadResponse, FussMastersResponse,
    SfdSyncPayloadResponse, SfdShipResponse,
    MaintopSyncRequest, MaintopSyncResponse, MaintopJICRequest, MaintopJICResponse,
    MaintopDistributionRequest, MaintopDistributionResponse
)
from fast_api.dependencies import verify_api_key

# Import Django models
from dart.models import Initiate_Dart, Complete_defect_dart, CompletedRoutine
from srar.models import SrarMonthlyHeader, SrarEquipmentExploitation
from ems.models import (
    FussRaiseDetails, RoutineDescription, MaintopHeader, MaintopDetail,
    T_maintopJIC, T_JICspares, T_JICtools, T_JICattachments,
    M_address, M_distribution_address, T_maintoplistdist, T_MaintoplibraryDisDef
)
from SFD.models import (
    ShipEquipment,
    GenericSpecification,
    Generic,
    EquipmentSpecification,
    Equipment,
    Supplier,
    EquipmentPolicy,
    Country,
    OpsAuthority,
    Propulsion,
    ShipClass,
    Command,
)
from Master.models import (
    Ch_Master_Symptoms,
    Department,
    Group,
    M_Delay,
    M_Diagnostic,
    M_Repair,
    M_RepairAgency,
    MRefit,
    MRefitCategory,
    RefitMaintenancePeriod,
    MRequiredAssistance,
    M_Severity,
    Section,
    Ship,
    Ch_Master_Ship_Remarks_By,
    M_Delinquery,
    T_RefComDelinqueryDetail,
    T_DryDocking,
    M_OCR,
    T_ABER,
    T_OpdefMain,
    T_opdefgeneratinfo,
    T_DefectAnalysis,
    T_MajorSpareconsumer,
    T_trailconductedParameter,
    T_opdefpriorparameter,
    T_photograph,
    M_Deferment,
    M_Reason,
    M_Inability,
    SFDHierarchy,
)
from django.db import transaction

router = APIRouter(
    prefix="/cmms",
    tags=["CMMS Integration"],
    dependencies=[Depends(verify_api_key)]
)


def _value(obj, *names):
    for name in names:
        if name is None:
            continue
        value = getattr(obj, name, None)
        if value is not None:
            return value
    return None


def _to_dict(obj):
    if not obj:
        return {}
    if isinstance(obj, dict):
        return obj
    raw = getattr(obj, "__dict__", {})
    d = {}
    for k, v in raw.items():
        if k.startswith("_"):
            continue
        if isinstance(v, (date, datetime)):
            d[k] = v.isoformat()
        else:
            d[k] = v
    return d


def _date_value(value):
    return value.isoformat() if value else None


def _master_row(obj, id_field, code_field, name_field, universal_field=None):
    return {
        "id": _value(obj, id_field),
        "code": _value(obj, code_field),
        "name": _value(obj, name_field),
        "universal_id": _value(obj, universal_field) if universal_field else None,
        "active": _value(obj, "Active", "active", "active_external"),
    }


def _t_dart_row(defect):
    completion = getattr(defect, "cmms_completion", None)
    equipment_ship = getattr(defect, "equipment_ship", None)
    department = getattr(defect, "department_id", None)

    return {
        "id": defect.id,
        "dart_number": defect.dart_number,
        "dart_sr_number": defect.dart_sr_number,
        "dart_date": _date_value(defect.dart_date),
        "rectification_date": _date_value(defect.rectification_date),
        "is_closed": defect.is_closed,
        "maintenance_period": defect.maintenance_period,
        "dart_occasion": defect.dart_occasion,
        "defective_component": defect.defective_component,
        "defective_descriptions": defect.defective_discriptions,
        "rha_defect": defect.RHA_defect,
        "trial_required": defect.trial_required,
        "ops_status": defect.ops_status,
        "is_guarantee_defect": defect.is_guarantee_defect,
        "cmms_sync_status": defect.cmms_sync_status,
        "universal_id_m_ship": _value(
            getattr(equipment_ship, "ship", None),
            "universal_id_m_ship",
        ),
        "universal_id_m_department": _value(
            department,
            "universal_id_m_department",
        ),
        "repair_agency_id": _value(completion, "repair_agency_code_id"),
        "diagnostic_id": _value(completion, "diagnostic_code_id"),
        "repair_id": _value(completion, "repair_code_id"),
        "delay_id": _value(completion, "delay_code_id"),
        "rectified_date": _date_value(_value(completion, "rectified_date")),
        "days_delay": _value(completion, "days_delay"),
        "spares_delay": _value(completion, "spares_delay"),
        "other_reasons": _value(completion, "other_reasons"),
        "lesson_learnt": _value(completion, "lesson_learnt"),
    }


def _build_dart_payload():
    completions = {
        item.dart_details_id: item
        for item in Complete_defect_dart.objects.select_related(
            "repair_agency_code",
            "diagnostic_code",
            "repair_code",
            "delay_code",
        )
    }
    defects = list(
        Initiate_Dart.objects.select_related(
            "department_id",
            "equipment_ship__ship",
        ).order_by("-created_date", "-id")
    )

    for defect in defects:
        defect.cmms_completion = completions.get(defect.id)

    return {
        "M_Diagnostic": [
            _master_row(row, "DiagnosticId", "DiagnosticCode", "DiagnosticName", "Universal_ID_M_Diagnostic")
            for row in M_Diagnostic.objects.all()
        ],
        "M_Refit": [
            _master_row(row, "refit_id", None, "refit_type", "universal_id_m_refit")
            for row in MRefit.objects.all()
        ],
        "M_Ship": [
            _master_row(row, "id", "code", "name", "universal_id_m_ship")
            for row in Ship.objects.all()
        ],
        "M_group": [
            _master_row(row, "id", "code", "name", None)
            for row in Group.objects.all()
        ],
        "M_department": [
            _master_row(row, "id", "code", "name", "universal_id_m_department")
            for row in Department.objects.all()
        ],
        "M_repair agency": [
            _master_row(row, "RepairAgencyID", "RepairAgencyCode", "RepairAgencyName", "Universal_ID_M_RepairAgency")
            for row in M_RepairAgency.objects.all()
        ],
        "M_Delay": [
            _master_row(row, "DelayID", "DelayCode", "DelayName", "Universal_ID_M_Delay")
            for row in M_Delay.objects.all()
        ],
        "M_Repair": [
            _master_row(row, "RepairID", "RepairCode", "RepairName", "Universal_ID_M_Repair")
            for row in M_Repair.objects.all()
        ],
        "M_section": [
            _master_row(row, "id", "code", "name", None)
            for row in Section.objects.all()
        ],
        "T_DART": [_t_dart_row(defect) for defect in defects],
    }


@router.get("/dart", response_model=CmmsDartPayloadResponse)
async def get_dart_cmms_payload():
    return await sync_to_async(_build_dart_payload)()

# ==========================================
# 1. DEFECTS (DART / OF_def)
# ==========================================
@router.get("/defects", response_model=List[DefectResponse])
async def get_defects(
    is_closed: Optional[bool] = None,
    is_operational: Optional[bool] = None,
    equipment_code: Optional[str] = None
):
    def query():
        qs = Initiate_Dart.objects.all()
        if is_closed is not None:
            qs = qs.filter(is_closed=is_closed)
        if is_operational is not None:
            if is_operational:
                qs = qs.filter(maintenance_period="OPERATIONAL")
            else:
                qs = qs.exclude(maintenance_period="OPERATIONAL")
        if equipment_code:
            qs = qs.filter(equipment_ship__equipment__equipment_code=equipment_code)
        return list(qs.order_by("-created_date"))

    defects = await sync_to_async(query)()
    return defects

@router.get("/defects/{defect_id}", response_model=DefectResponse)
async def get_defect_detail(defect_id: int):
    def query():
        try:
            return Initiate_Dart.objects.get(id=defect_id)
        except Initiate_Dart.DoesNotExist:
            return None

    defect = await sync_to_async(query)()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    return defect

@router.post("/defects", response_model=DefectResponse)
async def create_defect(payload: DefectCreate):
    def save():
        # Fetch FK references
        equipment_ship = ShipEquipment.objects.filter(id=payload.equipment_ship_id).first() if payload.equipment_ship_id else None
        
        defect = Initiate_Dart.objects.create(
            symptom_code_id=payload.symptom_code_id,
            serverity_code_id=payload.severity_code_id,
            remark_code_id=payload.remark_code_id,
            require_assistance_for_code_id=payload.require_assistance_for_code_id,
            equipment_ship=equipment_ship,
            department_id_id=payload.department_id_id,
            equipment_ems_id=payload.equipment_ems_id,
            dart_number=payload.dart_number,
            dart_sr_number=payload.dart_sr_number,
            dart_date=payload.dart_date,
            rectification_date=payload.rectification_date,
            ops_status=payload.ops_status,
            trial_required=payload.trial_required,
            defective_discriptions=payload.defective_discriptions,
            defective_component=payload.defective_component,
            RHA_defect=payload.RHA_defect,
            maintenance_period=payload.maintenance_period,
            dart_occasion=payload.dart_occasion,
            is_guarantee_defect=payload.is_guarantee_defect
        )
        return defect

    try:
        defect = await sync_to_async(save)()
        return defect
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/defects/{defect_id}/rectify", response_model=GenericSuccessResponse)
async def rectify_defect(defect_id: int, payload: DefectRectifyRequest):
    def process_rectification():
        with transaction.atomic():
            defect = Initiate_Dart.objects.get(id=defect_id)
            
            # Create Complete_defect_dart record
            Complete_defect_dart.objects.create(
                serial_no=payload.serial_no,
                dart_no=defect.dart_number,
                dart_details=defect,
                rectified_date=payload.rectified_date,
                repair_agency_code_id=payload.repair_agency_code_id,
                diagnostic_code_id=payload.diagnostic_code_id,
                repair_code_id=payload.repair_code_id,
                delay_code_id=payload.delay_code_id,
                days_delay=payload.days_delay,
                spares_delay=payload.spares_delay,
                other_reasons=payload.other_reasons,
                lesson_learnt=payload.lesson_learnt
            )
            
            # Mark defect as closed
            defect.is_closed = True
            defect.rectification_date = payload.rectified_date
            defect.save()
            return True

    try:
        await sync_to_async(process_rectification)()
        return GenericSuccessResponse(success=True, message="Defect rectified and closed successfully.")
    except Initiate_Dart.DoesNotExist:
        raise HTTPException(status_code=404, detail="Defect not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 2. SRAR (Monthly Report)
# ==========================================
@router.get("/srar", response_model=List[SRARDetailResponse])
async def get_srar_list():
    def query():
        headers = SrarMonthlyHeader.objects.all().order_by("-srar_year", "-srar_month")
        results = []
        for h in headers:
            exploitations = list(h.equipment_exploitations.all())
            h.equipment_exploitations_list = exploitations
            results.append(h)
        return results

    results = await sync_to_async(query)()
    # Map results to schemas
    mapped = []
    for h in results:
        mapped.append(
            SRARDetailResponse(
                id=h.id,
                ship_id=h.ship_id,
                srar_month=h.srar_month,
                srar_year=h.srar_year,
                distance_run_month=float(h.distance_run_month) if h.distance_run_month else None,
                max_speed=h.max_speed,
                eo_name=h.eo_name,
                equipment_exploitations=[
                    SrarEquipmentExploitationResponse(
                        id=ex.id,
                        sfd_details_id=ex.sfd_details_id,
                        hrs_for_month=ex.hrs_for_month,
                        rhsi_till_prev_month=ex.rhsi_till_prev_month,
                        rhsi_till_current_month=ex.rhsi_till_current_month
                    ) for ex in h.equipment_exploitations_list
                ]
            )
        )
    return mapped

@router.post("/srar", response_model=GenericSuccessResponse)
async def create_srar(
    header: SRARMonthlyHeaderCreate,
    exploitations: List[SrarEquipmentExploitationCreate]
):
    def save():
        with transaction.atomic():
            # Create header
            h = SrarMonthlyHeader.objects.create(
                ship_id=header.ship_id,
                srar_month=header.srar_month,
                srar_year=header.srar_year,
                hours_underway_month_hr=header.hours_underway_month_hr,
                hours_underway_month_min=header.hours_underway_month_min,
                distance_run_month=header.distance_run_month,
                distance_run_since_commissioning=header.distance_run_since_commissioning,
                max_speed=header.max_speed,
                eo_name=header.eo_name
            )
            
            # Create exploitations
            for exp in exploitations:
                SrarEquipmentExploitation.objects.create(
                    srar_monthly_header=h,
                    sfd_details_id=exp.sfd_details_id,
                    hrs_for_month=exp.hrs_for_month,
                    hrs_for_month_min=exp.hrs_for_month_min,
                    hrs_for_month_hrs=exp.hrs_for_month_hrs,
                    rhsi_till_current_month=exp.rhsi_till_current_month
                )
            return h.id

    try:
        header_id = await sync_to_async(save)()
        return GenericSuccessResponse(success=True, message=f"SRAR report created successfully with ID {header_id}.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 3. ROUTINES (Activity Calendar)
# ==========================================
@router.get("/routines/completed", response_model=List[CompletedRoutineResponse])
async def get_completed_routines():
    def query():
        return list(CompletedRoutine.objects.all().order_by("-created_at")[:100])
    
    completed = await sync_to_async(query)()
    return completed

@router.post("/routines/complete", response_model=GenericSuccessResponse)
async def complete_routine(payload: CompletedRoutineCreate):
    def save():
        routine = RoutineDescription.objects.get(id=payload.routine_id)
        CompletedRoutine.objects.create(
            routine=routine,
            old_dart_number=payload.old_dart_number,
            new_dart_number=payload.new_dart_number,
            date_of_completion=payload.date_of_completion,
            hours=payload.hours,
            minutes=payload.minutes,
            carried_by=payload.carried_by,
            p_no=payload.p_no,
            running_hour=payload.running_hour,
            due_running_hour=payload.due_running_hour,
            completion_details=payload.completion_details
        )
        return True

    try:
        await sync_to_async(save)()
        return GenericSuccessResponse(success=True, message="Routine completion recorded successfully.")
    except RoutineDescription.DoesNotExist:
        raise HTTPException(status_code=404, detail="Routine description not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 4. FUSS (Deferment)
# ==========================================
@router.get("/fuss", response_model=FussSyncPayloadResponse)
async def get_fuss_sync_payload():
    def query():
        try:
            t_fuss = list(FussRaiseDetails.objects.filter(isclosed_fuss=False))
        except Exception:
            t_fuss = []
        try:
            m_def = list(M_Deferment.objects.all())
        except Exception:
            m_def = []
        try:
            m_rsn = list(M_Reason.objects.all())
        except Exception:
            m_rsn = []
        try:
            m_inab = list(M_Inability.objects.all())
        except Exception:
            m_inab = []
        
        return {
            "T_fuss": t_fuss,
            "M_Deferment": m_def,
            "M_Reason": m_rsn,
            "M_Inability": m_inab
        }

    try:
        return await sync_to_async(query)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fuss", response_model=GenericSuccessResponse)
async def raise_deferment(payload: FussRaiseRequest):
    def save():
        try:
            routine = RoutineDescription.objects.get(id=payload.routine_description_id)
            routine_val = routine
        except Exception:
            routine_val = payload.routine_description_id

        serial_no = f"FUSS-2026-{payload.routine_description_id}"
        FussRaiseDetails.objects.create(
            routine_description_id=routine_val,
            fuss_date=payload.fuss_date,
            last_undertaken=payload.last_undertaken,
            due_date=payload.due_date,
            schedule_date=payload.schedule_date,
            equipment=payload.equipment,
            location_on_board=payload.location_on_board,
            maintop_no=payload.maintop_no,
            frequency=payload.frequency,
            isclosed_fuss=False,
            serial_no=serial_no
        )

    try:
        await sync_to_async(save)()
        return GenericSuccessResponse(success=True, message="Deferment (FUSS) raised successfully.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 5. ABER (Annual Budget Estimate of Repair)
# ==========================================
@router.get("/aber", response_model=List[AberEquipmentResponse])
async def get_aber_equipment():
    def query():
        # ABER: fitted equipment older than 6 years (installation_date <= today - 6 years)
        six_years_ago = date.today() - relativedelta(years=6)
        equipments = ShipEquipment.objects.filter(installation_date__lte=six_years_ago)
        
        results = []
        for eq in equipments:
            age_years = relativedelta(date.today(), eq.installation_date).years
            results.append(
                AberEquipmentResponse(
                    id=eq.id,
                    nomenclature=eq.nomenclature or "Unknown Nomenclature",
                    equipment_code=eq.equipment.equipment_code if (eq.equipment and eq.equipment.equipment_code) else "N/A",
                    installation_date=eq.installation_date,
                    age_years=float(age_years)
                )
            )
        return results

    results = await sync_to_async(query)()
    return results


# ==========================================
# 6. SFD (Ship Fit Database)
# ==========================================
@router.get("/sfd", response_model=List[ShipEquipmentResponse])
async def get_sfd_equipments(ship_id: Optional[int] = None):
    def query():
        qs = ShipEquipment.objects.all()
        if ship_id:
            qs = qs.filter(ship_id=ship_id)
        return list(qs)

    equipments = await sync_to_async(query)()
    return equipments


@router.get("/sfd/payload", response_model=SfdSyncPayloadResponse)
async def get_sfd_payload():
    def query():
        try:
            t_genspec = list(GenericSpecification.objects.all())
        except Exception:
            t_genspec = []
        try:
            m_grp = list(Group.objects.all())
        except Exception:
            m_grp = []
        try:
            m_sec = list(Section.objects.all())
        except Exception:
            m_sec = []
        try:
            m_eq = list(Equipment.objects.all())
        except Exception:
            m_eq = []
        try:
            m_sh = list(Ship.objects.all())
        except Exception:
            m_sh = []
        try:
            m_gen = list(Generic.objects.all())
        except Exception:
            m_gen = []
        try:
            m_cmd = list(Command.objects.all())
        except Exception:
            m_cmd = []
        try:
            m_ops = list(OpsAuthority.objects.all())
        except Exception:
            m_ops = []
        try:
            t_eqspec = list(EquipmentSpecification.objects.all())
        except Exception:
            t_eqspec = []
        try:
            t_eqship = list(ShipEquipment.objects.all())
        except Exception:
            t_eqship = []
        try:
            m_shhier = list(SFDHierarchy.objects.all())
        except Exception:
            m_shhier = []
        try:
            m_prop = list(Propulsion.objects.all())
        except Exception:
            m_prop = []
        try:
            t_eqpol = list(EquipmentPolicy.objects.all())
        except Exception:
            t_eqpol = []
        try:
            m_cty = list(Country.objects.all())
        except Exception:
            m_cty = []
        try:
            m_shcls = list(ShipClass.objects.all())
        except Exception:
            m_shcls = []
        try:
            m_sup = list(Supplier.objects.all())
        except Exception:
            m_sup = []
            
        return {
            "T_genericspecification": [_to_dict(x) for x in t_genspec],
            "M_group": [_to_dict(x) for x in m_grp],
            "M_Section": [_to_dict(x) for x in m_sec],
            "M_Equipment": [_to_dict(x) for x in m_eq],
            "M_ship": [_to_dict(x) for x in m_sh],
            "M_generic": [_to_dict(x) for x in m_gen],
            "M_command": [_to_dict(x) for x in m_cmd],
            "M_Ops Authority": [_to_dict(x) for x in m_ops],
            "T_Equipment Specification": [_to_dict(x) for x in t_eqspec],
            "T_EquipmentShipDetail": [_to_dict(x) for x in t_eqship],
            "M_Ship Hierarchy": [_to_dict(x) for x in m_shhier],
            "T_HTD EquipmentDetail": [],
            "T_EquipmentCommonspecdiffer": [],
            "M_propulsion": [_to_dict(x) for x in m_prop],
            "T_equipment policy": [_to_dict(x) for x in t_eqpol],
            "M_country": [_to_dict(x) for x in m_cty],
            "M_ship class": [_to_dict(x) for x in m_shcls],
            "T_equipment Supplier": [_to_dict(x) for x in m_sup],
            "M_Supplier": [_to_dict(x) for x in m_sup]
        }

    try:
        return await sync_to_async(query)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sfd/sync")
async def sync_sfd_payload(payload: dict):
    def process():
        records = payload.get("T_EquipmentShipDetail", [])
        processed = 0
        ignored = 0
        
        for item in records:
            item_id = item.get("id")
            nomenclature = item.get("nomenclature")
            
            existing = ShipEquipment.objects.filter(id=item_id).first()
            if existing:
                if getattr(existing, "is_synced", False):
                    ignored += 1
                else:
                    existing.nomenclature = nomenclature
                    existing.is_synced = True
                    existing.save()
                    processed += 1
            else:
                ShipEquipment.objects.create(
                    id=item_id,
                    nomenclature=nomenclature,
                    is_synced=True
                )
                processed += 1
                
        message = "Sync completed successfully." if processed > 0 else "No new records to sync."
        return {"processed": processed, "ignored": ignored, "message": message}

    try:
        return await sync_to_async(process)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sfd/ships", response_model=List[SfdShipResponse])
async def get_sfd_ships():
    def query():
        try:
            ships = list(Ship.objects.all())
        except Exception:
            ships = []
        results = []
        for s in ships:
            cmd_name = s.command.CommandName if getattr(s, "command", None) else None
            auth_name = s.authority.OpsAuthority if getattr(s, "authority", None) else None
            results.append({
                "id": s.id,
                "name": s.name,
                "code": s.code,
                "universal_id_m_ship": s.universal_id_m_ship,
                "class_code": getattr(s, "class_code", None),
                "command_name": cmd_name,
                "authority_name": auth_name
            })
        return results

    try:
        return await sync_to_async(query)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 7. REFIT INTEGRATION
# ==========================================
@router.get("/refit", response_model=RefitSyncPayloadResponse)
async def get_refit_sync_payload():
    def query():
        return {
            "M_Delinquery": [
                {
                    "id": d.DelinqueryID,
                    "code": d.DelinqueryCode,
                    "name": d.DelinqueryName,
                    "universal_id": d.Universal_ID_M_Delinquery,
                    "active": d.Active
                }
                for d in M_Delinquery.objects.all()
            ],
            "T_RefComDelinquery Detail": [
                {
                    "id": d.RefComDelinqueryDetailID,
                    "universal_id_t_refcomp": d.Universal_ID_T_RefComp,
                    "delinquency_code": d.DelinqueryCode,
                    "description": d.Description,
                    "days_delayed": d.DaysDelayed,
                    "remarks": d.Remarks,
                    "universal_id_t_refcomdelinquerydetail": d.Universal_ID_T_RefComDelinqueryDetail
                }
                for d in T_RefComDelinqueryDetail.objects.all()
            ],
            "M_Refit": [
                {
                    "id": r.refit_id,
                    "type": r.refit_type,
                    "description": r.description,
                    "universal_id_m_refit": r.universal_id_m_refit,
                    "active": r.active
                }
                for r in MRefit.objects.all()
            ],
            "T_DryDocking": [
                {
                    "id": d.DryDockingID,
                    "universal_id_t_refcomp": d.Universal_ID_T_RefComp,
                    "dock_entry_date": _date_value(d.DockEntryDate),
                    "dock_undock_date": _date_value(d.DockUndockDate),
                    "yard_dock_name": d.YardDockName,
                    "hull_inspection_status": d.HullInspectionStatus,
                    "universal_id_t_drydocking": d.Universal_ID_T_DryDocking
                }
                for d in T_DryDocking.objects.all()
            ],
            "M-OCR": [
                {
                    "id": o.OCRID,
                    "universal_id_t_refcomp": o.Universal_ID_T_RefComp,
                    "report_ref_no": o.ReportRefNo,
                    "clearance_status": o.ClearanceStatus,
                    "trial_outcome": o.TrialOutcome,
                    "report_date": _date_value(o.ReportDate),
                    "universal_id_m_ocr": o.Universal_ID_M_OCR
                }
                for o in M_OCR.objects.all()
            ],
            "T_Refcomp": [
                {
                    "id": r.id,
                    "name": r.name,
                    "maintenance_period": r.maintenance_period,
                    "occasion": r.occasion,
                    "plan_start_date": _date_value(r.plan_start_date),
                    "plan_end_date": _date_value(r.plan_end_date),
                    "actual_start_date": _date_value(r.actual_start_date),
                    "actual_end_date": _date_value(r.actual_end_date),
                    "universal_id_t_refcomp": r.Universal_ID_T_RefComp,
                    "universal_id_m_command": r.Universal_ID_M_Command,
                    "universal_id_m_ship": r.Universal_ID_M_Ship,
                    "universal_id_m_refit": r.Universal_ID_M_Refit,
                    "universal_id_m_refitplace": r.Universal_ID_M_RefitPlace
                }
                for r in RefitMaintenancePeriod.objects.all()
            ]
        }
    return await sync_to_async(query)()


@router.get("/refit/completions", response_model=List[dict])
async def get_refit_completions():
    def query():
        return [
            {
                "id": r.id,
                "name": r.name,
                "maintenance_period": r.maintenance_period,
                "occasion": r.occasion,
                "plan_start_date": _date_value(r.plan_start_date),
                "plan_end_date": _date_value(r.plan_end_date),
                "actual_start_date": _date_value(r.actual_start_date),
                "actual_end_date": _date_value(r.actual_end_date),
                "universal_id_t_refcomp": r.Universal_ID_T_RefComp,
                "universal_id_m_command": r.Universal_ID_M_Command,
                "universal_id_m_ship": r.Universal_ID_M_Ship,
                "universal_id_m_refit": r.Universal_ID_M_Refit,
                "universal_id_m_refitplace": r.Universal_ID_M_RefitPlace
            }
            for r in RefitMaintenancePeriod.objects.all()
        ]
    return await sync_to_async(query)()


@router.post("/refit/completions", response_model=RefitCompletionResponse, status_code=201)
async def create_refit_completion(payload: RefitCompletionCreate):
    def save():
        ship = Ship.objects.filter(universal_id_m_ship=payload.ship_code).first()
        refit = MRefit.objects.filter(refit_type=payload.refit_type).first()
        category = refit.refit_category_f_key if refit else None
        
        # generate a temporary universal ID if none is provided
        universal_id = f"U-RC-{date.today().isoformat()}-{payload.ship_code}"
        
        r = RefitMaintenancePeriod.objects.create(
            name=payload.refit_type,
            maintenance_period=payload.refit_type,
            occasion="Refit",
            plan_start_date=payload.planned_start_date,
            plan_end_date=payload.planned_end_date,
            actual_start_date=payload.actual_start_date,
            actual_end_date=payload.actual_end_date,
            Universal_ID_T_RefComp=universal_id,
            Universal_ID_M_Command=payload.universal_id_m_command,
            Universal_ID_M_Ship=payload.ship_code,
            Universal_ID_M_Refit=refit.universal_id_m_refit if refit else None,
            Universal_ID_M_RefitPlace=payload.refit_place,
            ship_universal_f_key=ship,
            universal_m_refit=refit,
            refit_category_f_key=category
        )
        return r
    try:
        r = await sync_to_async(save)()
        return r
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refit/completions/{universal_id_t_refcomp}/delinquency", response_model=GenericSuccessResponse)
async def log_refit_delinquency(universal_id_t_refcomp: str, payload: RefitDelinquencyCreate):
    def save():
        detail_uid = f"U-RCD-{universal_id_t_refcomp}-{payload.delinquency_code}"
        T_RefComDelinqueryDetail.objects.create(
            Universal_ID_T_RefComp=universal_id_t_refcomp,
            DelinqueryCode=payload.delinquency_code,
            Description=payload.description,
            DaysDelayed=payload.days_delayed,
            Remarks=payload.remarks,
            Universal_ID_T_RefComDelinqueryDetail=detail_uid
        )
    try:
        await sync_to_async(save)()
        return GenericSuccessResponse(success=True, message="Delinquency detail logged successfully.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refit/completions/{universal_id_t_refcomp}/drydock", response_model=GenericSuccessResponse)
async def log_refit_drydock(universal_id_t_refcomp: str, payload: RefitDryDockingCreate):
    def save():
        dock_uid = f"U-DD-{universal_id_t_refcomp}"
        T_DryDocking.objects.create(
            Universal_ID_T_RefComp=universal_id_t_refcomp,
            DockEntryDate=payload.dock_entry_date,
            DockUndockDate=payload.dock_undock_date,
            YardDockName=payload.yard_dock_name,
            HullInspectionStatus=payload.hull_inspection_status,
            Universal_ID_T_DryDocking=dock_uid
        )
    try:
        await sync_to_async(save)()
        return GenericSuccessResponse(success=True, message="Drydocking period logged successfully.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refit/completions/{universal_id_t_refcomp}/ocr", response_model=GenericSuccessResponse)
async def log_refit_ocr(universal_id_t_refcomp: str, payload: RefitOCRCreate):
    def save():
        ocr_uid = f"U-OCR-{universal_id_t_refcomp}"
        M_OCR.objects.create(
            Universal_ID_T_RefComp=universal_id_t_refcomp,
            ReportRefNo=payload.report_ref_no,
            ClearanceStatus=payload.clearance_status,
            TrialOutcome=payload.trial_outcome,
            ReportDate=payload.report_date,
            Universal_ID_M_OCR=ocr_uid
        )
    try:
        await sync_to_async(save)()
        return GenericSuccessResponse(success=True, message="OCR status updated successfully.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/aber", response_model=List[AberEquipmentResponse])
async def get_aber_due_list():
    def get_list():
        six_years_ago = date.today() - relativedelta(years=6)
        qs = ShipEquipment.objects.filter(installation_date__lte=six_years_ago)
        results = []
        for item in qs:
            inst_date = getattr(item, "installation_date", None)
            if not inst_date:
                continue
            age_years = (date.today() - inst_date).days / 365.25
            if age_years < 6.0:
                continue
            
            eq_code = ""
            if getattr(item, "equipment", None):
                eq_code = getattr(item.equipment, "equipment_code", "")
            
            ship_uid = None
            if getattr(item, "ship", None):
                ship_uid = getattr(item.ship, "universal_id_m_ship", None)
                
            results.append({
                "id": item.id,
                "nomenclature": getattr(item, "nomenclature", ""),
                "equipment_code": eq_code,
                "installation_date": inst_date,
                "age_years": age_years,
                "universal_id_m_ship": ship_uid
            })
        return results

    try:
        return await sync_to_async(get_list)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/aber/submit", response_model=AberSubmitResponse, status_code=status.HTTP_201_CREATED)
async def submit_aber_estimate(payload: AberSubmitRequest):
    def save():
        try:
            ship = Ship.objects.filter(id=payload.ship_id).first()
            ship_uid = ship.universal_id_m_ship if ship else f"U-SHIP-{payload.ship_id}"
        except Exception:
            ship_uid = f"U-SHIP-{payload.ship_id}"
        
        try:
            fit_eq = ShipEquipment.objects.filter(id=payload.fitted_equipment_id).first()
            fit_uid = fit_eq.t_equipment_ship_detail if fit_eq else f"U-EQ-{payload.fitted_equipment_id}"
        except Exception:
            fit_uid = f"U-EQ-{payload.fitted_equipment_id}"
        
        temp_uid = f"U-ABER-{payload.ship_id}-{payload.fitted_equipment_id}-{payload.budget_year}"
        
        aber = T_ABER.objects.create(
            Universal_ID_M_Ship=ship_uid,
            Universal_ID_T_EquipmentShipDetail=fit_uid,
            BudgetYear=payload.budget_year,
            EstimateCost=payload.estimate_cost,
            Currency=payload.currency,
            ABERAuthority=payload.aber_authority,
            RepairAgencyID=payload.repair_agency_id,
            Remarks=payload.remarks,
            Universal_ID_T_ABER=temp_uid
        )
        return aber

    try:
        return await sync_to_async(save)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/aber/history", response_model=List[AberSubmitResponse])
async def get_aber_history(ship_id: Optional[str] = None, year: Optional[int] = None):
    def query():
        filters = {}
        if ship_id:
            filters["Universal_ID_M_Ship"] = ship_id
        if year:
            filters["BudgetYear"] = year
        
        qs = T_ABER.objects.filter(**filters)
        return list(qs)
        
    try:
        return await sync_to_async(query)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/opdef", response_model=OpdefSyncPayloadResponse)
async def get_opdef_payload():
    def query():
        try:
            opdef_main = list(T_OpdefMain.objects.all())
        except Exception:
            opdef_main = []
        try:
            opdef_gen = list(T_opdefgeneratinfo.objects.all())
        except Exception:
            opdef_gen = []
        try:
            defect_anal = list(T_DefectAnalysis.objects.all())
        except Exception:
            defect_anal = []
        try:
            spare_cons = list(T_MajorSpareconsumer.objects.all())
        except Exception:
            spare_cons = []
        try:
            trail_cond = list(T_trailconductedParameter.objects.all())
        except Exception:
            trail_cond = []
        try:
            prior_param = list(T_opdefpriorparameter.objects.all())
        except Exception:
            prior_param = []
        try:
            photo = list(T_photograph.objects.all())
        except Exception:
            photo = []
        
        return {
            "T_OpdefMain": opdef_main,
            "T_opdefgeneratinfo": opdef_gen,
            "T_DefectAnalysis": defect_anal,
            "T_MajorSpareconsumer": spare_cons,
            "T_trailconductedParameter": trail_cond,
            "T_opdefpriorparameter": prior_param,
            "T_photograph": photo
        }
    try:
        return await sync_to_async(query)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/opdef", response_model=OpdefInitiateResponse, status_code=status.HTTP_201_CREATED)
async def initiate_opdef(payload: OpdefInitiateRequest):
    def save():
        try:
            ship = Ship.objects.filter(id=payload.ship_id).first()
            ship_uid = ship.universal_id_m_ship if ship else f"U-SHIP-{payload.ship_id}"
        except Exception:
            ship_uid = f"U-SHIP-{payload.ship_id}"
        
        try:
            fit_eq = ShipEquipment.objects.filter(id=payload.fitted_equipment_id).first()
            fit_uid = fit_eq.t_equipment_ship_detail if fit_eq else f"U-EQ-{payload.fitted_equipment_id}"
        except Exception:
            fit_uid = f"U-EQ-{payload.fitted_equipment_id}"

        temp_uid = f"U-OPD-{payload.ship_id}-{payload.fitted_equipment_id}-{payload.opdef_number}"

        with transaction.atomic():
            main = T_OpdefMain.objects.create(
                Universal_ID_M_Ship=ship_uid,
                Universal_ID_T_EquipmentShipDetail=fit_uid,
                OpdefNumber=payload.opdef_number,
                OpdefDate=payload.opdef_date,
                DepartmentID=payload.department_id,
                DefectDescription=payload.defect_description,
                Universal_ID_T_OpdefMain=temp_uid
            )

            T_opdefgeneratinfo.objects.create(
                Universal_ID_T_OpdefMain=temp_uid,
                OperationalImpact=payload.operational_impact,
                Universal_ID_T_OpdefGeneratInfo=f"U-OPDG-{temp_uid}"
            )
            return main

    try:
        return await sync_to_async(save)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/opdef/{opdef_id}/analysis", response_model=GenericSuccessResponse)
async def submit_opdef_analysis(opdef_id: int, payload: OpdefAnalysisRequest):
    def save():
        main = T_OpdefMain.objects.get(id=opdef_id)
        temp_uid = f"U-OPDA-{opdef_id}"
        T_DefectAnalysis.objects.create(
            Universal_ID_T_OpdefMain=main.Universal_ID_T_OpdefMain,
            AnalysisDate=payload.analysis_date,
            FailureCause=payload.failure_cause,
            RectificationMethodProposed=payload.rectification_method_proposed,
            AnalysedBy=payload.analysed_by,
            Universal_ID_T_DefectAnalysis=temp_uid
        )

    try:
        await sync_to_async(save)()
        return GenericSuccessResponse(success=True, message="Defect analysis recorded successfully.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/opdef/{opdef_id}/spares", response_model=GenericSuccessResponse)
async def log_opdef_spares(opdef_id: int, payload: OpdefSpareRequest):
    def save():
        main = T_OpdefMain.objects.get(id=opdef_id)
        temp_uid = f"U-OPDS-{opdef_id}-{payload.spare_item_code}"
        T_MajorSpareconsumer.objects.create(
            Universal_ID_T_OpdefMain=main.Universal_ID_T_OpdefMain,
            SpareItemCode=payload.spare_item_code,
            Nomenclature=payload.nomenclature,
            QuantityConsumed=payload.quantity_consumed,
            UnitCost=payload.unit_cost,
            Remarks=payload.remarks,
            Universal_ID_T_MajorSpareConsumer=temp_uid
        )

    try:
        await sync_to_async(save)()
        return GenericSuccessResponse(success=True, message="Spare consumption recorded successfully.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/opdef/{opdef_id}/trials", response_model=GenericSuccessResponse)
async def log_opdef_trials(opdef_id: int, payload: OpdefTrialRequest):
    def save():
        main = T_OpdefMain.objects.get(id=opdef_id)
        temp_uid = f"U-OPDT-{opdef_id}"
        T_trailconductedParameter.objects.create(
            Universal_ID_T_OpdefMain=main.Universal_ID_T_OpdefMain,
            TrialDate=payload.trial_date,
            RPMReading=payload.rpm_reading,
            TemperatureCelsius=payload.temperature_celsius,
            VibrationVelocityMMS=payload.vibration_velocity_mms,
            Status=payload.status,
            Universal_ID_T_TrialConductedParameter=temp_uid
        )

    try:
        await sync_to_async(save)()
        return GenericSuccessResponse(success=True, message="Trial parameters logged successfully.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/opdef/{opdef_id}/prior-parameters", response_model=GenericSuccessResponse)
async def log_opdef_prior_params(opdef_id: int, payload: OpdefPriorParamRequest):
    def save():
        main = T_OpdefMain.objects.get(id=opdef_id)
        temp_uid = f"U-OPDP-{opdef_id}"
        T_opdefpriorparameter.objects.create(
            Universal_ID_T_OpdefMain=main.Universal_ID_T_OpdefMain,
            ReadingTime=payload.reading_time,
            RPMReading=payload.rpm_reading,
            TemperatureCelsius=payload.temperature_celsius,
            VibrationVelocityMMS=payload.vibration_velocity_mms,
            Remarks=payload.remarks,
            Universal_ID_T_OpdefPriorParameter=temp_uid
        )

    try:
        await sync_to_async(save)()
        return GenericSuccessResponse(success=True, message="Prior parameters logged successfully.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/opdef/{opdef_id}/photographs", response_model=OpdefPhotoResponse)
async def upload_opdef_photograph(
    opdef_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    def save(file_path):
        main = T_OpdefMain.objects.get(id=opdef_id)
        temp_uid = f"U-OPDPH-{opdef_id}"
        T_photograph.objects.create(
            Universal_ID_T_OpdefMain=main.Universal_ID_T_OpdefMain,
            FilePath=file_path,
            Description=description or "",
            UploadedDate=datetime.now(),
            Universal_ID_T_Photograph=temp_uid
        )

    try:
        file_path = f"/media/opdef_photos/{file.filename}"
        await sync_to_async(save)(file_path)
        return OpdefPhotoResponse(
            success=True,
            file_path=file_path,
            message="Photograph associated successfully."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fuss/masters", response_model=FussMastersResponse)
async def get_fuss_masters():
    def query():
        try:
            def_list = list(M_Deferment.objects.all())
        except Exception:
            def_list = []
        try:
            rsn_list = list(M_Reason.objects.all())
        except Exception:
            rsn_list = []
        try:
            inab_list = list(M_Inability.objects.all())
        except Exception:
            inab_list = []
        
        return {
            "M_deferment": def_list,
            "M_reason": rsn_list,
            "M_inability": inab_list
        }

    try:
        return await sync_to_async(query)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 8. MAINTOP INTEGRATION
# ==========================================

@router.post("/maintop/sync", response_model=MaintopSyncResponse)
async def sync_maintop(payload: MaintopSyncRequest):
    def save():
        with transaction.atomic():
            headers_count = 0
            details_count = 0
            
            for item in payload.T_maintopheader:
                MaintopHeader.objects.update_or_create(
                    universal_id_t_maintopheader=item.Universal_ID_T_MaintopHeader,
                    defaults={
                        "maintop_id": item.MaintopID,
                        "maintop_no": item.MaintopNo,
                        "maintop_title": item.MaintopTitle,
                        "amendment_no": item.AmendmentNo,
                        "active": bool(item.Active) if item.Active is not None else None,
                        "universal_id_t_maintopheader": item.Universal_ID_T_MaintopHeader,
                    }
                )
                headers_count += 1
                
            for item in payload.T_maintopdetail:
                header = None
                if item.Universal_ID_T_MaintopHeader:
                    try:
                        header = MaintopHeader.objects.filter(
                            universal_id_t_maintopheader=item.Universal_ID_T_MaintopHeader
                        ).first()
                    except Exception:
                        pass
                
                MaintopDetail.objects.update_or_create(
                    universal_id_t_maintopdetail=item.Universal_ID_T_MaintopDetail,
                    defaults={
                        "routine_id": item.RoutineID,
                        "maintopheader_f_key": header,
                        "maintop_id": item.MaintopID,
                        "maintop_no": item.MaintopNo,
                        "routine_no": item.RoutineNo,
                        "routine_description": item.RoutineDescription,
                        "frequency": item.Frequency,
                        "active": bool(item.Active) if item.Active is not None else None,
                        "universal_id_t_maintopheader": item.Universal_ID_T_MaintopHeader,
                        "universal_id_t_maintopdetail": item.Universal_ID_T_MaintopDetail,
                    }
                )
                details_count += 1
                
            return headers_count, details_count

    try:
        hc, dc = await sync_to_async(save)()
        return MaintopSyncResponse(status=True, headers_processed=hc, details_processed=dc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/maintop/jic", response_model=MaintopJICResponse)
async def sync_maintop_jic(payload: MaintopJICRequest):
    def save():
        with transaction.atomic():
            jics_count = 0
            spares_count = 0
            tools_count = 0
            attachments_count = 0
            
            for item in payload.T_maintopJIC:
                T_maintopJIC.objects.update_or_create(
                    Universal_ID_T_MaintopJIC=item.Universal_ID_T_MaintopJIC,
                    defaults={
                        "JICID": item.JICID,
                        "Universal_ID_T_MaintopJIC": item.Universal_ID_T_MaintopJIC,
                        "Universal_ID_T_MaintopDetail": item.Universal_ID_T_MaintopDetail,
                        "JobSteps": item.JobSteps,
                    }
                )
                jics_count += 1
                
            for item in payload.T_JICspares:
                T_JICspares.objects.update_or_create(
                    Universal_ID_T_JICspares=item.Universal_ID_T_JICspares,
                    defaults={
                        "JICID": item.JICID,
                        "SpareItemCode": item.SpareItemCode,
                        "Quantity": item.Quantity,
                        "Universal_ID_T_JICspares": item.Universal_ID_T_JICspares,
                    }
                )
                spares_count += 1
                
            for item in payload.T_JICtools:
                T_JICtools.objects.update_or_create(
                    Universal_ID_T_JICtools=item.Universal_ID_T_JICtools,
                    defaults={
                        "JICID": item.JICID,
                        "ToolCode": item.ToolCode,
                        "ToolName": item.ToolName,
                        "Universal_ID_T_JICtools": item.Universal_ID_T_JICtools,
                    }
                )
                tools_count += 1
                
            for item in payload.T_JICattachments:
                T_JICattachments.objects.update_or_create(
                    Universal_ID_T_JICattachments=item.Universal_ID_T_JICattachments,
                    defaults={
                        "JICID": item.JICID,
                        "FileName": item.FileName,
                        "FileUrl": item.FileUrl,
                        "Universal_ID_T_JICattachments": item.Universal_ID_T_JICattachments,
                    }
                )
                attachments_count += 1
                
            return jics_count, spares_count, tools_count, attachments_count

    try:
        jc, sc, tc, ac = await sync_to_async(save)()
        return MaintopJICResponse(
            status=True,
            jics_processed=jc,
            spares_processed=sc,
            tools_processed=tc,
            attachments_processed=ac
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/maintop/distribution", response_model=MaintopDistributionResponse)
async def sync_maintop_distribution(payload: MaintopDistributionRequest):
    def save():
        with transaction.atomic():
            addr_count = 0
            dist_count = 0
            list_count = 0
            def_count = 0
            
            for item in payload.M_address:
                M_address.objects.update_or_create(
                    Universal_ID_M_Address=item.Universal_ID_M_Address,
                    defaults={
                        "AddressID": item.AddressID,
                        "AddressName": item.AddressName,
                        "Universal_ID_M_Address": item.Universal_ID_M_Address,
                    }
                )
                addr_count += 1
                
            for item in payload.M_distribution_address:
                M_distribution_address.objects.update_or_create(
                    Universal_ID_M_DistributionAddress=item.Universal_ID_M_DistributionAddress,
                    defaults={
                        "DistAddressID": item.DistAddressID,
                        "AddressID": item.AddressID,
                        "DistName": item.DistName,
                        "Universal_ID_M_DistributionAddress": item.Universal_ID_M_DistributionAddress,
                    }
                )
                dist_count += 1
                
            for item in payload.T_maintoplistdist:
                T_maintoplistdist.objects.update_or_create(
                    Universal_ID_T_MaintopListDist=item.Universal_ID_T_MaintopListDist,
                    defaults={
                        "MaintopID": item.MaintopID,
                        "DistAddressID": item.DistAddressID,
                        "Active": item.Active,
                        "Universal_ID_T_MaintopListDist": item.Universal_ID_T_MaintopListDist,
                    }
                )
                list_count += 1
                
            for item in payload.T_MaintoplibraryDisDef:
                T_MaintoplibraryDisDef.objects.update_or_create(
                    Universal_ID_T_MaintopLibraryDisDef=item.Universal_ID_T_MaintopLibraryDisDef,
                    defaults={
                        "LibraryID": item.LibraryID,
                        "DefaultAddressID": item.DefaultAddressID,
                        "IsDefaultActive": item.IsDefaultActive,
                        "Universal_ID_T_MaintopLibraryDisDef": item.Universal_ID_T_MaintopLibraryDisDef,
                    }
                )
                def_count += 1
                
            return addr_count, dist_count, list_count, def_count

    try:
        ac, dc, lc, dfc = await sync_to_async(save)()
        return MaintopDistributionResponse(
            status=True,
            addresses_processed=ac,
            distributions_processed=dc,
            defaults_processed=dfc
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



