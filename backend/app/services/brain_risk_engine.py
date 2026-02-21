"""
Phase 5 Risk Engine v1
Rule-based risk analysis with risk register output
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from ..models.brain_assets import (
    AssetSupplierReliability, AssetBuyerPaymentBehavior, RiskSeverity
)
from ..services.brain_assets_repository import BrainAssetRepository
from ..services.brain_registry import BrainEngineRegistry, BrainEngineValidator, make_data_used_item
from ..schemas.brain import (
    RiskInput, RiskOutput, RiskItem, ExplainabilityBundle
)

class RiskEngine:
    """
    Rule-based risk analysis engine
    Evaluates political, payment, supplier, and route risks
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = BrainAssetRepository(db)
        self.registry = BrainEngineRegistry(db)
        self.validator = BrainEngineValidator()
    
    def run_analysis(self, tenant_id: UUID, input_data: RiskInput) -> RiskOutput:
        """
        Run complete risk analysis
        
        Args:
            tenant_id: Tenant ID for RLS
            input_data: Risk analysis input
            
        Returns:
            RiskOutput with risk register and overall assessment
        """
        try:
            # Validate input
            validation_result = self._validate_input(input_data)
            if not validation_result[0]:
                return self._create_insufficient_data_response(
                    tenant_id, input_data, validation_result[1]
                )
            
            # Get tenant risk configuration
            tenant_config = self._get_tenant_risk_config(tenant_id)
            
            # Analyze different risk types
            political_risks = self._analyze_political_risks(input_data, tenant_config)
            payment_risks = self._analyze_payment_risks(input_data, tenant_id)
            supplier_risks = self._analyze_supplier_risks(input_data, tenant_id)
            route_risks = self._analyze_route_risks(input_data, tenant_config)
            
            # Combine all risks
            all_risks = political_risks + payment_risks + supplier_risks + route_risks
            
            # Calculate overall risk level
            overall_risk_level = self._calculate_overall_risk_level(all_risks)
            
            # Create explainability bundle
            explainability = self._create_explainability_bundle(
                tenant_id, input_data, all_risks, tenant_config
            )
            
            # Save engine run
            output_payload = {
                "risk_register": [risk.dict() for risk in all_risks],
                "overall_risk_level": overall_risk_level.value if overall_risk_level else None,
                "tenant_config": tenant_config
            }
            
            self.registry.create_successful_run(
                tenant_id,
                "risk",
                input_data.dict(),
                output_payload,
                explainability
            )
            
            return RiskOutput(
                status="success",
                risk_register=all_risks,
                overall_risk_level=overall_risk_level,
                explainability=explainability
            )
            
        except Exception as e:
            # Create failed run
            error_data = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.registry.create_failed_run(
                tenant_id,
                "risk",
                input_data.dict(),
                error_data
            )
            
            raise
    
    def _validate_input(self, input_data: RiskInput) -> Tuple[bool, List[str]]:
        """Validate risk input data"""
        missing_fields = []
        
        # Check required fields
        required_fields = [
            'product_key', 'origin_country', 'destination_country', 
            'incoterms', 'payment_terms'
        ]
        
        is_valid, missing = self.validator.validate_required_fields(
            input_data.dict(), required_fields
        )
        missing_fields.extend(missing)
        
        return (len(missing_fields) == 0), missing_fields
    
    def _get_tenant_risk_config(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get tenant-specific risk configuration"""
        # For now, return default configuration
        # In production, this would come from tenant settings
        return {
            "risk_countries": ["IR", "KP", "SY", "AF", "SS", "MM", "YE"],
            "sanctions_countries": ["IR", "KP", "SY", "RU"],
            "risky_routes": ["RedSea", "Strait_of_Hormuz", "Suez_Canal"],
            "high_risk_payment_terms": ["OA"],
            "supplier_reliability_threshold": 70,
            "buyer_payment_delay_threshold": 30
        }
    
    def _analyze_political_risks(self, input_data: RiskInput, tenant_config: Dict[str, Any]) -> List[RiskItem]:
        """Analyze political and sanctions risks"""
        risks = []
        
        # Check destination country risk
        if input_data.destination_country in tenant_config["risk_countries"]:
            risks.append(RiskItem(
                type="political",
                severity=RiskSeverity.HIGH,
                reason=f"Destination country {input_data.destination_country} is in high-risk list",
                mitigation_steps=[
                    "Consider alternative destination markets",
                    "Obtain political risk insurance",
                    "Monitor political developments closely"
                ]
            ))
        
        # Check sanctions risk
        if input_data.destination_country in tenant_config["sanctions_countries"]:
            risks.append(RiskItem(
                type="political",
                severity=RiskSeverity.HIGH,
                reason=f"Destination country {input_data.destination_country} is under sanctions",
                mitigation_steps=[
                    "Verify compliance with sanctions regulations",
                    "Consult legal counsel before proceeding",
                    "Consider alternative routing if applicable"
                ]
            ))
        
        # Check origin country risk
        if input_data.origin_country in tenant_config["risk_countries"]:
            risks.append(RiskItem(
                type="political",
                severity=RiskSeverity.MEDIUM,
                reason=f"Origin country {input_data.origin_country} is in risk list",
                mitigation_steps=[
                    "Verify export compliance requirements",
                    "Monitor origin country political situation",
                    "Consider alternative suppliers if available"
                ]
            ))
        
        return risks
    
    def _analyze_payment_risks(self, input_data: RiskInput, tenant_id: UUID) -> List[RiskItem]:
        """Analyze payment risks"""
        risks = []
        
        # Check payment terms risk
        if input_data.payment_terms.value in ["OA"]:
            risks.append(RiskItem(
                type="payment",
                severity=RiskSeverity.HIGH,
                reason=f"High-risk payment terms: {input_data.payment_terms.value}",
                mitigation_steps=[
                    "Request LC or TT payment terms",
                    "Obtain credit insurance",
                    "Reduce payment period if possible"
                ]
            ))
        elif input_data.payment_terms.value == "TT":
            risks.append(RiskItem(
                type="payment",
                severity=RiskSeverity.MEDIUM,
                reason=f"Moderate risk payment terms: {input_data.payment_terms.value}",
                mitigation_steps=[
                    "Confirm payment timing with buyer",
                    "Consider partial advance payment",
                    "Monitor buyer payment history"
                ]
            ))
        
        # Check buyer payment behavior if destination country provided
        if input_data.destination_country:
            buyer_behaviors = self.repo.get_buyer_payment_behavior(
                tenant_id, input_data.destination_country
            )
            
            if buyer_behaviors:
                # Calculate average metrics
                avg_delay = sum(
                    b.avg_payment_delay_days for b in buyer_behaviors 
                    if b.avg_payment_delay_days is not None
                ) / len([b for b in buyer_behaviors if b.avg_payment_delay_days is not None])
                
                avg_default_rate = sum(
                    float(b.default_rate) for b in buyer_behaviors 
                    if b.default_rate is not None
                ) / len([b for b in buyer_behaviors if b.default_rate is not None])
                
                # Check payment delay risk
                if avg_delay > 30:
                    risks.append(RiskItem(
                        type="payment",
                        severity=RiskSeverity.MEDIUM,
                        reason=f"High average payment delay in {input_data.destination_country}: {avg_delay:.1f} days",
                        mitigation_steps=[
                            "Require shorter payment terms",
                            "Consider payment guarantees",
                            "Monitor buyer creditworthiness"
                        ]
                    ))
                
                # Check default rate risk
                if avg_default_rate > 0.05:  # 5%
                    risks.append(RiskItem(
                        type="payment",
                        severity=RiskSeverity.HIGH,
                        reason=f"High default rate in {input_data.destination_country}: {avg_default_rate:.2%}",
                        mitigation_steps=[
                            "Require LC payment terms",
                            "Obtain trade credit insurance",
                            "Consider pre-payment or escrow"
                        ]
                    ))
        
        return risks
    
    def _analyze_supplier_risks(self, input_data: RiskInput, tenant_id: UUID) -> List[RiskItem]:
        """Analyze supplier risks"""
        risks = []
        
        # Only analyze if supplier_id is provided
        if not input_data.supplier_id:
            return risks
        
        # Try to find supplier by name (assuming supplier_id is name for now)
        # In production, this would be a proper supplier lookup
        supplier_records = self.repo.list_suppliers_by_country(
            tenant_id, input_data.origin_country
        )
        
        matching_suppliers = [
            s for s in supplier_records 
            if input_data.supplier_id.lower() in s.supplier_name.lower()
        ]
        
        if matching_suppliers:
            supplier = matching_suppliers[0]  # Use first match
            
            # Check reliability score
            if supplier.reliability_score < 50:
                risks.append(RiskItem(
                    type="supplier",
                    severity=RiskSeverity.HIGH,
                    reason=f"Low supplier reliability score: {supplier.reliability_score}",
                    mitigation_steps=[
                        "Consider alternative suppliers",
                        "Request additional quality assurances",
                        "Implement stricter inspection procedures"
                    ]
                ))
            elif supplier.reliability_score < 70:
                risks.append(RiskItem(
                    type="supplier",
                    severity=RiskSeverity.MEDIUM,
                    reason=f"Moderate supplier reliability score: {supplier.reliability_score}",
                    mitigation_steps=[
                        "Monitor supplier performance closely",
                        "Consider backup suppliers",
                        "Implement quality control checks"
                    ]
                ))
            
            # Check on-time delivery rate
            if supplier.on_time_rate is not None and supplier.on_time_rate < 0.8:
                risks.append(RiskItem(
                    type="supplier",
                    severity=RiskSeverity.MEDIUM,
                    reason=f"Poor on-time delivery rate: {supplier.on_time_rate:.1%}",
                    mitigation_steps=[
                        "Build buffer time into schedule",
                        "Consider penalty clauses for delays",
                        "Monitor delivery performance"
                    ]
                ))
            
            # Check defect rate
            if supplier.defect_rate is not None and supplier.defect_rate > 0.05:
                risks.append(RiskItem(
                    type="supplier",
                    severity=RiskSeverity.HIGH,
                    reason=f"High defect rate: {supplier.defect_rate:.1%}",
                    mitigation_steps=[
                        "Implement stricter quality control",
                        "Require quality certifications",
                        "Consider alternative suppliers"
                    ]
                ))
            
            # Check dispute history
            if supplier.dispute_count > 3:
                risks.append(RiskItem(
                    type="supplier",
                    severity=RiskSeverity.MEDIUM,
                    reason=f"High dispute count: {supplier.dispute_count}",
                    mitigation_steps=[
                        "Review dispute history details",
                        "Include clear dispute resolution clauses",
                        "Consider alternative suppliers"
                    ]
                ))
        
        else:
            # Unknown supplier
            risks.append(RiskItem(
                type="supplier",
                severity=RiskSeverity.MEDIUM,
                reason=f"Unknown supplier: {input_data.supplier_id}",
                mitigation_steps=[
                    "Conduct supplier verification",
                    "Request references and certifications",
                    "Start with trial orders"
                ]
            ))
        
        return risks
    
    def _analyze_route_risks(self, input_data: RiskInput, tenant_config: Dict[str, Any]) -> List[RiskItem]:
        """Analyze route risks"""
        risks = []
        
        # Check route tags for risky areas
        if input_data.route_tags:
            for tag in input_data.route_tags:
                if tag in tenant_config["risky_routes"]:
                    risks.append(RiskItem(
                        type="route",
                        severity=RiskSeverity.HIGH,
                        reason=f"Route passes through high-risk area: {tag}",
                        mitigation_steps=[
                            "Consider alternative routing options",
                            "Obtain route-specific insurance",
                            "Monitor route security situation",
                            "Build extra time into delivery schedule"
                        ]
                    ))
        
        # Check for common high-risk routes based on geography
        high risk_routes = [
            ("IR", "any"),  # Iran to anywhere
            ("any", "IR"),  # Anywhere to Iran
            ("RU", "UA"),  # Russia to Ukraine
            ("UA", "RU"),  # Ukraine to Russia
        ]
        
        for origin, dest in high risk_routes:
            if (origin == "any" or input_data.origin_country == origin) and \
               (dest == "any" or input_data.destination_country == dest):
                risks.append(RiskItem(
                    type="route",
                    severity=RiskSeverity.HIGH,
                    reason=f"High-risk route: {input_data.origin_country} to {input_data.destination_country}",
                    mitigation_steps=[
                        "Verify route feasibility and safety",
                        "Consider alternative transit countries",
                        "Obtain comprehensive shipping insurance",
                        "Monitor geopolitical developments"
                    ]
                ))
                break
        
        return risks
    
    def _calculate_overall_risk_level(self, risks: List[RiskItem]) -> Optional[RiskSeverity]:
        """Calculate overall risk level from individual risks"""
        if not risks:
            return None
        
        # Count risks by severity
        high_count = sum(1 for risk in risks if risk.severity == RiskSeverity.HIGH)
        medium_count = sum(1 for risk in risks if risk.severity == RiskSeverity.MEDIUM)
        low_count = sum(1 for risk in risks if risk.severity == RiskSeverity.LOW)
        
        # Determine overall level
        if high_count >= 2:
            return RiskSeverity.HIGH
        elif high_count >= 1 or medium_count >= 3:
            return RiskSeverity.HIGH
        elif medium_count >= 2:
            return RiskSeverity.MEDIUM
        elif medium_count >= 1 or low_count >= 3:
            return RiskSeverity.MEDIUM
        elif low_count >= 1:
            return RiskSeverity.LOW
        else:
            return RiskSeverity.LOW
    
    def _create_explainability_bundle(
        self,
        tenant_id: UUID,
        input_data: RiskInput,
        risks: List[RiskItem],
        tenant_config: Dict[str, Any]
    ) -> ExplainabilityBundle:
        """Create comprehensive explainability bundle"""
        
        # Data used
        data_used = []
        
        # Add input data source
        data_used.append(make_data_used_item(
            source_name="user_input",
            dataset="risk_analysis_input",
            coverage=f"{input_data.origin_country}->{input_data.destination_country}",
            confidence=1.0
        ))
        
        # Add tenant config source
        data_used.append(make_data_used_item(
            source_name="tenant_configuration",
            dataset="risk_settings",
            coverage=f"Risk countries: {len(tenant_config['risk_countries'])}, Sanctions: {len(tenant_config['sanctions_countries'])}",
            confidence=0.9
        ))
        
        # Add asset data sources if used
        asset_sources_used = set()
        for risk in risks:
            if "buyer behavior" in risk.reason.lower():
                asset_sources_used.add("asset_buyer_payment_behavior")
            elif "supplier" in risk.reason.lower():
                asset_sources_used.add("asset_supplier_reliability")
        
        for source in asset_sources_used:
            data_used.append(make_data_used_item(
                source_name=source,
                dataset=source,
                coverage="Historical risk data",
                confidence=0.8
            ))
        
        # Assumptions
        assumptions = [
            "Risk assessment based on current geopolitical situation",
            "Historical data may not reflect current conditions",
            "Route risk assessment based on major shipping lanes"
        ]
        
        if not input_data.supplier_id:
            assumptions.append("No supplier-specific analysis performed")
        
        if not input_data.route_tags:
            assumptions.append("No specific route tags provided for analysis")
        
        # Confidence calculation
        confidence = self._calculate_confidence(input_data, risks, asset_sources_used)
        confidence_rationale = f"Base confidence 0.4 + data availability + risk factor coverage = {confidence:.1f}"
        
        # Action plan
        action_plan = []
        if any(risk.severity == RiskSeverity.HIGH for risk in risks):
            action_plan.append("Address high-risk items before proceeding")
            action_plan.append("Consider alternative markets or suppliers")
        
        if any(risk.type == "payment" for risk in risks):
            action_plan.append("Review and strengthen payment terms")
        
        if any(risk.type == "supplier" for risk in risks):
            action_plan.append("Conduct additional supplier due diligence")
        
        if any(risk.type == "route" for risk in risks):
            action_plan.append("Verify routing and insurance coverage")
        
        action_plan.append("Monitor risk factors throughout transaction")
        
        # Limitations
        limitations = [
            "Risk assessment based on available data sources",
            "Political situations can change rapidly",
            "Historical performance may not predict future results",
            "Route risks may vary by specific logistics provider"
        ]
        
        return ExplainabilityBundle(
            data_used=data_used,
            assumptions=assumptions,
            confidence=confidence,
            confidence_rationale=confidence_rationale,
            action_plan=action_plan,
            limitations=limitations,
            computation_method="Rule-based risk analysis with configurable thresholds",
            missing_fields=[]
        )
    
    def _calculate_confidence(
        self, 
        input_data: RiskInput, 
        risks: List[RiskItem], 
        asset_sources_used: set
    ) -> float:
        """Calculate confidence score based on data availability"""
        confidence = 0.4  # Base confidence
        
        # Add confidence for supplier data
        if input_data.supplier_id:
            confidence += 0.2
        
        # Add confidence for route tags
        if input_data.route_tags:
            confidence += 0.1
        
        # Add confidence for asset data usage
        confidence += len(asset_sources_used) * 0.15
        
        # Add confidence for risk coverage
        risk_types = set(risk.type for risk in risks)
        confidence += len(risk_types) * 0.05
        
        return min(confidence, 0.9)
    
    def _create_insufficient_data_response(
        self,
        tenant_id: UUID,
        input_data: RiskInput,
        missing_fields: List[str]
    ) -> RiskOutput:
        """Create insufficient data response"""
        suggested_steps = [
            f"Provide missing field: {field}" for field in missing_fields
        ]
        
        # Create insufficient data run
        self.registry.create_insufficient_data_run(
            tenant_id,
            "risk",
            input_data.dict(),
            missing_fields,
            suggested_steps
        )
        
        return RiskOutput(
            status="insufficient_data",
            explainability=ExplainabilityBundle(
                data_used=[],
                assumptions=[f"Missing required fields: {', '.join(missing_fields)}"],
                confidence=0.0,
                confidence_rationale="Insufficient data for computation",
                action_plan=suggested_steps,
                limitations=["Insufficient data"],
                computation_method="None - insufficient data",
                missing_fields=missing_fields
            )
        )
