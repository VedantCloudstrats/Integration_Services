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


from rest_framework import serializers
from sfd.models import ChangeEquipmentRequest, SFDTransaction


class CMMS_T_EquipmentShipDetailSerializer(serializers.ModelSerializer):
    EquipmentShipID = serializers.IntegerField(
        source="equipment_ship_id", read_only=True
    )
    EquipmentID = serializers.IntegerField(
        source="equipment_id", required=False, allow_null=True
    )
    ShipID = serializers.IntegerField(source="ship_id", required=False, allow_null=True)
    LocationCode = serializers.IntegerField(
        source="location_code", required=False, allow_null=True
    )
    LocationOnBoard = serializers.CharField(
        source="location_on_board", required=False, allow_null=True, allow_blank=True
    )
    NoOfFits = serializers.IntegerField(
        source="no_of_fits", required=False, allow_null=True
    )
    EquipmentSrNo = serializers.CharField(
        source="equipment_sr_no", required=False, allow_null=True, allow_blank=True
    )
    OEMPartNo = serializers.CharField(
        source="oem_part_no", required=False, allow_null=True, allow_blank=True
    )
    InstallationDate = serializers.DateTimeField(
        source="installation_date", required=False, allow_null=True
    )
    RemovalDate = serializers.DateTimeField(
        source="removal_date", required=False, allow_null=True
    )
    SupplierID = serializers.IntegerField(
        source="supplier_id", required=False, allow_null=True
    )
    ManufacturerID = serializers.IntegerField(
        source="manufacturer_id", required=False, allow_null=True
    )
    Remark = serializers.CharField(
        source="remark", required=False, allow_null=True, allow_blank=True
    )
    SRARApplicable = serializers.BooleanField(source="srar_applicable", required=False)
    MaintopID = serializers.IntegerField(
        source="maintop_id", required=False, allow_null=True
    )
    ParentEquipment = serializers.IntegerField(
        source="parent_equipment", required=False, allow_null=True
    )
    Active = serializers.BooleanField(source="active", required=False, allow_null=True)
    Nomenclature = serializers.CharField(
        source="nomenclature", required=False, allow_null=True, allow_blank=True
    )
    ServiceLife = serializers.IntegerField(
        source="service_life", required=False, allow_null=True
    )
    Status = serializers.IntegerField(source="status", required=False, allow_null=True)
    Equipment_Type_ID = serializers.IntegerField(
        source="equipment_type_id", required=False, allow_null=True
    )
    Universal_ID_T_EquipmentShipDetail = serializers.CharField(
        source="universal_id_t_equipment_ship_detail",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_M_Ship = serializers.CharField(
        source="universal_id_m_ship", required=False, allow_null=True, allow_blank=True
    )
    Universal_ID_M_Equipment = serializers.CharField(
        source="universal_id_m_equipment",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_M_SrarType = serializers.CharField(
        source="universal_id_m_srar_type",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_M_Supplier_Supplier = serializers.CharField(
        source="universal_id_m_supplier",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_M_Supplier_Manufacturer = serializers.CharField(
        source="universal_id_m_manufacturer",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_M_Equipment_ParentEquipment = serializers.CharField(
        source="universal_id_m_equipment_parent",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_M_Department = serializers.CharField(
        source="universal_id_m_department",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_T_MaintopHeader = serializers.CharField(
        source="universal_id_t_maintop_header",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_Ch_Master_Equipment_Type = serializers.CharField(
        source="universal_id_ch_master_equipment_type",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Removal_Remark = serializers.CharField(
        source="removal_remark", required=False, allow_null=True, allow_blank=True
    )
    Authority_Of_Removal = serializers.CharField(
        source="authority_of_removal", required=False, allow_null=True, allow_blank=True
    )
    Authority_Of_Installation = serializers.CharField(
        source="authority_of_installation",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    RH_Of_New_Equipemnt_At_Time_Of_Installation = serializers.IntegerField(
        source="rh_at_installation", required=False, allow_null=True
    )
    Universal_ID_M_SubDepartment = serializers.CharField(
        source="universal_id_m_sub_department",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    INSMAREMARKS = serializers.CharField(
        source="insma_remarks", required=False, allow_null=True, allow_blank=True
    )
    IsSynced = serializers.IntegerField(
        source="is_synced", required=False, allow_null=True
    )

    class Meta:
        model = SFDTransaction
        fields = [
            "EquipmentShipID",
            "EquipmentID",
            "ShipID",
            "LocationCode",
            "LocationOnBoard",
            "NoOfFits",
            "EquipmentSrNo",
            "OEMPartNo",
            "InstallationDate",
            "RemovalDate",
            "SupplierID",
            "ManufacturerID",
            "Remark",
            "SRARApplicable",
            "MaintopID",
            "ParentEquipment",
            "Active",
            "Nomenclature",
            "ServiceLife",
            "Status",
            "Equipment_Type_ID",
            "Universal_ID_T_EquipmentShipDetail",
            "Universal_ID_M_Ship",
            "Universal_ID_M_Equipment",
            "Universal_ID_M_SrarType",
            "Universal_ID_M_Supplier_Supplier",
            "Universal_ID_M_Supplier_Manufacturer",
            "Universal_ID_M_Equipment_ParentEquipment",
            "Universal_ID_M_Department",
            "Universal_ID_T_MaintopHeader",
            "Universal_ID_Ch_Master_Equipment_Type",
            "Removal_Remark",
            "Authority_Of_Removal",
            "Authority_Of_Installation",
            "RH_Of_New_Equipemnt_At_Time_Of_Installation",
            "Universal_ID_M_SubDepartment",
            "INSMAREMARKS",
            "IsSynced",
        ]


class CMMS_T_EquipmentShipDetailIngestSerializer(CMMS_T_EquipmentShipDetailSerializer):
    class Meta(CMMS_T_EquipmentShipDetailSerializer.Meta):
        fields = [
            field
            for field in CMMS_T_EquipmentShipDetailSerializer.Meta.fields
            if field != "IsSynced"
        ]


class CMMS_T_ChangeEquipmentRequestSerializer(serializers.ModelSerializer):
    EquipmentShipId = serializers.IntegerField(
        source="equipment_ship_id_id", required=False, allow_null=True
    )
    Equipment = serializers.CharField(
        source="equipment", required=False, allow_null=True, allow_blank=True
    )
    Model = serializers.CharField(
        source="model", required=False, allow_null=True, allow_blank=True
    )
    Supplier = serializers.CharField(
        source="supplier", required=False, allow_null=True, allow_blank=True
    )
    Manufacture = serializers.CharField(
        source="manufacture", required=False, allow_null=True, allow_blank=True
    )
    Active = serializers.BooleanField(source="active", required=False)
    CreatedBy = serializers.IntegerField(
        source="created_by", required=False, allow_null=True
    )
    CreatedDate = serializers.DateTimeField(
        source="created_date", required=False, allow_null=True
    )
    Universal_ID_T_SFDChangeRequest = serializers.CharField(
        source="universal_id_t_sfd_change_request",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_T_EquipmentShipDetail = serializers.CharField(
        source="universal_id_t_equipment_ship_detail",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_A_User_Created_By = serializers.CharField(
        source="universal_id_a_user_created_by",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_A_User_Updated_By = serializers.CharField(
        source="universal_id_a_user_updated_by",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    UpdatedBy = serializers.IntegerField(
        source="updated_by", required=False, allow_null=True
    )
    UpdatedDate = serializers.DateTimeField(
        source="updated_date", required=False, allow_null=True
    )
    IsSynced = serializers.IntegerField(
        source="is_synced", required=False, allow_null=True
    )

    class Meta:
        model = ChangeEquipmentRequest
        fields = [
            "EquipmentShipId",
            "Equipment",
            "Model",
            "Supplier",
            "Manufacture",
            "Active",
            "CreatedBy",
            "CreatedDate",
            "Universal_ID_T_SFDChangeRequest",
            "Universal_ID_T_EquipmentShipDetail",
            "Universal_ID_A_User_Created_By",
            "Universal_ID_A_User_Updated_By",
            "UpdatedBy",
            "UpdatedDate",
            "IsSynced",
        ]


class CMMS_M_ShipSerializer(serializers.ModelSerializer):
    ShipID = serializers.IntegerField(source="ship_id", required=False, allow_null=True)
    ShipSrNo = serializers.DecimalField(
        source="ship_sr_no",
        max_digits=5,
        decimal_places=0,
        required=False,
        allow_null=True,
    )
    ShipCode = serializers.CharField(
        source="ship_code", required=False, allow_null=True, allow_blank=True
    )
    ShipName = serializers.CharField(
        source="ship_name", required=False, allow_null=True, allow_blank=True
    )
    CommissionDate = serializers.DateTimeField(
        source="commission_date", required=False, allow_null=True
    )
    DecommissionDate = serializers.DateTimeField(
        source="decommission_date", required=False, allow_null=True
    )
    Displacement = serializers.IntegerField(
        source="displacement", required=False, allow_null=True
    )
    DecommissionScheduledDate = serializers.DateTimeField(
        source="decommission_scheduled_date", required=False, allow_null=True
    )
    Active = serializers.BooleanField(source="active", required=False, allow_null=True)
    YardNo = serializers.CharField(
        source="yard_no", required=False, allow_null=True, allow_blank=True
    )
    LengthOverall = serializers.CharField(
        source="length_overall", required=False, allow_null=True, allow_blank=True
    )
    Universal_ID_M_Ship = serializers.CharField(
        source="universal_id_m_ship", required=True
    )
    Universal_ID_M_ShipCategory = serializers.CharField(
        source="universal_id_m_ship_category",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_M_ShipClass = serializers.CharField(
        source="universal_id_m_ship_class",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_M_Command = serializers.CharField(
        source="universal_id_m_command",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_M_OpsAuthority = serializers.CharField(
        source="universal_id_m_ops_authority",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_M_Propulsion = serializers.CharField(
        source="universal_id_m_propulsion",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Refit_Authority = serializers.CharField(
        source="refit_authority", required=False, allow_null=True, allow_blank=True
    )
    Address = serializers.CharField(
        source="address", required=False, allow_null=True, allow_blank=True
    )
    Universal_ID_M_Overseeing_Team = serializers.CharField(
        source="universal_id_m_overseeing_team",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    IsInGD = serializers.BooleanField(
        source="is_in_gd", required=False, allow_null=True
    )
    Universal_ID_M_ShipUnitCategory = serializers.CharField(
        source="universal_id_m_ship_unit_category",
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    class Meta:
        model = ShipMaster
        fields = [
            "ShipID",
            "ShipSrNo",
            "ShipCode",
            "ShipName",
            "CommissionDate",
            "DecommissionDate",
            "Displacement",
            "DecommissionScheduledDate",
            "Active",
            "YardNo",
            "LengthOverall",
            "Universal_ID_M_Ship",
            "Universal_ID_M_ShipCategory",
            "Universal_ID_M_ShipClass",
            "Universal_ID_M_Command",
            "Universal_ID_M_OpsAuthority",
            "Universal_ID_M_Propulsion",
            "Refit_Authority",
            "Address",
            "Universal_ID_M_Overseeing_Team",
            "IsInGD",
            "Universal_ID_M_ShipUnitCategory",
        ]


class CMMS_M_DepartmentSerializer(serializers.ModelSerializer):
    DepartmentID = serializers.IntegerField(
        source="pk", required=False, allow_null=True
    )
    Description = serializers.CharField(
        source="description", required=False, allow_null=True, allow_blank=True
    )
    DeptCode = serializers.CharField(
        source="dep_code", required=False, allow_null=True, allow_blank=True
    )
    Active = serializers.SerializerMethodField()
    Universal_ID_M_Department = serializers.CharField(
        source="universal_id_m_department", required=True
    )

    class Meta:
        model = DepartmentMaster
        fields = [
            "DepartmentID",
            "Description",
            "DeptCode",
            "Active",
            "Universal_ID_M_Department",
        ]

    def get_Active(self, obj):
        return True


class CMMS_M_EquipmentSerializer(serializers.ModelSerializer):
    EquipmentID = serializers.IntegerField(
        source="equipment_id", required=False, allow_null=True
    )
    EquipmentCode = serializers.CharField(
        source="equipment_code", required=False, allow_null=True, allow_blank=True
    )
    EquipmentName = serializers.CharField(
        source="equipment_name", required=False, allow_null=True, allow_blank=True
    )
    EquipmentModel = serializers.CharField(
        source="equipment_model", required=False, allow_null=True, allow_blank=True
    )
    Active = serializers.BooleanField(source="active", required=False)
    MaintopNumber = serializers.IntegerField(
        source="maintop_number", required=False, allow_null=True
    )
    ManufacturerName = serializers.CharField(
        source="manufacturer_name", required=False, allow_null=True, allow_blank=True
    )
    authority = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    Universal_ID_M_Equipment = serializers.CharField(
        source="universal_id_m_equipment", required=True
    )
    Universal_ID_M_Section = serializers.CharField(
        source="universal_id_m_section",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_M_Group = serializers.CharField(
        source="universal_id_m_group", required=False, allow_null=True, allow_blank=True
    )
    Universal_ID_T_MaintopHeader = serializers.CharField(
        source="universal_id_t_maintop_header",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Universal_ID_Ch_Master_Equipment_Type = serializers.CharField(
        source="universal_id_ch_master_equipment_type",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Equipment_Type_ID = serializers.IntegerField(
        source="equipment_type_id", required=False, allow_null=True
    )
    ILMSEquipmentCode = serializers.CharField(
        source="ilms_equipment_code", required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = EquipmentMaster
        fields = [
            "EquipmentID",
            "EquipmentCode",
            "EquipmentName",
            "EquipmentModel",
            "Active",
            "MaintopNumber",
            "ManufacturerName",
            "authority",
            "Universal_ID_M_Equipment",
            "Universal_ID_M_Section",
            "Universal_ID_M_Group",
            "Universal_ID_T_MaintopHeader",
            "Universal_ID_Ch_Master_Equipment_Type",
            "Equipment_Type_ID",
            "ILMSEquipmentCode",
        ]


class CMMS_M_SupplierSerializer(serializers.ModelSerializer):
    SupplierID = serializers.IntegerField(
        source="supplier_id", required=False, allow_null=True
    )
    SupplierCode = serializers.CharField(
        source="supplier_code", required=False, allow_null=True, allow_blank=True
    )
    SupplierName = serializers.CharField(
        source="supplier_name", required=False, allow_null=True, allow_blank=True
    )
    CountryCode = serializers.CharField(
        source="country_code", required=False, allow_null=True, allow_blank=True
    )
    Address = serializers.CharField(
        source="address", required=False, allow_null=True, allow_blank=True
    )
    SupplierManufacturer = serializers.IntegerField(
        source="supplier_manufacture", required=False, allow_null=True
    )
    Active = serializers.BooleanField(source="active", required=False)
    Universal_ID_M_Supplier = serializers.CharField(
        source="universal_id_M_supplier", required=True
    )
    Universal_ID_M_Country = serializers.CharField(
        source="universal_id_M_country",
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    class Meta:
        model = SupplierMaster
        fields = [
            "SupplierID",
            "SupplierCode",
            "SupplierName",
            "CountryCode",
            "Address",
            "SupplierManufacturer",
            "Active",
            "Universal_ID_M_Supplier",
            "Universal_ID_M_Country",
        ]


class CMMS_M_SubDepartmentSerializer(serializers.ModelSerializer):
    SubDepartmentID = serializers.IntegerField(
        source="pk", required=False, allow_null=True
    )
    Description = serializers.CharField(
        source="description", required=False, allow_null=True, allow_blank=True
    )
    SubDeptCode = serializers.CharField(
        source="sub_department_code", required=False, allow_null=True, allow_blank=True
    )
    Active = serializers.BooleanField(source="active", required=False)
    Universal_ID_M_Department = serializers.CharField(
        source="universal_id_m_department", required=True
    )
    Universal_ID_M_SubDepartment = serializers.CharField(
        source="universal_id_m_sub_department", required=True
    )
    Universal_ID_M_ShipClass = serializers.CharField(
        source="universal_id_m_ship_class",
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    class Meta:
        model = SubDepartmentMaster
        fields = [
            "SubDepartmentID",
            "Description",
            "SubDeptCode",
            "Active",
            "Universal_ID_M_Department",
            "Universal_ID_M_SubDepartment",
            "Universal_ID_M_ShipClass",
        ]


class CMMS_EquipmentTypeMasterSerializer(serializers.ModelSerializer):
    equipment_type_id = serializers.IntegerField(required=False, allow_null=True)
    equipment_desc = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    status = serializers.IntegerField(required=False, allow_null=True)
    universal_id_ch_master_equipment_type = serializers.CharField(required=True)

    class Meta:
        model = EquipmentTypeMaster
        fields = [
            "equipment_type_id",
            "equipment_desc",
            "status",
            "universal_id_ch_master_equipment_type",
        ]





class CMMS_M_PropulsionSerializer(serializers.ModelSerializer):
    PropulsionID = serializers.IntegerField(
        source="propulsion_id", required=False, allow_null=True
    )
    PropulsionName = serializers.CharField(
        source="propulsion_name", required=False, allow_null=True, allow_blank=True
    )
    Active = serializers.BooleanField(source="active", required=False, allow_null=True)
    Universal_ID_M_Propulsion = serializers.CharField(
        source="universal_id_m_propulsion", required=True
    )

    class Meta:
        model = PropulsionMaster
        fields = [
            "PropulsionID",
            "PropulsionName",
            "Active",
            "Universal_ID_M_Propulsion",
        ]


class CMMS_M_CountrySerializer(serializers.ModelSerializer):
    CountryID = serializers.IntegerField(
        source="country_id", required=False, allow_null=True
    )
    CountryCode = serializers.CharField(
        source="country_code", required=False, allow_null=True, allow_blank=True
    )
    CountryName = serializers.CharField(
        source="country_name", required=False, allow_null=True, allow_blank=True
    )
    Active = serializers.BooleanField(source="active", required=False, allow_null=True)
    Universal_ID_M_Country = serializers.CharField(
        source="universal_id_m_country", required=True
    )

    class Meta:
        model = CountryMaster
        fields = [
            "CountryID",
            "CountryCode",
            "CountryName",
            "Active",
            "Universal_ID_M_Country",
        ]


class CMMS_M_CommandSerializer(serializers.ModelSerializer):
    CommandID = serializers.IntegerField(
        source="command_id", required=False, allow_null=True
    )
    CommandName = serializers.CharField(
        source="command_name", required=False, allow_null=True, allow_blank=True
    )
    CommandCode = serializers.CharField(
        source="command_code", required=False, allow_null=True, allow_blank=True
    )
    Active = serializers.BooleanField(source="active", required=False, allow_null=True)
    Universal_ID_M_Command = serializers.CharField(
        source="universal_id_m_command", required=True
    )

    class Meta:
        model = CommandMaster
        fields = [
            "CommandID",
            "CommandName",
            "CommandCode",
            "Active",
            "Universal_ID_M_Command",
        ]


class CMMS_M_OpsAuthoritySerializer(serializers.ModelSerializer):
    AuthorityID = serializers.IntegerField(
        source="authority_id", required=False, allow_null=True
    )
    OpsCode = serializers.IntegerField(
        source="ops_code", required=False, allow_null=True
    )
    OpsAuthority = serializers.CharField(
        source="ops_authority", required=False, allow_null=True, allow_blank=True
    )
    CommandID = serializers.IntegerField(
        source="command_id", required=False, allow_null=True
    )
    CommandName = serializers.CharField(
        source="command_name", required=False, allow_null=True, allow_blank=True
    )
    Active = serializers.BooleanField(source="active", required=False, allow_null=True)
    Universal_ID_M_OpsAuthority = serializers.CharField(
        source="universal_id_m_ops_authority", required=True
    )
    Universal_ID_M_Command = serializers.CharField(
        source="universal_id_m_command",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    Address = serializers.CharField(
        source="address", required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = OpsAuthorityMaster
        fields = [
            "AuthorityID",
            "OpsCode",
            "OpsAuthority",
            "CommandID",
            "CommandName",
            "Active",
            "Universal_ID_M_OpsAuthority",
            "Universal_ID_M_Command",
            "Address",
        ]


class CMMS_M_ShipCategorySerializer(serializers.ModelSerializer):
    ShipCategoryID = serializers.IntegerField(
        source="ship_category_id", required=False, allow_null=True
    )
    ShipCategoryName = serializers.CharField(
        source="ship_category_name", required=False, allow_null=True, allow_blank=True
    )
    Active = serializers.BooleanField(source="active", required=False, allow_null=True)
    Universal_ID_M_ShipCategory = serializers.CharField(
        source="universal_id_m_ship_category", required=True
    )

    class Meta:
        model = ShipCategoryMaster
        fields = [
            "ShipCategoryID",
            "ShipCategoryName",
            "Active",
            "Universal_ID_M_ShipCategory",
        ]
