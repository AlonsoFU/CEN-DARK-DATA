"""
EAF Universal Schema Definitions
Chilean Electrical System Failure Analysis Reports

This module defines the universal JSON schema structure for EAF documents,
ensuring consistent data transformation across all failure analysis reports.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """EAF document metadata"""
    document_id: str = Field(..., description="Unique EAF document identifier")
    document_type: str = Field(default="EAF", description="Document type")
    eaf_number: str = Field(..., description="EAF report number (e.g., EAF 299/2025)")
    source_file: str = Field(..., description="Source PDF file path")
    processing_date: datetime = Field(default_factory=datetime.now)
    extraction_version: str = Field(default="1.0")
    domain: str = Field(default="operaciones")
    subdomain: str = Field(default="eaf")


class IncidentMetadata(BaseModel):
    """Incident-specific metadata"""
    incident_date: datetime = Field(..., description="Date of the electrical incident")
    incident_type: str = Field(..., description="Type of failure/incident")
    severity_level: str = Field(..., description="Incident severity classification")
    affected_system: str = Field(..., description="Affected electrical system/equipment")
    location: str = Field(..., description="Geographic location of incident")


class EquipmentInfo(BaseModel):
    """Equipment involved in the incident"""
    equipment_id: str = Field(..., description="Equipment identifier")
    equipment_type: str = Field(..., description="Type of equipment")
    manufacturer: str = Field(None, description="Equipment manufacturer")
    model: str = Field(None, description="Equipment model")
    voltage_level: str = Field(None, description="Operating voltage level")
    installation_date: datetime = Field(None, description="Equipment installation date")
    last_maintenance: datetime = Field(None, description="Last maintenance date")


class CompanyEntity(BaseModel):
    """Company entities involved"""
    name: str = Field(..., description="Company name")
    rut: str = Field(None, description="Chilean RUT identifier")
    role: str = Field(..., description="Company role in incident")
    contact_info: Dict[str, Any] = Field(default_factory=dict)


class FailureAnalysis(BaseModel):
    """Failure analysis details"""
    root_cause: str = Field(..., description="Primary root cause of failure")
    contributing_factors: List[str] = Field(default_factory=list)
    failure_mode: str = Field(..., description="How the failure occurred")
    impact_assessment: str = Field(..., description="Impact on grid operations")
    duration_minutes: int = Field(None, description="Incident duration in minutes")


class CorrectiveActions(BaseModel):
    """Corrective and preventive actions"""
    immediate_actions: List[str] = Field(default_factory=list)
    corrective_measures: List[str] = Field(default_factory=list)
    preventive_measures: List[str] = Field(default_factory=list)
    responsible_party: str = Field(None, description="Responsible organization")
    completion_deadline: datetime = Field(None, description="Action completion deadline")


class TechnicalData(BaseModel):
    """Technical measurements and data"""
    measurements: Dict[str, Any] = Field(default_factory=dict)
    operating_conditions: Dict[str, Any] = Field(default_factory=dict)
    weather_conditions: Dict[str, Any] = Field(default_factory=dict)
    system_state: Dict[str, Any] = Field(default_factory=dict)


class RegulatoryReferences(BaseModel):
    """Regulatory and legal references"""
    applicable_norms: List[str] = Field(default_factory=list)
    cen_procedures: List[str] = Field(default_factory=list)
    legal_framework: List[str] = Field(default_factory=list)
    compliance_status: str = Field(None, description="Compliance assessment")


class CrossReferences(BaseModel):
    """Cross-references to other documents and entities"""
    related_eaf_reports: List[str] = Field(default_factory=list)
    related_equipment: List[str] = Field(default_factory=list)
    related_companies: List[str] = Field(default_factory=list)
    similar_incidents: List[str] = Field(default_factory=list)
    external_references: List[str] = Field(default_factory=list)


class QualityMetrics(BaseModel):
    """Extraction quality and validation metrics"""
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    validation_status: str = Field(default="pending")
    processing_warnings: List[str] = Field(default_factory=list)
    manual_review_flags: List[str] = Field(default_factory=list)
    data_completeness: float = Field(default=0.0, ge=0.0, le=1.0)


class EAFUniversalSchema(BaseModel):
    """
    Universal schema for EAF (Estudios de Análisis de Falla) documents
    Chilean electrical system failure analysis reports
    """

    # Core metadata
    document_metadata: DocumentMetadata
    incident_metadata: IncidentMetadata

    # Content structure
    content_structure: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document structure and sections"
    )

    # Extracted entities
    equipment_entities: List[EquipmentInfo] = Field(default_factory=list)
    company_entities: List[CompanyEntity] = Field(default_factory=list)

    # Analysis data
    failure_analysis: FailureAnalysis
    corrective_actions: CorrectiveActions
    technical_data: TechnicalData

    # References and compliance
    regulatory_references: RegulatoryReferences
    cross_references: CrossReferences

    # Quality assurance
    quality_metrics: QualityMetrics

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        validate_assignment = True
        use_enum_values = True


def create_eaf_template(eaf_number: str, incident_date: datetime) -> EAFUniversalSchema:
    """
    Create a template EAF schema with basic metadata

    Args:
        eaf_number: EAF report number (e.g., "EAF 299/2025")
        incident_date: Date of the electrical incident

    Returns:
        EAFUniversalSchema: Template schema with basic metadata
    """

    document_metadata = DocumentMetadata(
        document_id=f"eaf_{eaf_number.replace('/', '_').replace(' ', '_').lower()}",
        eaf_number=eaf_number,
        source_file=f"{eaf_number.replace('/', '_').replace(' ', '_')}.pdf"
    )

    incident_metadata = IncidentMetadata(
        incident_date=incident_date,
        incident_type="",
        severity_level="",
        affected_system="",
        location=""
    )

    failure_analysis = FailureAnalysis(
        root_cause="",
        failure_mode="",
        impact_assessment=""
    )

    corrective_actions = CorrectiveActions()
    technical_data = TechnicalData()
    regulatory_references = RegulatoryReferences()
    cross_references = CrossReferences()
    quality_metrics = QualityMetrics()

    return EAFUniversalSchema(
        document_metadata=document_metadata,
        incident_metadata=incident_metadata,
        failure_analysis=failure_analysis,
        corrective_actions=corrective_actions,
        technical_data=technical_data,
        regulatory_references=regulatory_references,
        cross_references=cross_references,
        quality_metrics=quality_metrics
    )


def validate_eaf_schema(data: Dict[str, Any]) -> EAFUniversalSchema:
    """
    Validate and create EAF schema from dictionary data

    Args:
        data: Dictionary containing EAF data

    Returns:
        EAFUniversalSchema: Validated schema instance

    Raises:
        ValidationError: If data doesn't match schema requirements
    """
    return EAFUniversalSchema(**data)