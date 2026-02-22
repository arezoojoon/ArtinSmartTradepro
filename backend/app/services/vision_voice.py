"""
Vision and Voice Parsing Service
Phase 6 Enhancement - AI-powered document and voice processing for CRM
"""
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import base64
import io
from PIL import Image
import numpy as np
from dataclasses import dataclass

from app.models.crm import CRMCompany, CRMContact, CRMDeal
from app.models.tenant import Tenant
from app.config import get_settings


@dataclass
class ParsedDocument:
    """Parsed document information"""
    document_type: str
    confidence: float
    extracted_text: str
    entities: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_time: float


@dataclass
class TranscribedAudio:
    """Transcribed audio information"""
    transcript: str
    confidence: float
    language: str
    duration: float
    speaker_count: int
    entities: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class VisionVoiceService:
    """Service for AI-powered vision and voice processing"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gemini_api_key = get_settings().GEMINI_API_KEY
        self.openai_api_key = get_settings().OPENAI_API_KEY
        
        # Document type patterns
        self.document_patterns = {
            "business_card": {
                "keywords": ["email", "phone", "address", "company", "title"],
                "fields": ["name", "title", "company", "email", "phone", "address"]
            },
            "invoice": {
                "keywords": ["invoice", "bill", "amount", "due", "payment", "total"],
                "fields": ["invoice_number", "date", "due_date", "amount", "vendor", "customer"]
            },
            "contract": {
                "keywords": ["contract", "agreement", "terms", "conditions", "party"],
                "fields": ["contract_number", "parties", "effective_date", "expiry_date", "terms"]
            },
            "purchase_order": {
                "keywords": ["purchase order", "PO", "order", "quantity", "price"],
                "fields": ["po_number", "vendor", "items", "total_amount", "delivery_date"]
            }
        }
        
        # Entity patterns
        self.entity_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            "currency": r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
            "company": r'\b(?:Inc|Corp|LLC|Ltd|Co|Company)\b',
            "address": r'\b\d+\s+[\w\s]+(?:St|Ave|Rd|Blvd|Dr)\b'
        }
    
    async def process_document(
        self,
        image_data: bytes,
        tenant_id: str,
        document_type_hint: Optional[str] = None
    ) -> ParsedDocument:
        """
        Process document image using AI vision
        
        Args:
            image_data: Raw image bytes
            tenant_id: Tenant ID for context
            document_type_hint: Optional hint about document type
        """
        start_time = datetime.utcnow()
        
        try:
            # Convert image to base64 for API
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Call Gemini Vision API
            extracted_text = await self._extract_text_from_image(image_base64)
            
            # Detect document type
            detected_type = await self._detect_document_type(extracted_text, document_type_hint)
            
            # Extract entities
            entities = await self._extract_entities(extracted_text, detected_type)
            
            # Structure extracted data
            structured_data = await self._structure_document_data(
                extracted_text, detected_type, entities
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ParsedDocument(
                document_type=detected_type,
                confidence=self._calculate_confidence(extracted_text, entities),
                extracted_text=extracted_text,
                entities=entities,
                metadata={
                    "structured_data": structured_data,
                    "processing_time": processing_time,
                    "tenant_id": tenant_id,
                    "processed_at": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            return ParsedDocument(
                document_type="error",
                confidence=0.0,
                extracted_text="",
                entities=[],
                metadata={"error": str(e)},
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def process_audio(
        self,
        audio_data: bytes,
        tenant_id: str,
        language_hint: Optional[str] = "en"
    ) -> TranscribedAudio:
        """
        Process audio using AI speech-to-text
        
        Args:
            audio_data: Raw audio bytes
            tenant_id: Tenant ID for context
            language_hint: Language hint for transcription
        """
        start_time = datetime.utcnow()
        
        try:
            # Convert audio to base64 for API
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Call speech-to-text API
            transcript = await self._transcribe_audio(audio_base64, language_hint)
            
            # Detect language
            detected_language = await self._detect_language(transcript)
            
            # Extract entities from transcript
            entities = await self._extract_entities(transcript, "voice")
            
            # Estimate duration (mock calculation)
            duration = len(audio_data) / 16000  # Assuming 16kHz sample rate
            
            # Detect speaker count (mock calculation)
            speaker_count = await self._detect_speakers(transcript)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return TranscribedAudio(
                transcript=transcript,
                confidence=self._calculate_transcription_confidence(transcript),
                language=detected_language,
                duration=duration,
                speaker_count=speaker_count,
                entities=entities,
                metadata={
                    "processing_time": processing_time,
                    "tenant_id": tenant_id,
                    "processed_at": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            return TranscribedAudio(
                transcript="",
                confidence=0.0,
                language="unknown",
                duration=0.0,
                speaker_count=0,
                entities=[],
                metadata={"error": str(e)},
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def _extract_text_from_image(self, image_base64: str) -> str:
        """Extract text from image using Gemini Vision API"""
        # Mock implementation - in production, this would call Gemini Vision API
        mock_text = """
        John Smith
        Senior Sales Manager
        ABC Trading Corporation
        123 Business Ave, Suite 100
        New York, NY 10001
        Email: john.smith@abctrading.com
        Phone: (212) 555-0123
        Website: www.abctrading.com
        """
        
        return mock_text.strip()
    
    async def _detect_document_type(self, text: str, hint: Optional[str]) -> str:
        """Detect document type from text content"""
        if hint and hint in self.document_patterns:
            return hint
        
        # Score each document type based on keyword matches
        scores = {}
        for doc_type, pattern in self.document_patterns.items():
            score = 0
            for keyword in pattern["keywords"]:
                if keyword.lower() in text.lower():
                    score += 1
            scores[doc_type] = score
        
        # Return highest scoring type
        if scores:
            return max(scores, key=scores.get)
        
        return "unknown"
    
    async def _extract_entities(self, text: str, context: str) -> List[Dict[str, Any]]:
        """Extract entities from text using patterns and AI"""
        entities = []
        
        # Extract using regex patterns
        import re
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "type": entity_type,
                    "value": match,
                    "confidence": 0.8,
                    "context": context
                })
        
        # Extract structured entities for specific document types
        if context == "business_card":
            entities.extend(await self._extract_business_card_entities(text))
        elif context == "invoice":
            entities.extend(await self._extract_invoice_entities(text))
        elif context == "voice":
            entities.extend(await self._extract_voice_entities(text))
        
        return entities
    
    async def _extract_business_card_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities specific to business cards"""
        entities = []
        lines = text.strip().split('\n')
        
        # Extract name (usually first line)
        if lines:
            entities.append({
                "type": "name",
                "value": lines[0].strip(),
                "confidence": 0.9,
                "context": "business_card"
            })
        
        # Extract title (usually second line)
        if len(lines) > 1:
            entities.append({
                "type": "title",
                "value": lines[1].strip(),
                "confidence": 0.8,
                "context": "business_card"
            })
        
        # Extract company name
        for line in lines:
            if any(keyword in line.lower() for keyword in ["corp", "inc", "llc", "ltd", "company"]):
                entities.append({
                    "type": "company",
                    "value": line.strip(),
                    "confidence": 0.85,
                    "context": "business_card"
                })
                break
        
        return entities
    
    async def _extract_invoice_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities specific to invoices"""
        entities = []
        
        # Extract invoice number
        import re
        invoice_patterns = [
            r'Invoice[:\s#]*\s*([A-Z0-9-]+)',
            r'INV[:\s#]*\s*([A-Z0-9-]+)',
            r'Bill[:\s#]*\s*([A-Z0-9-]+)'
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities.append({
                    "type": "invoice_number",
                    "value": match.group(1),
                    "confidence": 0.9,
                    "context": "invoice"
                })
                break
        
        # Extract total amount
        amount_patterns = [
            r'Total[:\s]*\$?([\d,]+\.?\d*)',
            r'Amount[:\s]*\$?([\d,]+\.?\d*)',
            r'\$([\d,]+\.?\d*)'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities.append({
                    "type": "total_amount",
                    "value": matches[-1],  # Take last match (usually the total)
                    "confidence": 0.85,
                    "context": "invoice"
                })
                break
        
        return entities
    
    async def _extract_voice_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities specific to voice transcription"""
        entities = []
        
        # Extract action items
        action_keywords = ["follow up", "call back", "schedule", "meeting", "send", "email"]
        for keyword in action_keywords:
            if keyword in text.lower():
                entities.append({
                    "type": "action_item",
                    "value": keyword,
                    "confidence": 0.7,
                    "context": "voice"
                })
        
        # Extract dates mentioned
        import re
        date_patterns = [
            r'\b(?:next|this)\s+(?:week|month|monday|tuesday|wednesday|thursday|friday)\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:tomorrow|today|yesterday)\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "type": "date_mentioned",
                    "value": match,
                    "confidence": 0.8,
                    "context": "voice"
                })
        
        return entities
    
    async def _structure_document_data(
        self, text: str, doc_type: str, entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Structure extracted data based on document type"""
        structured = {"document_type": doc_type, "raw_text": text}
        
        if doc_type == "business_card":
            # Structure business card data
            for entity in entities:
                if entity["type"] == "name":
                    structured["contact_name"] = entity["value"]
                elif entity["type"] == "title":
                    structured["title"] = entity["value"]
                elif entity["type"] == "company":
                    structured["company_name"] = entity["value"]
                elif entity["type"] == "email":
                    structured["email"] = entity["value"]
                elif entity["type"] == "phone":
                    structured["phone"] = entity["value"]
                elif entity["type"] == "address":
                    structured["address"] = entity["value"]
        
        elif doc_type == "invoice":
            # Structure invoice data
            for entity in entities:
                if entity["type"] == "invoice_number":
                    structured["invoice_number"] = entity["value"]
                elif entity["type"] == "total_amount":
                    structured["total_amount"] = entity["value"]
                elif entity["type"] == "date":
                    structured["invoice_date"] = entity["value"]
        
        return structured
    
    async def _transcribe_audio(self, audio_base64: str, language: str) -> str:
        """Transcribe audio using speech-to-text API"""
        # Mock implementation - in production, this would call OpenAI Whisper or similar
        mock_transcript = """
        Hi, this is John from ABC Trading Corporation. I'm calling to follow up on our proposal 
        for the soybean export deal we discussed last week. I wanted to confirm if you've had 
        a chance to review the terms and if you have any questions about the pricing structure. 
        We're offering competitive rates and can deliver within 2 weeks. Please let me know if 
        you'd like to proceed or if you need any additional information. I can be reached at 
        (212) 555-0123. Thank you and have a great day.
        """
        
        return mock_transcript.strip()
    
    async def _detect_language(self, text: str) -> str:
        """Detect language of transcribed text"""
        # Mock implementation - in production, this would use language detection
        return "en"  # Default to English
    
    async def _detect_speakers(self, transcript: str) -> int:
        """Detect number of speakers in transcript"""
        # Mock implementation - in production, this would use speaker diarization
        return 1  # Default to single speaker
    
    def _calculate_confidence(self, text: str, entities: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for document processing"""
        if not text or not entities:
            return 0.0
        
        # Base confidence from entity count
        entity_confidence = min(len(entities) * 0.1, 0.5)
        
        # Text length confidence
        text_confidence = min(len(text) / 1000, 0.3)
        
        # Pattern matching confidence
        pattern_confidence = 0.2  # Base confidence for pattern matching
        
        return min(entity_confidence + text_confidence + pattern_confidence, 1.0)
    
    def _calculate_transcription_confidence(self, transcript: str) -> float:
        """Calculate confidence score for transcription"""
        if not transcript:
            return 0.0
        
        # Base confidence from transcript quality
        word_count = len(transcript.split())
        
        if word_count < 10:
            return 0.3
        elif word_count < 50:
            return 0.7
        else:
            return 0.9
    
    async def create_crm_record_from_document(
        self, parsed_doc: ParsedDocument, tenant_id: str
    ) -> Dict[str, Any]:
        """Create CRM record from parsed document"""
        try:
            structured_data = parsed_doc.metadata.get("structured_data", {})
            
            if parsed_doc.document_type == "business_card":
                # Create or update contact
                contact_data = {
                    "name": structured_data.get("contact_name"),
                    "title": structured_data.get("title"),
                    "company": structured_data.get("company_name"),
                    "email": structured_data.get("email"),
                    "phone": structured_data.get("phone"),
                    "address": structured_data.get("address"),
                    "source": "vision_parsing",
                    "tenant_id": tenant_id
                }
                
                # Check if contact already exists
                existing_contact = self.db.query(CRMContact).filter(
                    CRMContact.email == structured_data.get("email"),
                    CRMContact.tenant_id == tenant_id
                ).first()
                
                if existing_contact:
                    # Update existing contact
                    for key, value in contact_data.items():
                        if value and key != "tenant_id":
                            setattr(existing_contact, key, value)
                    self.db.commit()
                    
                    return {
                        "action": "updated",
                        "record_type": "contact",
                        "record_id": str(existing_contact.id),
                        "confidence": parsed_doc.confidence
                    }
                else:
                    # Create new contact
                    new_contact = CRMContact(**contact_data)
                    self.db.add(new_contact)
                    self.db.commit()
                    
                    return {
                        "action": "created",
                        "record_type": "contact",
                        "record_id": str(new_contact.id),
                        "confidence": parsed_doc.confidence
                    }
            
            elif parsed_doc.document_type == "invoice":
                # Create invoice record
                invoice_data = {
                    "invoice_number": structured_data.get("invoice_number"),
                    "amount": structured_data.get("total_amount"),
                    "date": structured_data.get("invoice_date"),
                    "source": "vision_parsing",
                    "tenant_id": tenant_id
                }
                
                return {
                    "action": "invoice_processed",
                    "record_type": "invoice",
                    "data": invoice_data,
                    "confidence": parsed_doc.confidence
                }
            
            else:
                return {
                    "action": "no_action",
                    "reason": f"No CRM mapping for document type: {parsed_doc.document_type}",
                    "confidence": parsed_doc.confidence
                }
                
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "confidence": parsed_doc.confidence
            }
    
    async def create_crm_record_from_audio(
        self, transcribed_audio: TranscribedAudio, tenant_id: str
    ) -> Dict[str, Any]:
        """Create CRM record from transcribed audio"""
        try:
            # Extract action items and create follow-up tasks
            action_entities = [e for e in transcribed_audio.entities if e["type"] == "action_item"]
            
            if action_entities:
                # Create follow-up task
                task_data = {
                    "title": f"Follow-up from voice note",
                    "description": transcribed_audio.transcript,
                    "priority": "medium",
                    "due_date": (datetime.utcnow() + timedelta(days=3)).isoformat(),
                    "source": "voice_parsing",
                    "tenant_id": tenant_id,
                    "metadata": {
                        "audio_duration": transcribed_audio.duration,
                        "language": transcribed_audio.language,
                        "confidence": transcribed_audio.confidence
                    }
                }
                
                return {
                    "action": "follow_up_created",
                    "record_type": "task",
                    "data": task_data,
                    "confidence": transcribed_audio.confidence,
                    "action_items": len(action_entities)
                }
            
            else:
                return {
                    "action": "transcript_saved",
                    "record_type": "note",
                    "transcript": transcribed_audio.transcript,
                    "confidence": transcribed_audio.confidence
                }
                
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "confidence": transcribed_audio.confidence
            }


# Helper function to get vision/voice service
def get_vision_voice_service(db: Session) -> VisionVoiceService:
    """Get vision/voice service instance"""
    return VisionVoiceService(db)
