"""
Hunter Phase 4 Scoring Engine v1
Explainable weights + deterministic signals
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from ..models.hunter_phase4 import HunterLead, HunterLeadIdentity, HunterEvidence
from ..services.hunter_repository import HunterRepository

@dataclass
class ScoringSignal:
    """Individual scoring signal with explanation"""
    name: str
    score: int
    max_score: int
    explanation: str
    evidence_count: int = 0
    raw_evidence: Optional[Dict[str, Any]] = None

@dataclass
class ScoringResult:
    """Complete scoring result with breakdown"""
    total_score: int
    max_score: int
    signals: List[ScoringSignal]
    risk_flags: List[str]
    breakdown: Dict[str, Any]

class HunterScoringEngine:
    """
    Lead scoring engine with explainable, deterministic signals
    Only scores based on available evidence - no guessing
    """
    
    def __init__(self, repo: HunterRepository):
        self.repo = repo
    
    def score_lead(self, tenant_id: str, lead_id: str, profile_weights: Optional[Dict[str, Any]] = None) -> ScoringResult:
        """
        Score a lead using deterministic signals
        
        Args:
            tenant_id: Tenant ID for RLS
            lead_id: Lead ID to score
            profile_weights: Optional custom weights (uses default if None)
            
        Returns:
            ScoringResult with total score and breakdown
        """
        # Get lead with all evidence
        lead = self.repo.get_lead_with_details(tenant_id, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        # Get scoring profile (default if none provided)
        if not profile_weights:
            default_profile = self.repo.get_default_scoring_profile(tenant_id)
            if default_profile:
                profile_weights = default_profile.weights
            else:
                profile_weights = self._get_default_weights()
        
        # Group evidence by field for easier access
        evidence_by_field = self._group_evidence_by_field(lead.evidence)
        identities_by_type = self._group_identities_by_type(lead.identities)
        
        # Calculate signals
        signals = []
        risk_flags = []
        
        # Signal E: Market Demand (0-20)
        demand_signal = self._calculate_market_demand(evidence_by_field, profile_weights)
        signals.append(demand_signal)
        
        # Signal F: Payment Risk (0-10)
        risk_signal = self._calculate_payment_risk(lead.country, evidence_by_field, profile_weights)
        signals.append(risk_signal)
        
        # Calculate risk flags
        risk_flags = self._calculate_risk_flags(lead, identities_by_type, evidence_by_field, profile_weights)
        
        # Calculate total score
        total_score = sum(signal.score for signal in signals)
        max_score = sum(signal.max_score for signal in signals)
        
        # Create breakdown
        breakdown = {
            "version": "3.0",
            "decision_summary": self._generate_decision_summary(signals, risk_flags),
            "signals": [
                {
                    "name": signal.name,
                    "score": signal.score,
                    "max_score": signal.max_score,
                    "explanation": signal.explanation,
                    "evidence_count": signal.evidence_count
                }
                for signal in signals
            ],
            "risk_flags": risk_flags,
            "total_possible": max_score,
            "score_percentage": round((total_score / max_score * 100), 1) if max_score > 0 else 0
        }
        
        return ScoringResult(
            total_score=total_score,
            max_score=max_score,
            signals=signals,
            risk_flags=risk_flags,
            breakdown=breakdown
        )
    
    def _group_evidence_by_field(self, evidence_list: List[HunterEvidence]) -> Dict[str, List[HunterEvidence]]:
        """Group evidence by field_name"""
        grouped = {}
        for evidence in evidence_list:
            if evidence.field_name not in grouped:
                grouped[evidence.field_name] = []
            grouped[evidence.field_name].append(evidence)
        return grouped
    
    def _group_identities_by_type(self, identity_list: List[HunterLeadIdentity]) -> Dict[str, List[HunterLeadIdentity]]:
        """Group identities by type"""
        grouped = {}
        for identity in identity_list:
            if identity.type not in grouped:
                grouped[identity.type] = []
            grouped[identity.type].append(identity)
        return grouped
    
    def _calculate_identity_completeness(self, identities_by_type: Dict[str, List], evidence_by_field: Dict[str, List], weights: Dict[str, Any]) -> ScoringSignal:
        """Signal A: Identity completeness (0-30)"""
        score = 0
        max_score = 30
        explanations = []
        
        # +10 if website exists
        if 'domain' in identities_by_type or 'website' in evidence_by_field:
            score += 10
            explanations.append("Has website/domain")
        
        # +10 if at least 1 verified email evidence
        email_evidence = evidence_by_field.get('email', [])
        if email_evidence:
            score += 10
            explanations.append(f"Has {len(email_evidence)} email(s)")
        
        # +10 if at least 1 phone evidence
        phone_evidence = evidence_by_field.get('phone', [])
        if phone_evidence:
            score += 10
            explanations.append(f"Has {len(phone_evidence)} phone number(s)")
        
        return ScoringSignal(
            name="Identity Completeness",
            score=score,
            max_score=max_score,
            explanation="; ".join(explanations) if explanations else "No identity data",
            evidence_count=len(identities_by_type) + len(evidence_by_field)
        )
    
    def _calculate_country_priority(self, country: str, weights: Dict[str, Any]) -> ScoringSignal:
        """Signal B: Country priority (0-20)"""
        score = 0
        max_score = 20
        
        # Get priority countries from profile
        priority_countries = weights.get('priority_countries', [])
        
        if country in priority_countries:
            score = 20
            explanation = f"Country {country} is in priority list"
        else:
            explanation = f"Country {country} not in priority list"
        
        return ScoringSignal(
            name="Country Priority",
            score=score,
            max_score=max_score,
            explanation=explanation,
            evidence_count=1
        )
    
    def _calculate_company_type_hint(self, evidence_by_field: Dict[str, List], weights: Dict[str, Any]) -> ScoringSignal:
        """Signal C: Company type hint (0-10)"""
        score = 0
        max_score = 10
        explanations = []
        matched_keywords = []
        
        # B2B/importer/distributor keywords
        b2b_keywords = [
            'b2b', 'wholesale', 'distributor', 'supplier', 'manufacturer',
            'import', 'export', 'trade', 'logistics', 'procurement',
            'business to business', 'bulk', 'volume'
        ]
        
        # Check in company name hints
        company_hints = evidence_by_field.get('company_name_hint', [])
        for hint in company_hints:
            hint_lower = hint.lower()
            for keyword in b2b_keywords:
                if keyword in hint_lower:
                    score += 5
                    matched_keywords.append(keyword)
                    explanations.append(f"Company hint '{hint}' contains '{keyword}'")
                    break
        
        # Check in industry hints
        industry_hints = evidence_by_field.get('industry_hint', [])
        for hint in industry_hints:
            hint_lower = hint.lower()
            for keyword in b2b_keywords:
                if keyword in hint_lower:
                    score += 3
                    if keyword not in matched_keywords:
                        matched_keywords.append(keyword)
                    explanations.append(f"Industry hint '{hint}' contains '{keyword}'")
                    break
        
        # Cap at max_score
        score = min(score, max_score)
        
        return ScoringSignal(
            name="Company Type Hint",
            score=score,
            max_score=max_score,
            explanation="; ".join(explanations) if explanations else "No B2B indicators found",
            evidence_count=len(company_hints) + len(industry_hints),
            raw_evidence={"matched_keywords": matched_keywords}
        )
    
    def _calculate_data_freshness(self, evidence_by_field: Dict[str, List], weights: Dict[str, Any]) -> ScoringSignal:
        """Signal D: Data freshness (0-10)"""
        score = 0
        max_score = 10
        
        # Find the most recent evidence
        most_recent = None
        for evidence_list in evidence_by_field.values():
            for evidence in evidence_list:
                if most_recent is None or evidence.collected_at > most_recent:
                    most_recent = evidence.collected_at
        
        if most_recent:
            days_ago = (datetime.utcnow() - most_recent).days
            
            if days_ago <= 30:
                score = 10
                explanation = f"Data collected {days_ago} days ago (recent)"
            elif days_ago <= 90:
                score = 5
                explanation = f"Data collected {days_ago} days ago (moderately recent)"
            else:
                score = 0
                explanation = f"Data collected {days_ago} days ago (stale)"
        else:
            explanation = "No evidence data available"
        
        return ScoringSignal(
            name="Data Freshness",
            score=score,
            max_score=max_score,
            explanation=explanation,
            evidence_count=len(evidence_by_field)
        )
    
    def _calculate_risk_flags(self, lead: HunterLead, identities_by_type: Dict[str, List], evidence_by_field: Dict[str, List], weights: Dict[str, Any]) -> List[str]:
        """Calculate risk flags (negative scores)"""
        risk_flags = []
        
        # Risk countries
        risk_countries = weights.get('risk_countries', [])
        if lead.country in risk_countries:
            risk_flags.append(f"High risk country: {lead.country}")
        
        # Free email domains
        free_email_domains = weights.get('free_email_domains', ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'])
        email_identities = identities_by_type.get('email', [])
        
        for identity in email_identities:
            domain = identity.value.split('@')[-1].lower()
            if domain in free_email_domains:
                risk_flags.append(f"Uses free email domain: {domain}")
                break  # Only add once
        
        # No website evidence
        if 'website' not in evidence_by_field and 'domain' not in identities_by_type:
            risk_flags.append("No website or domain evidence")
        
        # Very old data
        most_recent = None
        for evidence_list in evidence_by_field.values():
            for evidence in evidence_list:
                if most_recent is None or evidence.collected_at > most_recent:
                    most_recent = evidence.collected_at
        
        if most_recent and (datetime.utcnow() - most_recent).days > 180:
            risk_flags.append("Data is over 6 months old")
        
        return risk_flags
    
    def _calculate_market_demand(self, evidence_by_field: Dict[str, List[HunterEvidence]], weights: Dict[str, Any]) -> ScoringSignal:
        """Signal E: Market Demand (0-20) based on trade volumes"""
        score = 0
        max_score = 20
        explanations = []
        
        # Look for trade data evidence (from un_comtrade)
        trade_evidence = evidence_by_field.get('trade_data', [])
        for ev in trade_evidence:
            raw = ev.raw or {}
            volume = raw.get('value_usd', 0)
            growth = raw.get('growth_pct', 0)
            
            if volume > 100_000_000:
                score += 10
                explanations.append(f"Huge market volume identified: ${volume/1e9:.1f}B")
            elif volume > 10_000_000:
                score += 5
                explanations.append(f"Significant market volume: ${volume/1e6:.1f}M")
                
            if growth > 10:
                score += 10
                explanations.append(f"High growth market (+{growth}%)")
            elif growth > 0:
                score += 5
                explanations.append(f"Growing market (+{growth}%)")
        
        score = min(score, max_score)
        return ScoringSignal(
            name="Market Demand",
            score=score,
            max_score=max_score,
            explanation="; ".join(explanations) if explanations else "No trade data volume records",
            evidence_count=len(trade_evidence)
        )

    def _calculate_payment_risk(self, country: str, evidence_by_field: Dict[str, List[HunterEvidence]], weights: Dict[str, Any]) -> ScoringSignal:
        """Signal F: Payment Risk (0-10)"""
        score = 10  # Start with full score, deduct for risk
        max_score = 10
        explanations = ["No major payment risks identified"]
        
        risk_countries = weights.get('risk_countries', [])
        if country in risk_countries:
            score -= 7
            explanations = [f"Direct risk: {country} is in restricted/risk list"]
        
        # Optionally check Phase 5 payment behavior if linked (TBD)
        
        return ScoringSignal(
            name="Payment Risk",
            score=max(0, score),
            max_score=max_score,
            explanation="; ".join(explanations),
            evidence_count=1
        )

    def _generate_decision_summary(self, signals: List[ScoringSignal], risk_flags: List[str]) -> str:
        """Generate a GPT-style decision summary for the UI"""
        if not signals: return "Insufficient data for assessment."
        
        score_sum = sum(s.score for s in signals)
        max_sum = sum(s.max_score for s in signals)
        pct = (score_sum / max_sum * 100) if max_sum > 0 else 0
        
        if risk_flags:
            return f"Caution: Lead has {len(risk_flags)} risk flags. Overall match is {pct:.0f}% but requires compliance review."
        
        if pct > 80:
             return "Strong Match: High market alignment and verified contact data. Priority lead."
        if pct > 50:
             return "Moderate Match: Good potential, but requires further background enrichment."
        
        return "Low Match: Limited evidence or weak market signals."

    def _get_default_weights(self) -> Dict[str, Any]:
        """Get default scoring weights"""
        return {
            "priority_countries": ["US", "CA", "GB", "DE", "FR", "AU", "JP", "SG"],
            "risk_countries": ["IR", "KP", "SY", "SS", "AF"],
            "free_email_domains": ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"],
            "signal_weights": {
                "identity_completeness": 30,
                "country_priority": 20,
                "company_type_hint": 10,
                "data_freshness": 10
            }
        }
