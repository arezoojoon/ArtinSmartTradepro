"""
Phase 5 Cultural Profiles Seed Data
Initial cultural profiles for major trading countries
"""
from uuid import uuid4
from datetime import datetime

def seed_cultural_profiles(db_session):
    """Seed initial cultural profiles for major trading countries"""
    
    profiles = [
        {
            "country": "US",
            "negotiation_style": {
                "approach": "Direct and results-oriented",
                "pace": "Fast-paced",
                "decision_making": "Data-driven",
                "communication": "Explicit and straightforward"
            },
            "do_dont": {
                "do": [
                    "Be punctual and prepared",
                    "Use data to support arguments",
                    "Follow up promptly",
                    "Maintain professional demeanor"
                ],
                "don't": [
                    "Be overly emotional",
                    "Make promises you can't keep",
                    "Waste time with small talk",
                    "Use high-pressure tactics"
                ]
            },
            "typical_terms": {
                "payment_terms": ["Net 30", "Net 60"],
                "contract_formality": "High",
                "relationship_focus": "Transactional",
                "negotiation_timeline": "Weeks to months"
            }
        },
        {
            "country": "CN",
            "negotiation_style": {
                "approach": "Relationship-based and indirect",
                "pace": "Patient and long-term",
                "decision_making": "Consensus-driven",
                "communication": "Indirect and harmonious"
            },
            "do_dont": {
                "do": [
                    "Build relationships before business",
                    "Show respect for hierarchy",
                    "Be patient with decision process",
                    "Use formal titles"
                ],
                "don't": [
                    "Cause public embarrassment",
                    "Rush decision-making",
                    "Be overly direct",
                    "Ignore cultural protocols"
                ]
            },
            "typical_terms": {
                "payment_terms": ["LC", "TT"],
                "contract_formality": "High",
                "relationship_focus": "Long-term partnership",
                "negotiation_timeline": "Months"
            }
        },
        {
            "country": "DE",
            "negotiation_style": {
                "approach": "Analytical and systematic",
                "pace": "Methodical and thorough",
                "decision_making": "Technical and precise",
                "communication": "Formal and detailed"
            },
            "do_dont": {
                "do": [
                    "Come well-prepared with data",
                    "Be punctual and formal",
                    "Address technical details",
                    "Follow established procedures"
                ],
                "don't": [
                    "Be casual or informal",
                    "Make exaggerated claims",
                    "Skip technical details",
                    "Change plans suddenly"
                ]
            },
            "typical_terms": {
                "payment_terms": ["Net 30", "Net 60"],
                "contract_formality": "Very high",
                "relationship_focus": "Quality and reliability",
                "negotiation_timeline": "Weeks to months"
            }
        },
        {
            "country": "JP",
            "negotiation_style": {
                "approach": "Consensus-building and respectful",
                "pace": "Deliberate and patient",
                "decision_making": "Group consensus",
                "communication": "Indirect and polite"
            },
            "do_dont": {
                "do": [
                    "Show respect and humility",
                    "Build group consensus",
                    "Use formal language",
                    "Allow time for consideration"
                ],
                "don't": [
                    "Be confrontational",
                    "Force quick decisions",
                    "Use informal language",
                    "Disrespect hierarchy"
                ]
            },
            "typical_terms": {
                "payment_terms": ["LC", "TT"],
                "contract_formality": "Very high",
                "relationship_focus": "Long-term trust",
                "negotiation_timeline": "Months"
            }
        },
        {
            "country": "AE",
            "negotiation_style": {
                "approach": "Relationship-focused and hospitable",
                "pace": "Flexible but relationship-driven",
                "decision_making": "Personal and hierarchical",
                "communication": "Warm and personal"
            },
            "do_dont": {
                "do": [
                    "Build personal relationships",
                    "Show hospitality and respect",
                    "Be patient with process",
                    "Use formal greetings"
                ],
                "don't": [
                    "Rush relationship building",
                    "Be overly direct",
                    "Ignore religious considerations",
                    "Schedule meetings during prayer times"
                ]
            },
            "typical_terms": {
                "payment_terms": ["LC", "TT", "CAD"],
                "contract_formality": "Medium to high",
                "relationship_focus": "Personal trust",
                "negotiation_timeline": "Weeks to months"
            }
        },
        {
            "country": "IN",
            "negotiation_style": {
                "approach": "Relationship-based and flexible",
                "pace": "Variable and adaptable",
                "decision_making": "Hierarchical but flexible",
                "communication": "Polite and indirect"
            },
            "do_dont": {
                "do": [
                    "Build personal relationships",
                    "Show respect for hierarchy",
                    "Be patient with bureaucracy",
                    "Use formal titles"
                ],
                "don't": [
                    "Be overly direct",
                    "Rush decisions",
                    "Ignore cultural protocols",
                    "Be impatient with delays"
                ]
            },
            "typical_terms": {
                "payment_terms": ["LC", "TT", "DA"],
                "contract_formality": "Medium",
                "relationship_focus": "Long-term partnership",
                "negotiation_timeline": "Months"
            }
        },
        {
            "country": "BR",
            "negotiation_style": {
                "approach": "Relationship-focused and flexible",
                "pace": "Fluid and adaptable",
                "decision_making": "Personal and flexible",
                "communication": "Warm and expressive"
            },
            "do_dont": {
                "do": [
                    "Build personal connections",
                    "Be flexible and creative",
                    "Use informal communication",
                    "Show enthusiasm"
                ],
                "don't": [
                    "Be overly formal",
                    "Rush relationship building",
                    "Ignore personal connections",
                    "Be rigid with terms"
                ]
            },
            "typical_terms": {
                "payment_terms": ["TT", "DA", "OA"],
                "contract_formality": "Medium",
                "relationship_focus": "Personal trust",
                "negotiation_timeline": "Weeks"
            }
        },
        {
            "country": "SA",
            "negotiation_style": {
                "approach": "Relationship-based and respectful",
                "pace": "Patient and formal",
                "decision_making": "Hierarchical and consensus-driven",
                "communication": "Formal and polite"
            },
            "do_dont": {
                "do": [
                    "Build personal relationships",
                    "Show respect for traditions",
                    "Be patient with process",
                    "Use formal communication"
                ],
                "don't": [
                    "Be overly direct",
                    "Rush decisions",
                    "Ignore religious protocols",
                    "Schedule meetings during prayer times"
                ]
            },
            "typical_terms": {
                "payment_terms": ["LC", "TT"],
                "contract_formality": "High",
                "relationship_focus": "Trust and respect",
                "negotiation_timeline": "Months"
            }
        }
    ]
    
    # Create cultural profiles
    for profile_data in profiles:
        # Check if profile already exists
        existing = db_session.query(CulturalProfile).filter(
            CulturalProfile.country == profile_data["country"]
        ).first()
        
        if not existing:
            profile = CulturalProfile(
                id=uuid4(),
                tenant_id=uuid4(),  # Default tenant - in production this would be tenant-specific
                country=profile_data["country"],
                negotiation_style=profile_data["negotiation_style"],
                do_dont=profile_data["do_dont"],
                typical_terms=profile_data["typical_terms"],
                created_at=datetime.utcnow()
            )
            db_session.add(profile)
    
    db_session.commit()
    print(f"Seeded {len(profiles)} cultural profiles")
