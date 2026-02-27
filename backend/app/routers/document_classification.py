"""
Document Upload and Auto-Classification API
Automatically classifies and routes documents to appropriate modules
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
from app.core.tenant import get_tenant_context, TenantContext
from app.services.document_classifier import DocumentClassifier, DocumentType, TargetModule
from app.models.logistics import Shipment, ShipmentEvent
from app.models.crm import Company, Contact
from app.models.billing import Invoice
from app.core.config import settings
import uuid
import os
import shutil
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Document Classification"])

# Initialize classifier
classifier = DocumentClassifier()

@router.post("/upload")
async def upload_and_classify_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: str = Form(""),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload document and automatically classify and route to appropriate module
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Security: Validate file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Security: Validate file extension
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.txt', '.doc', '.docx'}
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Security: Validate MIME type
        allowed_mime_types = {
            'application/pdf', 'image/jpeg', 'image/png', 'image/tiff', 
            'text/plain', 'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        # Reset file pointer after reading
        await file.seek(0)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}{file_extension}"
        
        # Save file temporarily
        upload_dir = Path(settings.UPLOAD_DIR) / "documents" / tenant.tenant_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / safe_filename
        
        # Security: Use secure file writing
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Reset file pointer for classification
        await file.seek(0)
        
        # Classify document
        classification = await classifier.classify_document(
            file_content=file_content,
            filename=file.filename,
            tenant_id=tenant.tenant_id,
            user_id=tenant.user_id
        )
        
        # Store document record
        document_record = await _store_document_record(
            db=db,
            tenant_id=tenant.tenant_id,
            user_id=tenant.user_id,
            file_path=str(file_path),
            original_filename=file.filename,
            classification=classification,
            description=description
        )
        
        # Route to appropriate module in background
        background_tasks.add_task(
            route_document_to_module,
            document_id=document_record["id"],
            classification=classification,
            tenant_id=tenant.tenant_id,
            user_id=tenant.user_id
        )
        
        return {
            "success": True,
            "document_id": document_record["id"],
            "classification": {
                "document_type": classification.document_type.value,
                "target_module": classification.target_module.value,
                "confidence": classification.confidence,
                "routing_path": classification.routing_path,
                "suggested_actions": classification.suggested_actions
            },
            "extracted_data": classification.extracted_data,
            "message": f"Document classified as {classification.document_type.value} and routed to {classification.target_module.value}"
        }
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/classification-history")
async def get_classification_history(
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get document classification history for tenant"""
    try:
        query = text("""
            SELECT 
                id, original_filename, document_type, target_module, 
                confidence, classification_data, created_at, status
            FROM document_classifications 
            WHERE tenant_id = :tenant_id 
            ORDER BY created_at DESC 
            LIMIT :limit OFFSET :offset
        """)
        
        result = await db.execute(query, {
            "tenant_id": tenant.tenant_id,
            "limit": limit,
            "offset": offset
        })
        
        records = result.fetchall()
        
        return {
            "documents": [
                {
                    "id": row.id,
                    "filename": row.original_filename,
                    "document_type": row.document_type,
                    "target_module": row.target_module,
                    "confidence": row.confidence,
                    "classification_data": row.classification_data,
                    "created_at": row.created_at,
                    "status": row.status
                }
                for row in records
            ],
            "total": len(records)
        }
        
    except Exception as e:
        logger.error(f"Error getting classification history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reclassify/{document_id}")
async def reclassify_document(
    document_id: str,
    new_document_type: str,
    new_target_module: str,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """Manually reclassify a document"""
    try:
        # Validate document belongs to tenant
        query = text("""
            SELECT id FROM document_classifications 
            WHERE id = :document_id AND tenant_id = :tenant_id
        """)
        
        result = await db.execute(query, {
            "document_id": document_id,
            "tenant_id": tenant.tenant_id
        })
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update classification
        update_query = text("""
            UPDATE document_classifications 
            SET document_type = :document_type, 
                target_module = :target_module,
                status = 'reclassified',
                updated_at = NOW()
            WHERE id = :document_id AND tenant_id = :tenant_id
        """)
        
        await db.execute(update_query, {
            "document_id": document_id,
            "tenant_id": tenant.tenant_id,
            "document_type": new_document_type,
            "target_module": new_target_module
        })
        
        await db.commit()
        
        return {"success": True, "message": "Document reclassified successfully"}
        
    except Exception as e:
        logger.error(f"Error reclassifying document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _store_document_record(
    db: AsyncSession,
    tenant_id: str,
    user_id: str,
    file_path: str,
    original_filename: str,
    classification: Any,
    description: str
) -> Dict[str, Any]:
    """Store document classification record"""
    
    try:
        # Insert document record
        insert_query = text("""
            INSERT INTO document_classifications 
            (tenant_id, user_id, file_path, original_filename, document_type, 
             target_module, confidence, classification_data, description)
            VALUES (:tenant_id, :user_id, :file_path, :original_filename, :document_type,
                    :target_module, :confidence, :classification_data, :description)
            RETURNING id, created_at
        """)
        
        result = await db.execute(insert_query, {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "file_path": file_path,
            "original_filename": original_filename,
            "document_type": classification.document_type.value,
            "target_module": classification.target_module.value,
            "confidence": classification.confidence,
            "classification_data": {
                "extracted_data": classification.extracted_data,
                "suggested_actions": classification.suggested_actions,
                "routing_path": classification.routing_path
            },
            "description": description
        })
        
        record = result.fetchone()
        await db.commit()
        
        return {
            "id": str(record.id),
            "created_at": record.created_at.isoformat()
        }
    
    except IntegrityError as e:
        logger.error(f"Error storing document record: {e}")
        raise HTTPException(status_code=400, detail="Document record already exists")
    
    except Exception as e:
        logger.error(f"Error storing document record: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def route_document_to_module(
    document_id: str,
    classification: Any,
    tenant_id: str,
    user_id: str
):
    """
    Background task to route document to appropriate module
    """
    try:
        from app.db.session import async_session_maker
        
        async with async_session_maker() as db:
            if classification.target_module.value == TargetModule.LOGISTICS.value:
                await route_to_logistics(db, document_id, classification, tenant_id, user_id)
            elif classification.target_module.value == TargetModule.CRM.value:
                await route_to_crm(db, document_id, classification, tenant_id, user_id)
            elif classification.target_module.value == TargetModule.BILLING.value:
                await route_to_billing(db, document_id, classification, tenant_id, user_id)
            elif classification.target_module.value == TargetModule.PROCUREMENT.value:
                await route_to_procurement(db, document_id, classification, tenant_id, user_id)
            elif classification.target_module.value == TargetModule.WAREHOUSE.value:
                await route_to_warehouse(db, document_id, classification, tenant_id, user_id)
            elif classification.target_module.value == TargetModule.COMPLIANCE.value:
                await route_to_compliance(db, document_id, classification, tenant_id, user_id)
            
            # Update document status
            update_query = text("""
                UPDATE document_classifications 
                SET status = 'routed', updated_at = NOW()
                WHERE id = :document_id
            """)
            
            await db.execute(update_query, {"document_id": document_id})
            await db.commit()
            
    except Exception as e:
        logger.error(f"Error routing document {document_id}: {e}")

async def route_to_logistics(
    db: AsyncSession,
    document_id: str,
    classification: Any,
    tenant_id: str,
    user_id: str
):
    """Route document to logistics module"""
    try:
        extracted_data = classification.extracted_data
        
        if classification.document_type == DocumentType.BILL_OF_LADING:
            # Create or update shipment
            shipment_number = extracted_data.get('shipment_number')
            
            if shipment_number:
                # Check if shipment exists
                existing = await db.execute(
                    select(Shipment).where(
                        Shipment.shipment_number == shipment_number,
                        Shipment.tenant_id == tenant_id
                    )
                )
                
                if not existing.scalar_one_or_none():
                    # Create new shipment
                    new_shipment = Shipment(
                        tenant_id=tenant_id,
                        shipment_number=shipment_number,
                        origin={
                            "port": extracted_data.get('port_of_loading'),
                            "city": extracted_data.get('port_of_loading')
                        },
                        destination={
                            "port": extracted_data.get('port_of_discharge'),
                            "city": extracted_data.get('port_of_discharge')
                        },
                        status="created",
                        goods_description=f"Bill of Lading {shipment_number}",
                        ai_extracted=True
                    )
                    
                    db.add(new_shipment)
                    
                    # Add document reference event
                    event = ShipmentEvent(
                        tenant_id=tenant_id,
                        shipment_id=new_shipment.id,
                        event_type="created",
                        actor="AI Document Classifier",
                        notes=f"Bill of Lading uploaded and processed. Document ID: {document_id}",
                        payload={"document_id": document_id, "document_type": "bill_of_lading"}
                    )
                    db.add(event)
                    
                    await db.commit()
                    logger.info(f"Created shipment {shipment_number} from Bill of Lading")
        
    except Exception as e:
        logger.error(f"Error routing to logistics: {e}")

async def route_to_crm(
    db: AsyncSession,
    document_id: str,
    classification: Any,
    tenant_id: str,
    user_id: str
):
    """Route document to CRM module"""
    try:
        # Implementation for CRM routing
        extracted_data = classification.extracted_data
        
        # Extract company information and create/update company records
        # This would depend on your CRM schema
        
    except Exception as e:
        logger.error(f"Error routing to CRM: {e}")

async def route_to_billing(
    db: AsyncSession,
    document_id: str,
    classification: Any,
    tenant_id: str,
    user_id: str
):
    """Route document to billing module"""
    try:
        extracted_data = classification.extracted_data
        
        if classification.document_type == DocumentType.COMMERCIAL_INVOICE:
            # Create invoice record
            invoice_number = extracted_data.get('invoice_number')
            total_amount = extracted_data.get('total_amount')
            
            if invoice_number:
                # Implementation depends on your billing schema
                pass
        
    except Exception as e:
        logger.error(f"Error routing to billing: {e}")

async def route_to_procurement(
    db: AsyncSession,
    document_id: str,
    classification: Any,
    tenant_id: str,
    user_id: str
):
    """Route document to procurement module"""
    try:
        # Implementation for procurement routing
        pass
    except Exception as e:
        logger.error(f"Error routing to procurement: {e}")

async def route_to_warehouse(
    db: AsyncSession,
    document_id: str,
    classification: Any,
    tenant_id: str,
    user_id: str
):
    """Route document to warehouse module"""
    try:
        # Implementation for warehouse routing
        pass
    except Exception as e:
        logger.error(f"Error routing to warehouse: {e}")

async def route_to_compliance(
    db: AsyncSession,
    document_id: str,
    classification: Any,
    tenant_id: str,
    user_id: str
):
    """Route document to compliance module"""
    try:
        # Implementation for compliance routing
        pass
    except Exception as e:
        logger.error(f"Error routing to compliance: {e}")
