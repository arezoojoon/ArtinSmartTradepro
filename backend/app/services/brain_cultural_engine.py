"""
Phase 5 Cultural Strategy Engine v1
LLM-based cultural strategy with strict guardrails
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
import json

from ..models.brain_assets import CulturalProfile
from ..services.brain_assets_repository import BrainAssetRepository
from ..services.brain_registry import BrainEngineRegistry, BrainEngineValidator, make_data_used_item
from ..schemas.brain import (
    CulturalInput, CulturalOutput, CulturalTemplate, ExplainabilityBundle
)

# Gemini client placeholder - replace with actual implementation
class GeminiClient:
    """Placeholder for Gemini LLM client"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    def generate_content(self, prompt: str, system_prompt: str) -> str:
        """Generate content using Gemini with strict guardrails"""
        # This is a placeholder implementation
        # In production, this would call the actual Gemini API
        
        # For now, return a template response based on the prompt
        if "negotiation" in prompt.lower():
            return self._generate_negotiation_template(prompt)
        elif "email" in prompt.lower():
            return self._generate_email_template(prompt)
        elif "whatsapp" in prompt.lower():
            return self._generate_whatsapp_template(prompt)
        else:
            return self._generate_general_template(prompt)
    
    def _generate_negotiation_template(self, prompt: str) -> str:
        """Generate negotiation template"""
        return """
## Negotiation Strategy

### Opening Approach
- Start with relationship building
- Show understanding of their business needs
- Present win-win value proposition

### Key Talking Points
- Focus on mutual benefits
- Be prepared with data to support your position
- Listen actively to their concerns

### Objection Handling
- Acknowledge their perspective
- Provide alternative solutions
- Maintain professional tone

### Closing Strategy
- Summarize agreed points
- Define next steps clearly
- Confirm timeline and responsibilities
        """.strip()
    
    def _generate_email_template(self, prompt: str) -> str:
        """Generate email template"""
        return """
Subject: Partnership Opportunity

Dear [Contact Name],

I hope this email finds you well. I am reaching out regarding a potential partnership opportunity that could benefit both our organizations.

Based on our research, we believe our [product/service] aligns well with your business objectives. We would appreciate the opportunity to discuss how we can create value together.

Would you be available for a brief call next week to explore this further?

Best regards,
[Your Name]
[Your Title]
[Your Company]
        """.strip()
    
    def _generate_whatsapp_template(self, prompt: str) -> str:
        """Generate WhatsApp template"""
        return """
Hello [Name], this is [Your Name] from [Company]. 

I wanted to reach out about a potential business opportunity. Would you have a few minutes to discuss this week?

Thanks!
[Your Name]
        """.strip()
    
    def _generate_general_template(self, prompt: str) -> str:
        """Generate general template"""
        return """
Based on the cultural context provided, here are some key considerations:

### Communication Style
- Maintain professional and respectful tone
- Be direct but polite
- Focus on building relationships

### Business Etiquette
- Punctuality is important
- Dress appropriately for meetings
- Follow up promptly

### Next Steps
- Research local business customs
- Prepare relevant documentation
- Identify key decision makers
        """.strip()

class CulturalStrategyEngine:
    """
    Cultural strategy engine with LLM integration and strict guardrails
    Generates cultural insights and communication templates
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = BrainAssetRepository(db)
        self.registry = BrainEngineRegistry(db)
        self.validator = BrainEngineValidator()
        
        # Initialize Gemini client (placeholder)
        self.gemini_client = GeminiClient()
    
    def run_analysis(self, tenant_id: UUID, input_data: CulturalInput) -> CulturalOutput:
        """
        Run cultural strategy analysis
        
        Args:
            tenant_id: Tenant ID for RLS
            input_data: Cultural strategy input
            
        Returns:
            CulturalOutput with templates and cultural insights
        """
        try:
            # Validate input
            validation_result = self._validate_input(input_data)
            if not validation_result[0]:
                return self._create_insufficient_data_response(
                    tenant_id, input_data, validation_result[1]
                )
            
            # Get cultural profile
            cultural_profile = self._get_cultural_profile(tenant_id, input_data.destination_country)
            
            if not cultural_profile:
                return self._create_insufficient_data_response(
                    tenant_id, input_data, [f"No cultural profile found for {input_data.destination_country}"]
                )
            
            # Generate templates using LLM
            templates = self._generate_templates(input_data, cultural_profile)
            
            # Generate cultural insights
            negotiation_tips = self._generate_negotiation_tips(cultural_profile)
            objection_handling = self._generate_objection_handling(cultural_profile)
            
            # Create explainability bundle
            explainability = self._create_explainability_bundle(
                tenant_id, input_data, cultural_profile, templates
            )
            
            # Save engine run
            output_payload = {
                "templates": [template.dict() for template in templates],
                "negotiation_tips": negotiation_tips,
                "objection_handling": objection_handling,
                "referenced_profile_ids": [cultural_profile.id],
                "cultural_profile": {
                    "country": cultural_profile.country,
                    "negotiation_style": cultural_profile.negotiation_style,
                    "do_dont": cultural_profile.do_dont,
                    "typical_terms": cultural_profile.typical_terms
                }
            }
            
            self.registry.create_successful_run(
                tenant_id,
                "cultural",
                input_data.dict(),
                output_payload,
                explainability
            )
            
            return CulturalOutput(
                status="success",
                templates=templates,
                negotiation_tips=negotiation_tips,
                objection_handling=objection_handling,
                referenced_profile_ids=[cultural_profile.id],
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
                "cultural",
                input_data.dict(),
                error_data
            )
            
            raise
    
    def _validate_input(self, input_data: CulturalInput) -> Tuple[bool, List[str]]:
        """Validate cultural strategy input data"""
        missing_fields = []
        
        # Check required fields
        required_fields = [
            'destination_country', 'buyer_type', 'payment_terms_target', 
            'deal_context', 'language'
        ]
        
        is_valid, missing = self.validator.validate_required_fields(
            input_data.dict(), required_fields
        )
        missing_fields.extend(missing)
        
        # Validate deal context length
        if input_data.deal_context and len(input_data.deal_context) > 500:
            missing_fields.append("deal_context must be 500 characters or less")
        
        # Validate language
        valid_languages = {'en', 'ar', 'fa', 'ru', 'hi', 'ur'}
        if input_data.language not in valid_languages:
            missing_fields.append(f"Invalid language: {input_data.language}")
        
        return (len(missing_fields) == 0), missing_fields
    
    def _get_cultural_profile(self, tenant_id: UUID, country: str) -> Optional[CulturalProfile]:
        """Get cultural profile for country"""
        return self.repo.get_cultural_profile(tenant_id, country)
    
    def _generate_templates(
        self, 
        input_data: CulturalInput, 
        cultural_profile: CulturalProfile
    ) -> List[CulturalTemplate]:
        """Generate cultural templates using LLM"""
        templates = []
        
        # Prepare cultural data for LLM
        cultural_data = {
            "country": cultural_profile.country,
            "negotiation_style": cultural_profile.negotiation_style or {},
            "do_dont": cultural_profile.do_dont or {},
            "typical_terms": cultural_profile.typical_terms or {}
        }
        
        # Generate different template types
        template_types = ["negotiation", "email", "whatsapp"]
        
        for template_type in template_types:
            try:
                # Create prompt with strict guardrails
                prompt = self._create_llm_prompt(input_data, cultural_data, template_type)
                system_prompt = self._create_system_prompt(cultural_data)
                
                # Generate content
                content = self.gemini_client.generate_content(prompt, system_prompt)
                
                # Create template
                template = CulturalTemplate(
                    template_type=template_type,
                    content=content,
                    language=input_data.language,
                    referenced_profile_id=cultural_profile.id
                )
                templates.append(template)
                
            except Exception as e:
                # Log error but continue with other templates
                print(f"Error generating {template_type} template: {e}")
        
        return templates
    
    def _create_llm_prompt(
        self, 
        input_data: CulturalInput, 
        cultural_data: Dict[str, Any], 
        template_type: str
    ) -> str:
        """Create LLM prompt with cultural context"""
        
        prompt = f"""
Generate a {template_type} template for business communication in {cultural_data['country']}.

Context:
- Buyer Type: {input_data.buyer_type}
- Payment Terms Target: {input_data.payment_terms_target}
- Deal Context: {input_data.deal_context}
- Language: {input_data.language}

Cultural Profile:
- Negotiation Style: {json.dumps(cultural_data['negotiation_style'], indent=2)}
- Do's and Don'ts: {json.dumps(cultural_data['do_dont'], indent=2)}
- Typical Terms: {json.dumps(cultural_data['typical_terms'], indent=2)}

Requirements:
1. Use ONLY the provided cultural profile data
2. Do not invent any cultural facts
3. If the cultural profile is incomplete, acknowledge limitations
4. Generate content in the specified language
5. Focus on practical business communication
6. Include specific cultural considerations from the profile

Generate a professional {template_type} template that respects the cultural norms and business practices of {cultural_data['country']}.
        """.strip()
        
        return prompt
    
    def _create_system_prompt(self, cultural_data: Dict[str, Any]) -> str:
        """Create system prompt with strict guardrails"""
        return f"""
You are a cultural business communication expert specializing in {cultural_data['country']}.

CRITICAL RULES:
1. Use ONLY the cultural profile data provided
2. DO NOT invent any cultural facts, statistics, or assumptions
3. If information is missing, respond with "INSUFFICIENT DATA" and specify what's needed
4. All cultural references must be backed by the provided profile data
5. Do not make generalizations about the country or people
6. Focus only on business communication and negotiation practices

If the cultural profile lacks specific information for a request, acknowledge this limitation and provide only what can be derived from the available data.

Your response must be professional, respectful, and culturally appropriate based solely on the provided information.
        """.strip()
    
    def _generate_negotiation_tips(self, cultural_profile: CulturalProfile) -> List[str]:
        """Generate negotiation tips from cultural profile"""
        tips = []
        
        if cultural_profile.negotiation_style:
            style = cultural_profile.negotiation_style
            
            # Extract key points from negotiation style
            if isinstance(style, dict):
                for key, value in style.items():
                    if isinstance(value, list):
                        tips.extend([f"{key}: {item}" for item in value[:3]])  # Limit to 3 items
                    elif isinstance(value, str):
                        tips.append(f"{key}: {value}")
        
        # Add general tips if no specific ones found
        if not tips:
            tips = [
                "Research local business customs before meetings",
                "Build relationships before discussing business",
                "Be patient and respectful of local pace",
                "Follow up appropriately according to local norms"
            ]
        
        return tips[:5]  # Limit to 5 tips
    
    def _generate_objection_handling(self, cultural_profile: CulturalProfile) -> List[str]:
        """Generate objection handling strategies from cultural profile"""
        strategies = []
        
        if cultural_profile.do_dont:
            do_dont = cultural_profile.do_dont
            
            # Extract relevant points from do/dont
            if isinstance(do_dont, dict):
                if "don't" in do_dont:
                    dont_items = do_dont["don't"]
                    if isinstance(dont_items, list):
                        strategies.extend([f"Avoid: {item}" for item in dont_items[:2]])
                
                if "do" in do_dont:
                    do_items = do_dont["do"]
                    if isinstance(do_items, list):
                        strategies.extend([f"Practice: {item}" for item in do_items[:2]])
        
        # Add general strategies if no specific ones found
        if not strategies:
            strategies = [
                "Listen actively to understand objections",
                "Provide data to support your position",
                "Offer alternative solutions when possible",
                "Maintain respectful tone throughout"
            ]
        
        return strategies[:4]  # Limit to 4 strategies
    
    def _create_explainability_bundle(
        self,
        tenant_id: UUID,
        input_data: CulturalInput,
        cultural_profile: CulturalProfile,
        templates: List[CulturalTemplate]
    ) -> ExplainabilityBundle:
        """Create comprehensive explainability bundle"""
        
        # Data used
        data_used = []
        
        # Add input data source
        data_used.append(make_data_used_item(
            source_name="user_input",
            dataset="cultural_strategy_input",
            coverage=f"{input_data.destination_country} - {input_data.buyer_type}",
            confidence=1.0
        ))
        
        # Add cultural profile source
        data_used.append(make_data_used_item(
            source_name="cultural_profiles",
            dataset="cultural_business_practices",
            coverage=f"{cultural_profile.country} cultural profile",
            confidence=0.8
        ))
        
        # Add LLM source
        data_used.append(make_data_used_item(
            source_name="gemini_llm",
            dataset="cultural_template_generation",
            coverage=f"Generated {len(templates)} templates",
            confidence=0.6  # Lower confidence for LLM-generated content
        ))
        
        # Assumptions
        assumptions = [
            f"Cultural profile for {cultural_profile.country} is accurate and up-to-date",
            "Generated templates follow provided cultural guidelines",
            "LLM respects guardrails and uses only provided data",
            "Business context is accurately represented in input"
        ]
        
        if not cultural_profile.negotiation_style:
            assumptions.append("Limited negotiation style information available")
        
        if not cultural_profile.do_dont:
            assumptions.append("Limited do/dont guidance available")
        
        # Confidence calculation
        confidence = self._calculate_confidence(cultural_profile, templates)
        confidence_rationale = f"Base confidence 0.4 + profile completeness + template generation = {confidence:.1f}"
        
        # Action plan
        action_plan = [
            "Review generated templates for cultural appropriateness",
            "Customize templates with specific deal details",
            "Test templates with local cultural experts if possible",
            "Monitor response and adjust approach as needed"
        ]
        
        # Limitations
        limitations = [
            "Templates are generated based on available cultural profile data",
            "LLM may not capture all cultural nuances",
            "Individual preferences may vary from cultural norms",
            "Templates should be reviewed by local experts when possible"
        ]
        
        if not cultural_profile.negotiation_style:
            limitations.append("Limited negotiation style guidance available")
        
        return ExplainabilityBundle(
            data_used=data_used,
            assumptions=assumptions,
            confidence=confidence,
            confidence_rationale=confidence_rationale,
            action_plan=action_plan,
            limitations=limitations,
            computation_method="LLM-assisted cultural template generation with guardrails",
            missing_fields=[]
        )
    
    def _calculate_confidence(
        self, 
        cultural_profile: CulturalProfile, 
        templates: List[CulturalTemplate]
    ) -> float:
        """Calculate confidence score based on data availability"""
        confidence = 0.4  # Base confidence
        
        # Add confidence for cultural profile completeness
        if cultural_profile.negotiation_style:
            confidence += 0.2
        
        if cultural_profile.do_dont:
            confidence += 0.1
        
        if cultural_profile.typical_terms:
            confidence += 0.1
        
        # Add confidence for template generation
        if templates:
            confidence += 0.1
            confidence += min(len(templates) * 0.05, 0.1)  # Up to 0.1 for multiple templates
        
        return min(confidence, 0.8)  # Cap at 0.8 for LLM-based content
    
    def _create_insufficient_data_response(
        self,
        tenant_id: UUID,
        input_data: CulturalInput,
        missing_fields: List[str]
    ) -> CulturalOutput:
        """Create insufficient data response"""
        suggested_steps = [
            f"Provide missing field: {field}" for field in missing_fields
        ]
        
        if "No cultural profile found" in str(missing_fields):
            suggested_steps = [
                f"Create cultural profile for {input_data.destination_country}",
                "Add negotiation style information",
                "Include do/dont guidelines",
                "Add typical business terms"
            ]
        
        # Create insufficient data run
        self.registry.create_insufficient_data_run(
            tenant_id,
            "cultural",
            input_data.dict(),
            missing_fields,
            suggested_steps
        )
        
        return CulturalOutput(
            status="insufficient_data",
            templates=[],
            negotiation_tips=[],
            objection_handling=[],
            referenced_profile_ids=[],
            explainability=ExplainabilityBundle(
                data_used=[],
                assumptions=[f"Missing required data: {', '.join(missing_fields)}"],
                confidence=0.0,
                confidence_rationale="Insufficient data for computation",
                action_plan=suggested_steps,
                limitations=["Insufficient data"],
                computation_method="None - insufficient data",
                missing_fields=missing_fields
            )
        )
