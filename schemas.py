from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import date, datetime

# ==========================================
# COMMON SCHEMAS
# ==========================================
class GenericSuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class CmmsDartPayloadResponse(BaseModel):
    M_Diagnostic: List[dict]
    M_Refit: List[dict]
    M_Ship: List[dict]
    M_group: List[dict] = Field(alias="M_group")
    M_department: List[dict]
    M_repair_agency: List[dict] = Field(alias="M_repair agency")
    M_Delay: List[dict]
    M_Repair: List[dict]
    M_section: List[dict]
    T_DART: List[dict]

    class Config:
        populate_by_name = True


# ==========================================
# CMMS SCHEMAS
# ==========================================
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
    maintenance_period: Optional[str] = None # e.g. "OPERATIONAL" or "REFIT"
    dart_occasion: Optional[str] = None
    is_guarantee_defect: Optional[bool] = False

class DefectResponse(BaseModel):
    id: int
    dart_number: Optional[str]
    dart_sr_number: Optional[str]
    dart_date: Optional[date]
    rectification_date: Optional[date]
    is_closed: bool
    defective_discriptions: Optional[str]
    defective_component: Optional[str]
    maintenance_period: Optional[str]
    is_guarantee_defect: bool
    created_date: Optional[date]

    class Config:
        from_attributes = True

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
    routine_id: int
    old_dart_number: Optional[str]
    new_dart_number: Optional[str]
    date_of_completion: Optional[date]
    hours: Optional[int]
    minutes: Optional[int]
    carried_by: Optional[str]
    running_hour: Optional[str]
    completion_details: Optional[str]

    class Config:
        from_attributes = True

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
    sfd_details_id: int
    hrs_for_month: Optional[int]
    rhsi_till_prev_month: Optional[int]
    rhsi_till_current_month: Optional[int]

    class Config:
        from_attributes = True

class SRARDetailResponse(BaseModel):
    id: int
    ship_id: Optional[int]
    srar_month: int
    srar_year: int
    distance_run_month: Optional[float]
    max_speed: Optional[float]
    eo_name: Optional[str]
    equipment_exploitations: List[SrarEquipmentExploitationResponse] = []

    class Config:
        from_attributes = True

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

class FussRaiseResponse(BaseModel):
    id: int
    isclosed_fuss: bool
    serial_no: Optional[str]
    fuss_date: Optional[date]
    due_date: Optional[date]
    equipment: Optional[str]

    class Config:
        from_attributes = True

class AberEquipmentResponse(BaseModel):
    id: int
    nomenclature: str
    equipment_code: str
    installation_date: Optional[date]
    age_years: float
    universal_id_m_ship: Optional[str] = Field(None, alias="universal_id_m_ship")

    class Config:
        from_attributes = True
        populate_by_name = True

class ShipEquipmentResponse(BaseModel):
    id: int
    nomenclature: Optional[str]
    equipment_sr_no: Optional[str]
    location_on_board: Optional[str]
    installation_date: Optional[date]

    class Config:
        from_attributes = True

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
    Universal_ID_T_ABER: str = Field(alias="Universal_ID_T_ABER")
    Universal_ID_M_Ship: Optional[str] = Field(None, alias="Universal_ID_M_Ship")
    Universal_ID_T_EquipmentShipDetail: Optional[str] = Field(None, alias="Universal_ID_T_EquipmentShipDetail")
    BudgetYear: Optional[int] = Field(None, alias="BudgetYear")
    EstimateCost: Optional[float] = Field(None, alias="EstimateCost")
    Currency: Optional[str] = Field(None, alias="Currency")
    ABERAuthority: Optional[str] = Field(None, alias="ABERAuthority")
    RepairAgencyID: Optional[int] = Field(None, alias="RepairAgencyID")
    Remarks: Optional[str] = Field(None, alias="Remarks")

    class Config:
        from_attributes = True
        populate_by_name = True


# ==========================================
# ILMS SCHEMAS
# ==========================================
class ILMSItemCreate(BaseModel):
    item_code: str
    item_desc: str
    item_deno: str
    crp_category: str
    ved_category: Optional[str] = ""
    abc_category: Optional[str] = ""
    section_head: Optional[str] = ""

class ILMSItemResponse(BaseModel):
    item_code: str
    item_desc: str
    item_deno: str
    crp_category: str
    ved_category: str
    abc_category: str

    class Config:
        from_attributes = True

class ILMSVendorCreate(BaseModel):
    vendor_code: str
    name: str
    vendor_class: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country_code: Optional[str] = None

class ILMSVendorResponse(BaseModel):
    vendor_code: str
    name: Optional[str]
    vendor_class: Optional[str]
    city: Optional[str]
    country_code: Optional[str]

    class Config:
        from_attributes = True

class ILMSDemandCreate(BaseModel):
    ilms_spare_id: str
    vendor_id: Optional[str] = None
    demand_number: str
    in_progress_status: Optional[str] = "INITIATED"
    is_demand: Optional[bool] = True

class ILMSDemandResponse(BaseModel):
    id: int
    ilms_spare_id: str
    vendor_id: Optional[str]
    demand_number: str
    in_progress_status: str
    is_demand: bool

    class Config:
        from_attributes = True

class ILMSPTSCreate(BaseModel):
    ilms_spare_id: str
    vendor_id: Optional[str] = None
    in_progress_status: Optional[str] = "INITIATED"
    is_pts: Optional[bool] = True

class ILMSPTSResponse(BaseModel):
    id: int
    ilms_spare_id: str
    vendor_id: Optional[str]
    in_progress_status: str
    is_pts: bool

    class Config:
        from_attributes = True

class ILMSSurveyCreate(BaseModel):
    ilms_spare_id: str
    vendor_id: Optional[str] = None
    demand_number: Optional[str] = ""
    in_progress_status: Optional[str] = "PENDING"
    is_survey: Optional[bool] = True

class ILMSSurveyResponse(BaseModel):
    id: int
    ilms_spare_id: str
    vendor_id: Optional[str]
    demand_number: str
    in_progress_status: str
    is_survey: bool

    class Config:
        from_attributes = True


class ILMSIIFCreate(BaseModel):
    spare_id_id: int
    is_sync: Optional[bool] = False
    sync_response: Optional[bool] = False
    is_delete: Optional[bool] = False

class ILMSIIFResponse(BaseModel):
    id: int
    spare_id_id: Optional[int]
    is_sync: bool
    sync_response: bool
    is_delete: bool

    class Config:
        from_attributes = True

class ILMSReceiveCreate(BaseModel):
    spare_id: int
    issue_entry_id: Optional[int] = None
    quantity_toreceive: int
    demand_entry_id: Optional[int] = None
    dart_number: Optional[str] = None

class ILMSReceiveResponse(BaseModel):
    id: int
    spare_id: int
    issue_entry_id: Optional[int]
    quantity_toreceive: int
    demand_entry_id: Optional[int]
    dart_number: Optional[str]

    class Config:
        from_attributes = True

class ILMSPostReceiveCreate(BaseModel):
    spare_id: int
    issue_entry_id: Optional[int] = None
    quantity_received: int
    receipt_number: str
    receive_date: Optional[datetime] = None
    nac_status: Optional[bool] = False
    remarks: Optional[str] = ""
    dart_number: Optional[str] = None
    created_by: Optional[str] = ""

class ILMSPostReceiveResponse(BaseModel):
    id: int
    spare_id: int
    issue_entry_id: Optional[int]
    quantity_received: int
    receipt_number: str
    receive_date: Optional[datetime]
    nac_status: bool
    remarks: Optional[str]
    dart_number: Optional[str]
    created_by: Optional[str]

    class Config:
        from_attributes = True



# ==========================================
# WLMS SCHEMAS
# ==========================================
class WLMSEquipmentCreate(BaseModel):
    eqpt_id: int
    eqpt_name: str
    remarks: Optional[str] = None
    is_active: Optional[bool] = True

class WLMSEquipmentResponse(BaseModel):
    id: int
    eqpt_id: Optional[int]
    eqpt_name: Optional[str]
    remarks: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

class WLMSSpareCreate(BaseModel):
    item_code: str
    item_desc: str
    category: Optional[str] = None
    eqpt_id: Optional[int] = None
    denom_id: Optional[str] = None
    latest_qty: Optional[int] = None
    is_active: Optional[bool] = True

class WLMSSpareResponse(BaseModel):
    id: int
    item_code: Optional[str]
    item_desc: Optional[str]
    category: Optional[str]
    eqpt_id: Optional[int]
    latest_qty: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True

class WLMSDemandCreate(BaseModel):
    wed_spares_id: int
    demand_no: str
    demand_qty: str
    remarks: Optional[str] = None
    is_demand: Optional[bool] = True

class WLMSDemandResponse(BaseModel):
    id: int
    wed_spares_id: Optional[int]
    demand_no: str
    demand_qty: str
    is_demand: bool
    remarks: Optional[str]

    class Config:
        from_attributes = True

class WLMSPTSCreate(BaseModel):
    wed_spares_id: int
    PTS_demand_no: str
    demand_qty: str
    remarks: Optional[str] = None
    is_pts: Optional[bool] = True

class WLMSPTSResponse(BaseModel):
    id: int
    wed_spares_id: Optional[int]
    PTS_demand_no: str
    demand_qty: str
    is_pts: bool

    class Config:
        from_attributes = True

class WLMSSurveyCreate(BaseModel):
    wed_spares_id: int
    spare_cart_name: Optional[str] = ""
    wlms_status: Optional[str] = "PENDING"
    is_survey: Optional[bool] = True

class WLMSSurveyResponse(BaseModel):
    id: int
    wed_spares_id: Optional[int]
    spare_cart_name: str
    wlms_status: str
    is_survey: bool

    class Config:
        from_attributes = True


class WLMSIIFCreate(BaseModel):
    spare_id_id: int
    is_sync: Optional[bool] = False
    sync_response: Optional[bool] = False
    is_delete: Optional[bool] = False

class WLMSIIFResponse(BaseModel):
    id: int
    spare_id_id: Optional[int]
    is_sync: bool
    sync_response: bool
    is_delete: bool

    class Config:
        from_attributes = True

class WLMSReceiveCreate(BaseModel):
    demand_details_id: int
    demand_number: Optional[str] = None
    demand_date: Optional[date] = None
    demand_quantity: Optional[int] = 0
    demand_status: Optional[str] = None
    swmm_demandno: Optional[str] = None
    dart_no: Optional[str] = None
    gate_pass_no: Optional[str] = None
    gate_pass_date: Optional[datetime] = None

class WLMSReceiveResponse(BaseModel):
    id: int
    demand_details_id: Optional[int]
    demand_number: Optional[str]
    demand_date: Optional[date]
    demand_quantity: int
    demand_status: Optional[str]
    swmm_demandno: Optional[str]
    dart_no: Optional[str]
    gate_pass_no: Optional[str]
    gate_pass_date: Optional[datetime]

    class Config:
        from_attributes = True



# ==========================================
# ITTTM SCHEMAS
# ==========================================
class VibtrialXCreate(BaseModel):
    trial_id: int
    vib_X_Ship: Optional[str] = "TEST"
    vib_X_Equipment: Optional[str] = "TEST EQUIP"
    vib_X_Date: Optional[date] = None
    vib_X_CMMS: Optional[str] = None
    observation: Optional[str] = ""
    # nested dsc/performance parameters
    dsc_checks: Optional[dict] = None
    performance_checks: Optional[dict] = None

class VibtrialXResponse(BaseModel):
    id: int
    trial_id: Optional[int]
    vib_X_Ship: Optional[str]
    vib_X_Equipment: Optional[str]
    vib_X_Date: Optional[date]
    observation: Optional[str]

    class Config:
        from_attributes = True

class PrerangingCreate(BaseModel):
    Prerange_Gen_Date: Optional[date] = None
    Prerange_ShipName: Optional[str] = None
    Prerange_Occassion: Optional[str] = None

class PrerangingResponse(BaseModel):
    id: int
    Prerange_ShipName: Optional[str]
    Prerange_Occassion: Optional[str]
    Prerange_Gen_Date: Optional[date]

    class Config:
        from_attributes = True

class BlowingArcCreate(BaseModel):
    ship_id: int
    trial_date: date
    remarks: Optional[str] = None

class BlowingArcResponse(BaseModel):
    id: int
    ship_id: int
    trial_date: date
    remarks: Optional[str]

    class Config:
        from_attributes = True

class TrialSubmissionCreate(BaseModel):
    trial_id: int
    submission_date: date
    status: int
    comments: Optional[str] = None

class TrialSubmissionResponse(BaseModel):
    id: int
    trial_id: int
    submission_date: date
    status: int
    comments: Optional[str]

    class Config:
        from_attributes = True

class TrialApprovalRequest(BaseModel):
    trial_id: int
    approved_role_id: int
    comments: Optional[str] = ""
    status: int
    approved_level: int


# ==========================================
# REFIT SCHEMAS
# ==========================================
class RefitSyncPayloadResponse(BaseModel):
    M_Delinquery: List[dict]
    T_RefComDelinquery_Detail: List[dict] = Field(alias="T_RefComDelinquery Detail")
    M_Refit: List[dict]
    T_DryDocking: List[dict]
    M_OCR: List[dict] = Field(alias="M-OCR")
    T_Refcomp: List[dict]

    class Config:
        populate_by_name = True


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
    universal_id_t_refcomp: Optional[str] = Field(alias="Universal_ID_T_RefComp")

    class Config:
        from_attributes = True
        populate_by_name = True


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


# ==========================================
# OPDEF SCHEMAS
# ==========================================
class OpdefMainResponse(BaseModel):
    OpdefMainID: int
    Universal_ID_M_Ship: Optional[str] = Field(None, alias="Universal_ID_M_Ship")
    Universal_ID_T_EquipmentShipDetail: Optional[str] = Field(None, alias="Universal_ID_T_EquipmentShipDetail")
    OpdefNumber: Optional[str] = Field(None, alias="OpdefNumber")
    OpdefDate: Optional[date] = Field(None, alias="OpdefDate")
    DepartmentID: Optional[int] = Field(None, alias="DepartmentID")
    DefectDescription: Optional[str] = Field(None, alias="DefectDescription")
    Universal_ID_T_OpdefMain: Optional[str] = Field(None, alias="Universal_ID_T_OpdefMain")

    class Config:
        from_attributes = True
        populate_by_name = True

class OpdefGeneratInfoResponse(BaseModel):
    OpdefGeneratInfoID: int
    Universal_ID_T_OpdefMain: Optional[str] = Field(None, alias="Universal_ID_T_OpdefMain")
    OperationalImpact: Optional[str] = Field(None, alias="OperationalImpact")
    Universal_ID_T_OpdefGeneratInfo: Optional[str] = Field(None, alias="Universal_ID_T_OpdefGeneratInfo")

    class Config:
        from_attributes = True
        populate_by_name = True

class DefectAnalysisResponse(BaseModel):
    DefectAnalysisID: int
    Universal_ID_T_OpdefMain: Optional[str] = Field(None, alias="Universal_ID_T_OpdefMain")
    AnalysisDate: Optional[date] = Field(None, alias="AnalysisDate")
    FailureCause: Optional[str] = Field(None, alias="FailureCause")
    RectificationMethodProposed: Optional[str] = Field(None, alias="RectificationMethodProposed")
    AnalysedBy: Optional[str] = Field(None, alias="AnalysedBy")
    Universal_ID_T_DefectAnalysis: Optional[str] = Field(None, alias="Universal_ID_T_DefectAnalysis")

    class Config:
        from_attributes = True
        populate_by_name = True

class MajorSpareConsumerResponse(BaseModel):
    MajorSpareConsumerID: int
    Universal_ID_T_OpdefMain: Optional[str] = Field(None, alias="Universal_ID_T_OpdefMain")
    SpareItemCode: Optional[str] = Field(None, alias="SpareItemCode")
    Nomenclature: Optional[str] = Field(None, alias="Nomenclature")
    QuantityConsumed: Optional[int] = Field(None, alias="QuantityConsumed")
    UnitCost: Optional[float] = Field(None, alias="UnitCost")
    Remarks: Optional[str] = Field(None, alias="Remarks")
    Universal_ID_T_MajorSpareConsumer: Optional[str] = Field(None, alias="Universal_ID_T_MajorSpareConsumer")

    class Config:
        from_attributes = True
        populate_by_name = True

class TrialConductedParameterResponse(BaseModel):
    TrialConductedParameterID: int
    Universal_ID_T_OpdefMain: Optional[str] = Field(None, alias="Universal_ID_T_OpdefMain")
    TrialDate: Optional[date] = Field(None, alias="TrialDate")
    RPMReading: Optional[int] = Field(None, alias="RPMReading")
    TemperatureCelsius: Optional[float] = Field(None, alias="TemperatureCelsius")
    VibrationVelocityMMS: Optional[float] = Field(None, alias="VibrationVelocityMMS")
    Status: Optional[str] = Field(None, alias="Status")
    Universal_ID_T_TrialConductedParameter: Optional[str] = Field(None, alias="Universal_ID_T_TrialConductedParameter")

    class Config:
        from_attributes = True
        populate_by_name = True

class OpdefPriorParameterResponse(BaseModel):
    OpdefPriorParameterID: int
    Universal_ID_T_OpdefMain: Optional[str] = Field(None, alias="Universal_ID_T_OpdefMain")
    ReadingTime: Optional[datetime] = Field(None, alias="ReadingTime")
    RPMReading: Optional[int] = Field(None, alias="RPMReading")
    TemperatureCelsius: Optional[float] = Field(None, alias="TemperatureCelsius")
    VibrationVelocityMMS: Optional[float] = Field(None, alias="VibrationVelocityMMS")
    Remarks: Optional[str] = Field(None, alias="Remarks")
    Universal_ID_T_OpdefPriorParameter: Optional[str] = Field(None, alias="Universal_ID_T_OpdefPriorParameter")

    class Config:
        from_attributes = True
        populate_by_name = True

class PhotographResponse(BaseModel):
    PhotographID: int
    Universal_ID_T_OpdefMain: Optional[str] = Field(None, alias="Universal_ID_T_OpdefMain")
    FilePath: Optional[str] = Field(None, alias="FilePath")
    Description: Optional[str] = Field(None, alias="Description")
    UploadedDate: Optional[datetime] = Field(None, alias="UploadedDate")
    Universal_ID_T_Photograph: Optional[str] = Field(None, alias="Universal_ID_T_Photograph")

    class Config:
        from_attributes = True
        populate_by_name = True

class OpdefSyncPayloadResponse(BaseModel):
    T_OpdefMain: List[OpdefMainResponse]
    T_opdefgeneratinfo: List[OpdefGeneratInfoResponse]
    T_DefectAnalysis: List[DefectAnalysisResponse]
    T_MajorSpareconsumer: List[MajorSpareConsumerResponse]
    T_trailconductedParameter: List[TrialConductedParameterResponse]
    T_opdefpriorparameter: List[OpdefPriorParameterResponse]
    T_photograph: List[PhotographResponse]

    class Config:
        from_attributes = True
        populate_by_name = True


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
    Universal_ID_T_OpdefMain: str = Field(alias="Universal_ID_T_OpdefMain")

    class Config:
        from_attributes = True
        populate_by_name = True


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


# ==========================================
# FUSS SCHEMAS
# ==========================================
class FussRaiseDetailResponse(BaseModel):
    id: int
    isclosed_fuss: bool
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

    class Config:
        from_attributes = True

class MDefermentResponse(BaseModel):
    id: int = Field(alias="DefermentID")
    code: Optional[str] = Field(alias="DefermentCode")
    description: Optional[str] = Field(alias="Description")
    active: Optional[bool] = Field(alias="Active")
    universal_id: Optional[str] = Field(alias="Universal_ID_M_Deferment")

    class Config:
        from_attributes = True
        populate_by_name = True

class MReasonResponse(BaseModel):
    id: int = Field(alias="ReasonID")
    code: Optional[str] = Field(alias="ReasonCode")
    description: Optional[str] = Field(alias="Description")
    active: Optional[bool] = Field(alias="Active")
    universal_id: Optional[str] = Field(alias="Universal_ID_M_Reason")

    class Config:
        from_attributes = True
        populate_by_name = True

class MInabilityResponse(BaseModel):
    id: int = Field(alias="InabilityID")
    code: Optional[str] = Field(alias="InabilityCode")
    description: Optional[str] = Field(alias="Description")
    active: Optional[bool] = Field(alias="Active")
    universal_id: Optional[str] = Field(alias="Universal_ID_M_Inability")

    class Config:
        from_attributes = True
        populate_by_name = True

class FussSyncPayloadResponse(BaseModel):
    T_fuss: List[FussRaiseDetailResponse]
    M_Deferment: List[MDefermentResponse]
    M_Reason: List[MReasonResponse]
    M_Inability: List[MInabilityResponse]

    class Config:
        from_attributes = True
        populate_by_name = True

class FussMastersResponse(BaseModel):
    M_deferment: List[MDefermentResponse] = Field(alias="M_deferment")
    M_reason: List[MReasonResponse] = Field(alias="M_reason")
    M_inability: List[MInabilityResponse] = Field(alias="M_inability")

    class Config:
        from_attributes = True
        populate_by_name = True


# ==========================================
# SFD SCHEMAS
# ==========================================
class SfdSyncPayloadResponse(BaseModel):
    T_genericspecification: List[dict]
    M_group: List[dict]
    M_Section: List[dict]
    M_Equipment: List[dict]
    M_ship: List[dict]
    M_generic: List[dict]
    M_command: List[dict]
    M_Ops_Authority: List[dict] = Field(alias="M_Ops Authority")
    T_Equipment_Specification: List[dict] = Field(alias="T_Equipment Specification")
    T_EquipmentShipDetail: List[dict]
    M_Ship_Hierarchy: List[dict] = Field(alias="M_Ship Hierarchy")
    T_HTD_EquipmentDetail: List[dict] = Field(alias="T_HTD EquipmentDetail")
    T_EquipmentCommonspecdiffer: List[dict]
    M_propulsion: List[dict]
    T_equipment_policy: List[dict] = Field(alias="T_equipment policy")
    M_country: List[dict]
    M_ship_class: List[dict] = Field(alias="M_ship class")
    T_equipment_Supplier: List[dict] = Field(alias="T_equipment Supplier")
    M_Supplier: List[dict]

    class Config:
        populate_by_name = True


class SfdShipResponse(BaseModel):
    id: int
    name: Optional[str] = None
    code: Optional[str] = None
    universal_id_m_ship: Optional[str] = Field(None, alias="Universal_ID_M_Ship")
    class_code: Optional[str] = None
    command_name: Optional[str] = None
    authority_name: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


# ==========================================
# MAINTOP SCHEMAS
# ==========================================

class MaintopHeaderSyncItem(BaseModel):
    MaintopID: int
    MaintopNo: Optional[str] = None
    MaintopTitle: Optional[str] = None
    OriginalDate: Optional[str] = None
    AmendmentNo: Optional[int] = None
    Active: Optional[int] = None
    Universal_ID_T_MaintopHeader: str

    class Config:
        populate_by_name = True


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

    class Config:
        populate_by_name = True


class MaintopSyncRequest(BaseModel):
    T_maintopheader: List[MaintopHeaderSyncItem]
    T_maintopdetail: List[MaintopDetailSyncItem]

    class Config:
        populate_by_name = True


class MaintopSyncResponse(BaseModel):
    status: bool
    headers_processed: int
    details_processed: int


class MaintopJICSyncItem(BaseModel):
    JICID: int
    Universal_ID_T_MaintopJIC: str
    Universal_ID_T_MaintopDetail: str
    JobSteps: Optional[str] = None

    class Config:
        populate_by_name = True


class JICSparesSyncItem(BaseModel):
    JICID: Optional[int] = None
    SpareItemCode: Optional[str] = None
    Quantity: Optional[int] = None
    Universal_ID_T_JICspares: str

    class Config:
        populate_by_name = True


class JICToolsSyncItem(BaseModel):
    JICID: Optional[int] = None
    ToolCode: Optional[str] = None
    ToolName: Optional[str] = None
    Universal_ID_T_JICtools: str

    class Config:
        populate_by_name = True


class JICAttachmentsSyncItem(BaseModel):
    JICID: Optional[int] = None
    FileName: Optional[str] = None
    FileUrl: Optional[str] = None
    Universal_ID_T_JICattachments: str

    class Config:
        populate_by_name = True


class MaintopJICRequest(BaseModel):
    T_maintopJIC: List[MaintopJICSyncItem]
    T_JICspares: List[JICSparesSyncItem]
    T_JICtools: List[JICToolsSyncItem]
    T_JICattachments: List[JICAttachmentsSyncItem]

    class Config:
        populate_by_name = True


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

    class Config:
        populate_by_name = True


class DistAddressSyncItem(BaseModel):
    DistAddressID: int
    AddressID: Optional[int] = None
    DistName: Optional[str] = None
    Universal_ID_M_DistributionAddress: str

    class Config:
        populate_by_name = True


class MaintopListDistSyncItem(BaseModel):
    MaintopID: Optional[int] = None
    DistAddressID: Optional[int] = None
    Active: Optional[int] = None
    Universal_ID_T_MaintopListDist: str

    class Config:
        populate_by_name = True


class MaintopLibraryDisDefSyncItem(BaseModel):
    LibraryID: Optional[int] = None
    DefaultAddressID: Optional[int] = None
    IsDefaultActive: Optional[int] = None
    Universal_ID_T_MaintopLibraryDisDef: str

    class Config:
        populate_by_name = True


class MaintopDistributionRequest(BaseModel):
    M_address: List[AddressSyncItem]
    M_distribution_address: List[DistAddressSyncItem]
    T_maintoplistdist: List[MaintopListDistSyncItem]
    T_MaintoplibraryDisDef: List[MaintopLibraryDisDefSyncItem]

    class Config:
        populate_by_name = True


class MaintopDistributionResponse(BaseModel):
    status: bool
    addresses_processed: int
    distributions_processed: int
    defaults_processed: int





