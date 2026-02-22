"""
Vision/Voice Router - AI-powered Document and Voice Processing
Phase 6 Enhancement - Vision and voice parsing for CRM automation
"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_active_user
from app.services.vision_voice import get_vision_voice_service

router = APIRouter()


# Pydantic Models
class DocumentProcessingResponse(BaseModel):
    document_type: str
    confidence: float
    extracted_text: str
    entities: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_time: float


class AudioProcessingResponse(BaseModel):
    transcript: str
    confidence: float
    language: str
    duration: float
    speaker_count: int
    entities: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class CRMRecordResponse(BaseModel):
    action: str
    record_type: str
    record_id: Optional[str]
    confidence: float
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    reason: Optional[str]


@router.post("/process-document", response_model=DocumentProcessingResponse, summary="Process Document Image")
async def process_document(
    file: UploadFile = File(...),
    document_type_hint: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DocumentProcessingResponse:
    """
    Process document image using AI vision
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Get vision/voice service
    vision_service = get_vision_voice_service(db)
    
    try:
        # Read file content
        image_data = await file.read()
        
        # Process document
        parsed_doc = await vision_service.process_document(
            image_data=image_data,
            tenant_id=str(tenant_id),
            document_type_hint=document_type_hint
        )
        
        return DocumentProcessingResponse(
            document_type=parsed_doc.document_type,
            confidence=parsed_doc.confidence,
            extracted_text=parsed_doc.extracted_text,
            entities=parsed_doc.entities,
            metadata=parsed_doc.metadata,
            processing_time=parsed_doc.processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.post("/process-audio", response_model=AudioProcessingResponse, summary="Process Audio File")
async def process_audio(
    file: UploadFile = File(...),
    language_hint: Optional[str] = Form("en"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AudioProcessingResponse:
    """
    Process audio file using AI speech-to-text
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Validate file type
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # Get vision/voice service
    vision_service = get_vision_voice_service(db)
    
    try:
        # Read file content
        audio_data = await file.read()
        
        # Process audio
        transcribed_audio = await vision_service.process_audio(
            audio_data=audio_data,
            tenant_id=str(tenant_id),
            language_hint=language_hint
        )
        
        return AudioProcessingResponse(
            transcript=transcribed_audio.transcript,
            confidence=transcribed_audio.confidence,
            language=transcribed_audio.language,
            duration=transcribed_audio.duration,
            speaker_count=transcribed_audio.speaker_count,
            entities=transcribed_audio.entities,
            metadata=transcribed_audio.metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")


@router.post("/create-crm-record", response_model=CRMRecordResponse, summary="Create CRM Record from Document")
async def create_crm_record_from_document(
    file: UploadFile = File(...),
    document_type_hint: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CRMRecordResponse:
    """
    Process document and create corresponding CRM record
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Get vision/voice service
    vision_service = get_vision_voice_service(db)
    
    try:
        # Read file content
        image_data = await file.read()
        
        # Process document
        parsed_doc = await vision_service.process_document(
            image_data=image_data,
            tenant_id=str(tenant_id),
            document_type_hint=document_type_hint
        )
        
        # Create CRM record
        crm_result = await vision_service.create_crm_record_from_document(
            parsed_doc=parsed_doc,
            tenant_id=str(tenant_id)
        )
        
        return CRMRecordResponse(**crm_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CRM record creation failed: {str(e)}")


@router.post("/create-crm-record-audio", response_model=CRMRecordResponse, summary="Create CRM Record from Audio")
async def create_crm_record_from_audio(
    file: UploadFile = File(...),
    language_hint: Optional[str] = Form("en"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CRMRecordResponse:
    """
    Process audio and create corresponding CRM record
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Validate file type
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # Get vision/voice service
    vision_service = get_vision_voice_service(db)
    
    try:
        # Read file content
        audio_data = await file.read()
        
        # Process audio
        transcribed_audio = await vision_service.process_audio(
            audio_data=audio_data,
            tenant_id=str(tenant_id),
            language_hint=language_hint
        )
        
        # Create CRM record
        crm_result = await vision_service.create_crm_record_from_audio(
            transcribed_audio=transcribed_audio,
            tenant_id=str(tenant_id)
        )
        
        return CRMRecordResponse(**crm_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CRM record creation failed: {str(e)}")


@router.get("/document-types", summary="Get Supported Document Types")
async def get_supported_document_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get list of supported document types for processing
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    document_types = [
        {
            "type": "business_card",
            "display_name": "Business Card",
            "description": "Extract contact information from business cards",
            "supported_formats": ["jpg", "jpeg", "png", "bmp", "tiff"],
            "extracted_fields": ["name", "title", "company", "email", "phone", "address"],
            "crm_action": "create_or_update_contact"
        },
        {
            "type": "invoice",
            "display_name": "Invoice",
            "description": "Extract invoice details and amounts",
            "supported_formats": ["jpg", "jpeg", "png", "pdf"],
            "extracted_fields": ["invoice_number", "date", "due_date", "amount", "vendor", "customer"],
            "crm_action": "create_invoice_record"
        },
        {
            "type": "contract",
            "display_name": "Contract",
            "description": "Extract contract terms and parties",
            "supported_formats": ["jpg", "jpeg", "png", "pdf"],
            "extracted_fields": ["contract_number", "parties", "effective_date", "expiry_date", "terms"],
            "crm_action": "create_contract_record"
        },
        {
            "type": "purchase_order",
            "display_name": "Purchase Order",
            "description": "Extract PO details and line items",
            "supported_formats": ["jpg", "jpeg", "png", "pdf"],
            "extracted_fields": ["po_number", "vendor", "items", "total_amount", "delivery_date"],
            "crm_action": "create_po_record"
        },
        {
            "type": "receipt",
            "display_name": "Receipt",
            "description": "Extract receipt information and expenses",
            "supported_formats": ["jpg", "jpeg", "png"],
            "extracted_fields": ["date", "amount", "vendor", "items", "payment_method"],
            "crm_action": "create_expense_record"
        }
    ]
    
    return {
        "document_types": document_types,
        "total_count": len(document_types),
        "supported_image_formats": ["jpg", "jpeg", "png", "bmp", "tiff"],
        "supported_audio_formats": ["mp3", "wav", "m4a", "flac", "ogg"],
        "max_file_size_mb": 10,
        "processing_languages": ["en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko"]
    }


@router.get("/processing-history", summary="Get Processing History")
async def get_processing_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    document_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get history of document and audio processing
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Mock processing history data
    # In production, this would query a processing history table
    processing_history = [
        {
            "id": "1",
            "type": "document",
            "document_type": "business_card",
            "file_name": "john_smith_card.jpg",
            "confidence": 0.92,
            "processing_time": 2.3,
            "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "crm_action": "created_contact",
            "crm_record_id": "contact_123"
        },
        {
            "id": "2",
            "type": "audio",
            "document_type": "voice_note",
            "file_name": "followup_call.mp3",
            "confidence": 0.87,
            "processing_time": 5.1,
            "created_at": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
            "crm_action": "follow_up_created",
            "crm_record_id": "task_456"
        },
        {
            "id": "3",
            "type": "document",
            "document_type": "invoice",
            "file_name": "invoice_789.pdf",
            "confidence": 0.95,
            "processing_time": 3.7,
            "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "crm_action": "invoice_processed",
            "crm_record_id": None
        },
        {
            "id": "4",
            "type": "document",
            "document_type": "business_card",
            "file_name": "jane_doe_card.png",
            "confidence": 0.89,
            "processing_time": 1.8,
            "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "crm_action": "updated_contact",
            "crm_record_id": "contact_789"
        }
    ]
    
    # Filter by document type if specified
    if document_type:
        processing_history = [
            item for item in processing_history 
            if item["document_type"] == document_type
        ]
    
    # Apply pagination
    total = len(processing_history)
    paginated_history = processing_history[offset:offset + limit]
    
    return {
        "history": paginated_history,
        "total_count": total,
        "limit": limit,
        "offset": offset,
        "document_types": list(set(item["document_type"] for item in processing_history))
    }


@router.get("/processing-stats", summary="Get Processing Statistics")
async def get_processing_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get processing statistics for the specified period
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    # Mock statistics data
    # In production, this would calculate from actual processing history
    stats = {
        "period_days": days,
        "total_processed": 45,
        "document_processed": 32,
        "audio_processed": 13,
        "avg_confidence": 0.91,
        "avg_processing_time": 3.2,
        "crm_records_created": 28,
        "success_rate": 0.93,
        "document_type_breakdown": {
            "business_card": 18,
            "invoice": 8,
            "contract": 4,
            "receipt": 2
        },
        "daily_stats": [
            {
                "date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "processed": np.random.randint(0, 5),
                "avg_confidence": np.random.uniform(0.85, 0.95)
            }
            for i in range(days)
        ],
        "language_distribution": {
            "en": 38,
            "es": 4,
            "fr": 2,
            "de": 1
        }
    }
    
    return stats


@router.get("/supported-languages", summary="Get Supported Languages")
async def get_supported_languages(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get list of supported languages for audio processing
    """
    tenant_id = getattr(current_user, "current_tenant_id", getattr(current_user, "tenant_id", None))
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context found")
    
    languages = [
        {
            "code": "en",
            "name": "English",
            "display_name": "English",
            "confidence": 0.95,
            "supported": True
        },
        {
            "code": "es",
            "name": "Spanish",
            "display_name": "Español",
            "confidence": 0.90,
            "supported": True
        },
        {
            "code": "fr",
            "name": "French",
            "display_name": "Français",
            "confidence": 0.88,
            "supported": True
        },
        {
            "code": "de",
            "name": "German",
            "display_name": "Deutsch",
            "confidence": 0.87,
            "supported": True
        },
        {
            "code": "it",
            "name": "Italian",
            "display_name": "Italiano",
            "confidence": 0.85,
            "supported": True
        },
        {
            "code": "pt",
            "name": "Portuguese",
            "display_name": "Português",
            "confidence": 0.83,
            "supported": True
        },
        {
            "code": "zh",
            "name": "Chinese",
            "display_name": "中文",
            "confidence": 0.82,
            "supported": True
        },
        {
            "code": "ja",
            "name": "Japanese",
            "display_name": "日本語",
            "confidence": 0.80,
            "supported": True
        },
        {
            "code": "ko",
            "name": "Korean",
            "display_name": "한국어",
            "confidence": 0.78,
            "supported": True
        },
        {
            "code": "ru",
            "name": "Russian",
            "display_name": "Русский",
            "confidence": 0.75,
            "supported": False
        },
        {
            "code": "ar",
            "name": "Arabic",
            "display_name": "العربية",
            "confidence": 0.70,
            "supported": False
        }
    ]
    
    return {
        "languages": languages,
        "total_count": len(languages),
        "supported_count": len([lang for lang in languages if lang["supported"]]),
        "default_language": "en"
    }
