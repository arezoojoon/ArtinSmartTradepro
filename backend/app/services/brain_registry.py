"""
Phase 5 Brain Explainability and Engine Run Registry
Unified explainability/provenance layer and engine run registry
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..models.brain_assets import BrainEngineRun, BrainDataSource, BrainEngineType, BrainRunStatus
from ..services.brain_assets_repository import BrainAssetRepository

class DataUsedItem(BaseModel):
    """Single data source entry used in engine computation"""
    source_name: str = Field(..., description="Name of the data source")
    dataset: str = Field(..., description="Dataset or table name")
    collected_at: Optional[datetime] = Field(None, description="When data was collected")
    coverage: str = Field(..., description="Coverage description (e.g., 'US-EU trade 2023')")
    record_count: Optional[int] = Field(None, description="Number of records used")
    confidence: Optional[float] = Field(None, description="Confidence in this data source")

class ExplainabilityBundle(BaseModel):
    """Complete explainability bundle for brain engine outputs"""
    data_used: List[DataUsedItem] = Field(..., description="Data sources used in computation")
    assumptions: List[str] = Field(..., description="Explicit assumptions made")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    confidence_rationale: str = Field(..., description="How confidence was calculated")
    action_plan: List[str] = Field(..., description="Deterministic next steps")
    limitations: List[str] = Field(default_factory=list, description="Known limitations")
    computation_method: str = Field(..., description="Method used for computation")
    missing_fields: List[str] = Field(default_factory=list, description="Required fields that were missing")

class BrainEngineRegistry:
    """Registry for brain engine runs with explainability tracking"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = BrainAssetRepository(db)
    
    def create_successful_run(
        self,
        tenant_id: UUID,
        engine_type: BrainEngineType,
        input_payload: Dict[str, Any],
        output_payload: Dict[str, Any],
        explainability: ExplainabilityBundle
    ) -> BrainEngineRun:
        """Create a successful engine run record"""
        return self.repo.create_engine_run(tenant_id, {
            'engine_type': engine_type,
            'input_payload': input_payload,
            'output_payload': output_payload,
            'explainability': explainability.dict(),
            'status': BrainRunStatus.SUCCESS
        })
    
    def create_insufficient_data_run(
        self,
        tenant_id: UUID,
        engine_type: BrainEngineType,
        input_payload: Dict[str, Any],
        missing_fields: List[str],
        suggested_next_steps: List[str]
    ) -> BrainEngineRun:
        """Create an insufficient data run record"""
        explainability = ExplainabilityBundle(
            data_used=[],
            assumptions=[f"Missing required fields: {', '.join(missing_fields)}"],
            confidence=0.0,
            confidence_rationale="Insufficient data for computation",
            action_plan=suggested_next_steps,
            limitations=["Insufficient data"],
            computation_method="None - insufficient data",
            missing_fields=missing_fields
        )
        
        output_payload = {
            "status": "insufficient_data",
            "message": "Insufficient data for computation",
            "missing_fields": missing_fields,
            "suggested_next_steps": suggested_next_steps
        }
        
        return self.repo.create_engine_run(tenant_id, {
            'engine_type': engine_type,
            'input_payload': input_payload,
            'output_payload': output_payload,
            'explainability': explainability.dict(),
            'status': BrainRunStatus.INSUFFICIENT_DATA
        })
    
    def create_failed_run(
        self,
        tenant_id: UUID,
        engine_type: BrainEngineType,
        input_payload: Dict[str, Any],
        error: Dict[str, Any]
    ) -> BrainEngineRun:
        """Create a failed engine run record"""
        explainability = ExplainabilityBundle(
            data_used=[],
            assumptions=["Engine failed during computation"],
            confidence=0.0,
            confidence_rationale="Engine failure",
            action_plan=["Check error details and retry"],
            limitations=["Engine failure"],
            computation_method="None - engine failed"
        )
        
        return self.repo.create_engine_run(tenant_id, {
            'engine_type': engine_type,
            'input_payload': input_payload,
            'output_payload': {"status": "failed", "error": error},
            'explainability': explainability.dict(),
            'status': BrainRunStatus.FAILED,
            'error': error
        })
    
    def get_run_history(
        self,
        tenant_id: UUID,
        engine_type: Optional[BrainEngineType] = None,
        limit: int = 50
    ) -> List[BrainEngineRun]:
        """Get engine run history"""
        return self.repo.get_engine_runs(tenant_id, engine_type, limit=limit)
    
    def get_run(self, tenant_id: UUID, run_id: UUID) -> Optional[BrainEngineRun]:
        """Get specific engine run"""
        return self.repo.get_engine_run(tenant_id, run_id)
    
    def register_data_source(
        self,
        tenant_id: UUID,
        name: str,
        source_type: str,
        meta: Optional[Dict[str, Any]] = None
    ) -> BrainDataSource:
        """Register a new data source"""
        return self.repo.create_data_source(tenant_id, {
            'name': name,
            'type': source_type,
            'meta': meta or {}
        })
    
    def get_data_sources(self, tenant_id: UUID, active_only: bool = True) -> List[BrainDataSource]:
        """Get available data sources"""
        return self.repo.get_data_sources(tenant_id, active_only)
    
    def calculate_confidence_score(
        self,
        data_sources: List[DataUsedItem],
        assumptions_count: int,
        missing_fields_count: int
    ) -> tuple[float, str]:
        """
        Calculate confidence score based on data quality and completeness
        
        Args:
            data_sources: List of data sources used
            assumptions_count: Number of assumptions made
            missing_fields_count: Number of missing required fields
            
        Returns:
            Tuple of (confidence_score, rationale)
        """
        # Base confidence from data sources
        if not data_sources:
            return 0.0, "No data sources available"
        
        # Start with base confidence
        confidence = 0.3
        
        # Add confidence for data sources
        source_confidence = sum(
            ds.confidence if ds.confidence is not None else 0.5 
            for ds in data_sources
        ) / len(data_sources)
        confidence += source_confidence * 0.4
        
        # Deduct for assumptions
        confidence -= assumptions_count * 0.1
        
        # Deduct for missing fields
        confidence -= missing_fields_count * 0.15
        
        # Cap at 0.9 maximum
        confidence = max(0.0, min(0.9, confidence))
        
        rationale_parts = []
        if data_sources:
            rationale_parts.append(f"Used {len(data_sources)} data sources")
            rationale_parts.append(f"Average source confidence: {source_confidence:.2f}")
        if assumptions_count > 0:
            rationale_parts.append(f"Made {assumptions_count} assumptions")
        if missing_fields_count > 0:
            rationale_parts.append(f"Missing {missing_fields_count} required fields")
        
        rationale = "; ".join(rationale_parts)
        
        return confidence, rationale

class BrainEngineValidator:
    """Validator for brain engine inputs and outputs"""
    
    @staticmethod
    def validate_required_fields(
        input_data: Dict[str, Any],
        required_fields: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Validate that all required fields are present and not empty
        
        Args:
            input_data: Input data to validate
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, missing_fields)
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in input_data or input_data[field] is None:
                missing_fields.append(field)
            elif isinstance(input_data[field], str) and not input_data[field].strip():
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
    
    @staticmethod
    def validate_numeric_fields(
        input_data: Dict[str, Any],
        numeric_fields: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Validate that numeric fields contain valid numbers
        
        Args:
            input_data: Input data to validate
            numeric_fields: List of field names that should be numeric
            
        Returns:
            Tuple of (is_valid, invalid_fields)
        """
        invalid_fields = []
        
        for field in numeric_fields:
            if field in input_data and input_data[field] is not None:
                try:
                    float(input_data[field])
                except (ValueError, TypeError):
                    invalid_fields.append(field)
        
        return len(invalid_fields) == 0, invalid_fields
    
    @staticmethod
    def validate_currency_codes(
        input_data: Dict[str, Any],
        currency_fields: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Validate currency codes are valid 3-letter codes
        
        Args:
            input_data: Input data to validate
            currency_fields: List of field names containing currency codes
            
        Returns:
            Tuple of (is_valid, invalid_fields)
        """
        invalid_fields = []
        valid_currencies = {'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'AUD', 'CAD', 'CHF', 'SEK', 'NOK', 'DKK'}
        
        for field in currency_fields:
            if field in input_data and input_data[field] is not None:
                currency = str(input_data[field]).upper()
                if currency not in valid_currencies:
                    invalid_fields.append(field)
        
        return len(invalid_fields) == 0, invalid_fields

# Helper functions for creating explainability bundles
def make_insufficient_data_bundle(
    missing_fields: List[str],
    suggested_next_steps: List[str],
    engine_type: str
) -> ExplainabilityBundle:
    """Create explainability bundle for insufficient data cases"""
    return ExplainabilityBundle(
        data_used=[],
        assumptions=[f"Missing required fields: {', '.join(missing_fields)}"],
        confidence=0.0,
        confidence_rationale="Insufficient data for computation",
        action_plan=suggested_next_steps,
        limitations=["Insufficient data"],
        computation_method=f"None - insufficient data for {engine_type}",
        missing_fields=missing_fields
    )

def make_data_used_item(
    source_name: str,
    dataset: str,
    coverage: str,
    record_count: Optional[int] = None,
    confidence: Optional[float] = None
) -> DataUsedItem:
    """Create a DataUsedItem with common defaults"""
    return DataUsedItem(
        source_name=source_name,
        dataset=dataset,
        collected_at=datetime.utcnow(),
        coverage=coverage,
        record_count=record_count,
        confidence=confidence
    )
