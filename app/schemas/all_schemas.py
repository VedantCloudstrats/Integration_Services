"""
All Pydantic v2 schemas for the CMMS Integration Microservice.
Covers: Common, DART, SRAR, FUSS, ABER, SFD, Refit, OPDEF, MAINTOP
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import date, datetime

# ─────────────────────────────────────────────────────────────
# COMMON
# ─────────────────────────────────────────────────────────────


class GenericSuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    status_code: int
    error: str
    detail: str


# ─────────────────────────────────────────────────────────────
# DART
# ─────────────────────────────────────────────────────────────


class DefectCreate(BaseModel):
    symptom_code_id: Optional[int] = None
    severity_code_id: Optional[int] = None
    remark_code_id: Optional[int] = None
    require_assistance_for_code_id: Optional[int] = None
    equipment_ship_id: Optional[int] = None
    department_id_id: Optional[int] = None
    equipment_ems_id: Optional[int] = None
    dart_number: Optional[str] = None
    dart_sr_number: Optional[str] = None
    dart_date: Optional[date] = None
    rectification_date: Optional[date] = None
    ops_status: Optional[bool] = None
    trial_required: Optional[bool] = None
    defective_discriptions: Optional[str] = None
    defective_component: Optional[str] = None
    RHA_defect: Optional[str] = None
    maintenance_period: Optional[str] = None
    dart_occasion: Optional[str] = None
    is_guarantee_defect: Optional[bool] = False


class DefectResponse(BaseModel):
    id: int
    dart_number: Optional[str] = None
    dart_sr_number: Optional[str] = None
    dart_date: Optional[date] = None
    rectification_date: Optional[date] = None
    is_closed: bool = False
    defective_discriptions: Optional[str] = None
    defective_component: Optional[str] = None
    maintenance_period: Optional[str] = None
    is_guarantee_defect: bool = False
    created_date: Optional[date] = None

    model_config = {"from_attributes": True}


class DefectRectifyRequest(BaseModel):
    serial_no: str
    rectified_date: date
    repair_agency_code_id: Optional[int] = None
    diagnostic_code_id: Optional[int] = None
    repair_code_id: Optional[int] = None
    delay_code_id: Optional[int] = None
    days_delay: Optional[int] = None
    spares_delay: Optional[int] = None
    other_reasons: Optional[str] = None
    lesson_learnt: Optional[str] = None


class CmmsDartPayloadResponse(BaseModel):
    M_Diagnostic: List[dict] = []
    M_Refit: List[dict] = []
    M_Ship: List[dict] = []
    M_group: List[dict] = []
    M_department: List[dict] = []
    M_repair_agency: List[dict] = Field(default=[], alias="M_repair agency")
    M_Delay: List[dict] = []
    M_Repair: List[dict] = []
    M_section: List[dict] = []
    T_DART: List[dict] = []

    model_config = {"populate_by_name": True}


# ─────────────────────────────────────────────────────────────
# SRAR
# ─────────────────────────────────────────────────────────────


class SRARMonthlyHeaderCreate(BaseModel):
    ship_id: Optional[int] = None
    srar_month: int
    srar_year: int
    hours_underway_month_hr: Optional[int] = None
    hours_underway_month_min: Optional[int] = None
    distance_run_month: Optional[float] = None
    distance_run_since_commissioning: Optional[float] = None
    max_speed: Optional[float] = None
    eo_name: Optional[str] = None


class SrarEquipmentExploitationCreate(BaseModel):
    sfd_details_id: int
    hrs_for_month: Optional[int] = None
    hrs_for_month_min: Optional[int] = None
    hrs_for_month_hrs: Optional[int] = None
    rhsi_till_current_month: Optional[int] = None


class SrarEquipmentExploitationResponse(BaseModel):
    id: int
    sfd_details_id: Optional[int] = None
    hrs_for_month: Optional[int] = None
    rhsi_till_prev_month: Optional[int] = None
    rhsi_till_current_month: Optional[int] = None

    model_config = {"from_attributes": True}


class SRARDetailResponse(BaseModel):
    id: int
    ship_id: Optional[int] = None
    srar_month: int
    srar_year: int
    distance_run_month: Optional[float] = None
    max_speed: Optional[float] = None
    eo_name: Optional[str] = None
    equipment_exploitations: List[SrarEquipmentExploitationResponse] = []

    model_config = {"from_attributes": True}


class SRARBulkCreate(BaseModel):
    header: SRARMonthlyHeaderCreate
    exploitations: List[SrarEquipmentExploitationCreate] = []


# ─────────────────────────────────────────────────────────────
# COMPLETED ROUTINES
# ─────────────────────────────────────────────────────────────


class CompletedRoutineCreate(BaseModel):
    routine_id: int
    old_dart_number: Optional[str] = ""
    new_dart_number: Optional[str] = ""
    date_of_completion: Optional[date] = None
    hours: Optional[int] = None
    minutes: Optional[int] = None
    carried_by: Optional[str] = None
    p_no: Optional[str] = None
    running_hour: Optional[str] = None
    due_running_hour: Optional[str] = None
    completion_details: Optional[str] = None


class CompletedRoutineResponse(BaseModel):
    id: int
    routine_id: Optional[int] = None
    old_dart_number: Optional[str] = None
    new_dart_number: Optional[str] = None
    date_of_completion: Optional[date] = None
    hours: Optional[int] = None
    minutes: Optional[int] = None
    carried_by: Optional[str] = None
    running_hour: Optional[str] = None
    completion_details: Optional[str] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────
# FUSS
# ─────────────────────────────────────────────────────────────


class FussRaiseRequest(BaseModel):
    routine_description_id: int
    fuss_date: Optional[date] = None
    last_undertaken: Optional[date] = None
    due_date: Optional[date] = None
    schedule_date: Optional[date] = None
    equipment: Optional[str] = None
    location_on_board: Optional[str] = None
    maintop_no: Optional[str] = ""
    frequency: Optional[str] = ""


class FussRaiseDetailResponse(BaseModel):
    id: int
    isclosed_fuss: bool = False
    serial_no: Optional[str] = None
    routine_description_id: Optional[int] = None
    fuss_date: Optional[date] = None
    last_undertaken: Optional[date] = None
    due_date: Optional[date] = None
    schedule_date: Optional[date] = None
    equipment: Optional[str] = None
    location_on_board: Optional[str] = None
    maintop_no: Optional[str] = None
    frequency: Optional[str] = None

    model_config = {"from_attributes": True}


class MDefermentResponse(BaseModel):
    id: int = Field(alias="DefermentID")
    code: Optional[str] = Field(None, alias="DefermentCode")
    description: Optional[str] = Field(None, alias="Description")
    active: Optional[bool] = Field(None, alias="Active")
    universal_id: Optional[str] = Field(None, alias="Universal_ID_M_Deferment")

    model_config = {"from_attributes": True, "populate_by_name": True}


class MReasonResponse(BaseModel):
    id: int = Field(alias="ReasonID")
    code: Optional[str] = Field(None, alias="ReasonCode")
    description: Optional[str] = Field(None, alias="Description")
    active: Optional[bool] = Field(None, alias="Active")
    universal_id: Optional[str] = Field(None, alias="Universal_ID_M_Reason")

    model_config = {"from_attributes": True, "populate_by_name": True}


class MInabilityResponse(BaseModel):
    id: int = Field(alias="InabilityID")
    code: Optional[str] = Field(None, alias="InabilityCode")
    description: Optional[str] = Field(None, alias="Description")
    active: Optional[bool] = Field(None, alias="Active")
    universal_id: Optional[str] = Field(None, alias="Universal_ID_M_Inability")

    model_config = {"from_attributes": True, "populate_by_name": True}


class FussSyncPayloadResponse(BaseModel):
    T_fuss: List[FussRaiseDetailResponse] = []
    M_Deferment: List[MDefermentResponse] = []
    M_Reason: List[MReasonResponse] = []
    M_Inability: List[MInabilityResponse] = []


class FussMastersResponse(BaseModel):
    M_deferment: List[MDefermentResponse] = []
    M_reason: List[MReasonResponse] = []
    M_inability: List[MInabilityResponse] = []


# ─────────────────────────────────────────────────────────────
# ABER
# ─────────────────────────────────────────────────────────────


class AberEquipmentResponse(BaseModel):
    id: int
    nomenclature: str
    equipment_code: str
    installation_date: Optional[date] = None
    age_years: float
    universal_id_m_ship: Optional[str] = None

    model_config = {"from_attributes": True}


class AberSubmitRequest(BaseModel):
    ship_id: int
    fitted_equipment_id: int
    budget_year: int
    estimate_cost: float
    currency: str = "INR"
    aber_authority: str
    repair_agency_id: int
    remarks: Optional[str] = None


class AberSubmitResponse(BaseModel):
    ABERID: int
    Universal_ID_T_ABER: Optional[str] = Field(None, alias="Universal_ID_T_ABER")
    Universal_ID_M_Ship: Optional[str] = Field(None, alias="Universal_ID_M_Ship")
    BudgetYear: Optional[int] = Field(None, alias="BudgetYear")
    EstimateCost: Optional[float] = Field(None, alias="EstimateCost")
    Currency: Optional[str] = Field(None, alias="Currency")
    ABERAuthority: Optional[str] = Field(None, alias="ABERAuthority")
    RepairAgencyID: Optional[int] = Field(None, alias="RepairAgencyID")
    Remarks: Optional[str] = Field(None, alias="Remarks")

    model_config = {"from_attributes": True, "populate_by_name": True}


# ─────────────────────────────────────────────────────────────
# SFD
# ─────────────────────────────────────────────────────────────


class ShipEquipmentResponse(BaseModel):
    id: int
    nomenclature: Optional[str] = None
    equipment_sr_no: Optional[str] = None
    location_on_board: Optional[str] = None
    installation_date: Optional[date] = None

    model_config = {"from_attributes": True}


class SfdShipResponse(BaseModel):
    id: int
    name: Optional[str] = None
    code: Optional[str] = None
    universal_id_m_ship: Optional[str] = None
    command_name: Optional[str] = None
    authority_name: Optional[str] = None

    model_config = {"from_attributes": True}


class SfdSyncPayloadResponse(BaseModel):
    T_genericspecification: List[dict] = []
    M_group: List[dict] = []
    M_Section: List[dict] = []
    M_Equipment: List[dict] = []
    M_ship: List[dict] = []
    M_generic: List[dict] = []
    M_command: List[dict] = []
    T_EquipmentShipDetail: List[dict] = []
    M_propulsion: List[dict] = []
    M_country: List[dict] = []


# ─────────────────────────────────────────────────────────────
# REFIT
# ─────────────────────────────────────────────────────────────


class RefitCompletionCreate(BaseModel):
    ship_code: str
    refit_type: str
    planned_start_date: date
    planned_end_date: date
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    refit_place: Optional[str] = None
    universal_id_m_command: Optional[str] = None


class RefitCompletionResponse(BaseModel):
    id: int
    Universal_ID_T_RefComp: Optional[str] = None

    model_config = {"from_attributes": True}


class RefitDelinquencyCreate(BaseModel):
    delinquency_code: str
    description: str
    days_delayed: int
    remarks: Optional[str] = None


class RefitDryDockingCreate(BaseModel):
    dock_entry_date: date
    dock_undock_date: date
    yard_dock_name: str
    hull_inspection_status: Optional[str] = None


class RefitOCRCreate(BaseModel):
    report_ref_no: str
    clearance_status: str
    trial_outcome: Optional[str] = None
    report_date: date


class RefitSyncPayloadResponse(BaseModel):
    M_Delinquery: List[dict] = []
    T_RefComDelinquery_Detail: List[dict] = []
    M_Refit: List[dict] = []
    T_DryDocking: List[dict] = []
    M_OCR: List[dict] = []
    T_Refcomp: List[dict] = []


# ─────────────────────────────────────────────────────────────
# OPDEF
# ─────────────────────────────────────────────────────────────


class OpdefInitiateRequest(BaseModel):
    ship_id: int
    fitted_equipment_id: int
    opdef_number: str
    opdef_date: date
    operational_impact: str
    department_id: int
    defect_description: str


class OpdefInitiateResponse(BaseModel):
    OpdefMainID: int
    Universal_ID_T_OpdefMain: Optional[str] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class OpdefAnalysisRequest(BaseModel):
    analysis_date: date
    failure_cause: str
    rectification_method_proposed: str
    analysed_by: str


class OpdefSpareRequest(BaseModel):
    spare_item_code: str
    nomenclature: str
    quantity_consumed: int
    unit_cost: float
    remarks: Optional[str] = None


class OpdefTrialRequest(BaseModel):
    trial_date: date
    rpm_reading: int
    temperature_celsius: float
    vibration_velocity_mms: float
    status: str


class OpdefPriorParamRequest(BaseModel):
    reading_time: datetime
    rpm_reading: int
    temperature_celsius: float
    vibration_velocity_mms: float
    remarks: Optional[str] = None


class OpdefPhotoResponse(BaseModel):
    success: bool
    file_path: str
    message: str


class OpdefSyncPayloadResponse(BaseModel):
    T_OpdefMain: List[dict] = []
    T_opdefgeneratinfo: List[dict] = []
    T_DefectAnalysis: List[dict] = []
    T_MajorSpareconsumer: List[dict] = []
    T_trailconductedParameter: List[dict] = []
    T_opdefpriorparameter: List[dict] = []
    T_photograph: List[dict] = []


# ─────────────────────────────────────────────────────────────
# MAINTOP
# ─────────────────────────────────────────────────────────────


class MaintopHeaderSyncItem(BaseModel):
    MaintopID: int
    MaintopNo: Optional[str] = None
    MaintopTitle: Optional[str] = None
    AmendmentNo: Optional[int] = None
    Active: Optional[int] = None
    Universal_ID_T_MaintopHeader: str


class MaintopDetailSyncItem(BaseModel):
    RoutineID: int
    MaintopID: Optional[int] = None
    MaintopNo: Optional[str] = None
    RoutineNo: Optional[str] = None
    RoutineDescription: Optional[str] = None
    Frequency: Optional[str] = None
    Active: Optional[int] = None
    Universal_ID_T_MaintopHeader: Optional[str] = None
    Universal_ID_T_MaintopDetail: str


class MaintopSyncRequest(BaseModel):
    T_maintopheader: List[MaintopHeaderSyncItem]
    T_maintopdetail: List[MaintopDetailSyncItem]


class MaintopSyncResponse(BaseModel):
    status: bool
    headers_processed: int
    details_processed: int


class MaintopJICSyncItem(BaseModel):
    JICID: int
    Universal_ID_T_MaintopJIC: str
    Universal_ID_T_MaintopDetail: str
    JobSteps: Optional[str] = None


class JICSparesSyncItem(BaseModel):
    JICID: Optional[int] = None
    SpareItemCode: Optional[str] = None
    Quantity: Optional[int] = None
    Universal_ID_T_JICspares: str


class JICToolsSyncItem(BaseModel):
    JICID: Optional[int] = None
    ToolCode: Optional[str] = None
    ToolName: Optional[str] = None
    Universal_ID_T_JICtools: str


class JICAttachmentsSyncItem(BaseModel):
    JICID: Optional[int] = None
    FileName: Optional[str] = None
    FileUrl: Optional[str] = None
    Universal_ID_T_JICattachments: str


class MaintopJICRequest(BaseModel):
    T_maintopJIC: List[MaintopJICSyncItem]
    T_JICspares: List[JICSparesSyncItem]
    T_JICtools: List[JICToolsSyncItem]
    T_JICattachments: List[JICAttachmentsSyncItem]


class MaintopJICResponse(BaseModel):
    status: bool
    jics_processed: int
    spares_processed: int
    tools_processed: int
    attachments_processed: int


class AddressSyncItem(BaseModel):
    AddressID: int
    AddressName: Optional[str] = None
    Universal_ID_M_Address: str


class DistAddressSyncItem(BaseModel):
    DistAddressID: int
    AddressID: Optional[int] = None
    DistName: Optional[str] = None
    Universal_ID_M_DistributionAddress: str


class MaintopListDistSyncItem(BaseModel):
    MaintopID: Optional[int] = None
    DistAddressID: Optional[int] = None
    Active: Optional[int] = None
    Universal_ID_T_MaintopListDist: str


class MaintopLibraryDisDefSyncItem(BaseModel):
    LibraryID: Optional[int] = None
    DefaultAddressID: Optional[int] = None
    IsDefaultActive: Optional[int] = None
    Universal_ID_T_MaintopLibraryDisDef: str


class MaintopDistributionRequest(BaseModel):
    M_address: List[AddressSyncItem]
    M_distribution_address: List[DistAddressSyncItem]
    T_maintoplistdist: List[MaintopListDistSyncItem]
    T_MaintoplibraryDisDef: List[MaintopLibraryDisDefSyncItem]


class MaintopDistributionResponse(BaseModel):
    status: bool
    addresses_processed: int
    distributions_processed: int
    defaults_processed: int
