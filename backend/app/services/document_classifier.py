"""
AI-Powered Document Classification Service
Automatically detects document type and routes to appropriate module
"""
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import json
from pathlib import Path

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.logistics import Shipment, ShipmentEvent, ShipmentStatus
from app.models.crm import CRMCompany as Company, CRMContact as Contact, CRMDeal as Deal
from app.models.billing import Invoice, Receipt
from app.core.config import settings

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Document types that can be automatically classified"""
    BILL_OF_LADING = "bill_of_lading"
    PACKING_LIST = "packing_list"
    COMMERCIAL_INVOICE = "commercial_invoice"
    PURCHASE_ORDER = "purchase_order"
    DELIVERY_NOTE = "delivery_note"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    INSURANCE = "insurance"
    CUSTOMS_DECLARATION = "customs_declaration"
    QUALITY_CERTIFICATE = "quality_certificate"
    WAREHOUSE_RECEIPT = "warehouse_receipt"
    UNKNOWN = "unknown"

class TargetModule(Enum):
    """Target modules for document routing"""
    LOGISTICS = "logistics"
    CRM = "crm"
    BILLING = "billing"
    PROCUREMENT = "procurement"
    COMPLIANCE = "compliance"
    WAREHOUSE = "warehouse"

@dataclass
class DocumentClassification:
    """Document classification result"""
    document_type: DocumentType
    target_module: TargetModule
    confidence: float
    extracted_data: Dict
    suggested_actions: List[str]
    routing_path: str

class DocumentClassifier:
    """AI-powered document classification and routing"""
    
    def __init__(self):
        self.gemini_api_key = settings.GEMINI_API_KEY
        # Don't store client instance - create per request to avoid thread issues
        
        # Classification patterns for fast initial classification
        self.patterns = {
            DocumentType.BILL_OF_LADING: [
                r"bill of lading", r"b/l", r"bol", r"consignee", r"shipper", r"port of loading",
                r"port of discharge", r"vessel", r"voyage", r"container number"
            ],
            DocumentType.PACKING_LIST: [
                r"packing list", r"package list", r"cartons?", r"boxes?", r"gross weight",
                r"net weight", r"dimensions", r"hs code", r"item no"
            ],
            DocumentType.COMMERCIAL_INVOICE: [
                r"commercial invoice", r"invoice", r"tax invoice", r"vat", r"total amount",
                r"unit price", r"quantity", r"description of goods"
            ],
            DocumentType.PURCHASE_ORDER: [
                r"purchase order", r"p\.?o\.?", r"order no", r"requisition", r"supplier",
                r"delivery terms", r"payment terms"
            ],
            DocumentType.DELIVERY_NOTE: [
                r"delivery note", r"delivery receipt", r"proof of delivery", r"pod",
                r"received by", r"signature", r"date of delivery"
            ],
            DocumentType.RECEIPT: [
                r"receipt", r"payment received", r"cash receipt", r"paid", r"amount paid",
                r"payment confirmation"
            ],
            DocumentType.CONTRACT: [
                r"contract", r"agreement", r"terms and conditions", r"party", r"obligations",
                r"termination", r"governing law"
            ],
            DocumentType.INSURANCE: [
                r"insurance", r"policy", r"coverage", r"premium", r"claim", r"risk",
                r"beneficiary", r"insurer"
            ],
            DocumentType.CUSTOMS_DECLARATION: [
                r"customs declaration", r"import declaration", r"export declaration",
                r"tariff classification", r"duty", r"tax", r"customs value"
            ],
            DocumentType.QUALITY_CERTIFICATE: [
                r"quality certificate", r"certificate of analysis", r"inspection report",
                r"quality control", r"specification", r"compliance"
            ],
            DocumentType.WAREHOUSE_RECEIPT: [
                r"warehouse receipt", r"storage receipt", r"warehouse", r"storage",
                r"facility", r"deposited", r"received in warehouse"
            ]
        }
        
        # Module routing rules
        self.module_routing = {
            DocumentType.BILL_OF_LADING: TargetModule.LOGISTICS,
            DocumentType.PACKING_LIST: TargetModule.LOGISTICS,
            DocumentType.DELIVERY_NOTE: TargetModule.LOGISTICS,
            DocumentType.WAREHOUSE_RECEIPT: TargetModule.WAREHOUSE,
            DocumentType.COMMERCIAL_INVOICE: TargetModule.BILLING,
            DocumentType.RECEIPT: TargetModule.BILLING,
            DocumentType.PURCHASE_ORDER: TargetModule.PROCUREMENT,
            DocumentType.CONTRACT: TargetModule.COMPLIANCE,
            DocumentType.INSURANCE: TargetModule.COMPLIANCE,
            DocumentType.CUSTOMS_DECLARATION: TargetModule.COMPLIANCE,
            DocumentType.QUALITY_CERTIFICATE: TargetModule.COMPLIANCE,
        }

    async def classify_document(
        self, 
        file_content: bytes, 
        filename: str,
        tenant_id: str,
        user_id: str
    ) -> DocumentClassification:
        """
        Classify document using AI and pattern matching
        """
        try:
            # Step 1: Extract text using OCR/Vision AI
            extracted_text = await self._extract_text_from_document(file_content, filename)
            
            # Step 2: Fast pattern-based classification
            pattern_result = self._classify_by_patterns(extracted_text, filename)
            
            # Step 3: AI-powered confirmation and data extraction
            if self.gemini_api_key:
                ai_result = await self._classify_with_gemini(
                    extracted_text, filename, pattern_result
                )
                return ai_result
            else:
                return pattern_result
                
        except Exception as e:
            logger.error(f"Error classifying document {filename}: {e}")
            return self._create_fallback_classification(filename)

    async def _extract_text_from_document(self, file_content: bytes, filename: str) -> str:
        """Extract text from document using Vision AI with fallback"""
        try:
            # First try basic text extraction for common formats
            if filename.lower().endswith(('.txt', '.md')):
                return file_content.decode('utf-8', errors='ignore')
            
            # If no Gemini API key, try basic extraction
            if not self.gemini_api_key:
                logger.warning("Gemini API key not configured, using basic text extraction")
                if filename.lower().endswith('.pdf'):
                    return await self._extract_pdf_text(file_content)
                return ""
            
            # Use Gemini Vision API for text extraction
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.gemini_api_key
            }
            
            # Convert file to base64
            import base64
            file_b64 = base64.b64encode(file_content).decode()
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"""
Extract all text from this document. Focus on:
1. Document title and type
2. Key entities (names, dates, numbers, addresses)
3. Document structure and sections
4. Any identifying markers or codes

Document name: {filename}

Provide the extracted text in a clean, structured format.
"""
                    }, {
                        "inline_data": {
                            "mime_type": self._get_mime_type(filename),
                            "data": file_b64
                        }
                    }]
                }]
            }
            
            try:
                # Create fresh client per request to avoid thread issues
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                        headers=headers,
                        json=payload
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    if "candidates" in result and len(result["candidates"]) > 0:
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        logger.warning("Gemini API returned empty candidates")
                        return ""
                elif response.status_code == 429:
                    logger.warning("Gemini API rate limit exceeded, falling back to pattern matching")
                    return ""
                elif response.status_code >= 500:
                    logger.error(f"Gemini API server error: {response.status_code}, falling back")
                    return ""
                else:
                    logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                    return ""
                    
            except httpx.TimeoutException:
                logger.error("Gemini API timeout, falling back to pattern matching")
                return ""
            except httpx.RequestError as e:
                logger.error(f"Gemini API request error: {e}, falling back")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""

    def _classify_by_patterns(self, text: str, filename: str) -> DocumentClassification:
        """Fast classification using regex patterns"""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        best_match = None
        highest_score = 0
        
        for doc_type, patterns in self.patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches * 10  # Each pattern match adds 10 points
                
            # Filename bonus
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    score += 50  # Filename match gives bonus points
            
            if score > highest_score:
                highest_score = score
                best_match = doc_type
        
        if best_match and highest_score > 20:  # Minimum threshold
            target_module = self.module_routing.get(best_match, TargetModule.LOGISTICS)
            confidence = min(highest_score / 100, 0.95)  # Cap at 95%
            
            return DocumentClassification(
                document_type=best_match,
                target_module=target_module,
                confidence=confidence,
                extracted_data=self._extract_key_data(text, best_match),
                suggested_actions=self._get_suggested_actions(best_match),
                routing_path=self._get_routing_path(target_module)
            )
        
        return self._create_fallback_classification(filename)

    async def _classify_with_gemini(
        self, 
        text: str, 
        filename: str,
        pattern_result: DocumentClassification
    ) -> DocumentClassification:
        """Use Gemini AI for advanced classification and data extraction"""
        try:
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.gemini_api_key
            }
            
            prompt = f"""
Analyze this document and provide a detailed classification:

Document Name: {filename}
Extracted Text:
{text[:5000]}  # Limit text length

Based on the document content, provide:
1. Document type (one of: {', '.join([dt.value for dt in DocumentType])})
2. Target module (one of: {', '.join([tm.value for tm in TargetModule])})
3. Confidence level (0.0 to 1.0)
4. Key extracted data (JSON format)
5. Suggested actions (list)
6. Routing path

Initial pattern analysis suggests: {pattern_result.document_type.value} with {pattern_result.confidence:.2f} confidence.

Please confirm or correct this classification and provide detailed data extraction.

Respond in JSON format:
{{
    "document_type": "...",
    "target_module": "...",
    "confidence": 0.0,
    "extracted_data": {{...}},
    "suggested_actions": ["..."],
    "routing_path": "..."
}}
"""
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            response = await self.client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_text = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Extract JSON from AI response
                try:
                    json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
                    if json_match:
                        ai_data = json.loads(json_match.group())
                        
                        # Convert to DocumentClassification
                        doc_type = DocumentType(ai_data.get("document_type", "unknown"))
                        target_module = TargetModule(ai_data.get("target_module", "logistics"))
                        
                        return DocumentClassification(
                            document_type=doc_type,
                            target_module=target_module,
                            confidence=float(ai_data.get("confidence", 0.8)),
                            extracted_data=ai_data.get("extracted_data", {}),
                            suggested_actions=ai_data.get("suggested_actions", []),
                            routing_path=ai_data.get("routing_path", self._get_routing_path(target_module))
                        )
                except json.JSONDecodeError:
                    logger.error("Failed to parse AI response JSON")
                    
            return pattern_result  # Fallback to pattern result
            
        except Exception as e:
            logger.error(f"Error in AI classification: {e}")
            return pattern_result

    def _extract_key_data(self, text: str, doc_type: DocumentType) -> Dict:
        """Extract key data based on document type"""
        data = {}
        
        if doc_type == DocumentType.BILL_OF_LADING:
            data.update(self._extract_bl_data(text))
        elif doc_type == DocumentType.COMMERCIAL_INVOICE:
            data.update(self._extract_invoice_data(text))
        elif doc_type == DocumentType.PACKING_LIST:
            data.update(self._extract_packing_data(text))
        # Add more extraction methods as needed
        
        return data

    def _extract_bl_data(self, text: str) -> Dict:
        """Extract Bill of Lading specific data"""
        data = {}
        
        # Extract shipment number
        shipment_match = re.search(r'(?:shipment\s*no|bol\s*no|reference)[:\s]*([A-Z0-9\-]+)', text, re.IGNORECASE)
        if shipment_match:
            data['shipment_number'] = shipment_match.group(1)
        
        # Extract ports
        port_patterns = [
            (r'port\s*of\s*loading[:\s]*([^\n]+)', 'port_of_loading'),
            (r'port\s*of\s*discharge[:\s]*([^\n]+)', 'port_of_discharge'),
            (r'port\s*of\s*delivery[:\s]*([^\n]+)', 'port_of_delivery')
        ]
        
        for pattern, key in port_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[key] = match.group(1).strip()
        
        # Extract container numbers
        containers = re.findall(r'([A-Z]{4}\d{7})', text)
        if containers:
            data['container_numbers'] = containers
        
        return data

    def _extract_invoice_data(self, text: str) -> Dict:
        """Extract Invoice specific data"""
        data = {}
        
        # Extract invoice number
        invoice_match = re.search(r'(?:invoice\s*no|invoice\s*number)[:\s]*([A-Z0-9\-]+)', text, re.IGNORECASE)
        if invoice_match:
            data['invoice_number'] = invoice_match.group(1)
        
        # Extract total amount
        amount_match = re.search(r'(?:total|amount)[:\s]*\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
        if amount_match:
            data['total_amount'] = float(amount_match.group(1).replace(',', ''))
        
        return data

    def _extract_packing_data(self, text: str) -> Dict:
        """Extract Packing List specific data"""
        data = {}
        
        # Extract package count
        package_match = re.search(r'(?:no\s*of\s*packages?|total\s*packages?)[:\s]*([\d,]+)', text, re.IGNORECASE)
        if package_match:
            data['package_count'] = int(package_match.group(1).replace(',', ''))
        
        # Extract weight
        weight_match = re.search(r'(?:gross\s*weight|total\s*weight)[:\s]*([\d,]+\.?\d*)\s*kg', text, re.IGNORECASE)
        if weight_match:
            data['gross_weight'] = float(weight_match.group(1).replace(',', ''))
        
        return data

    def _get_suggested_actions(self, doc_type: DocumentType) -> List[str]:
        """Get suggested actions based on document type"""
        actions = {
            DocumentType.BILL_OF_LADING: [
                "Create shipment record",
                "Schedule pickup/delivery",
                "Update tracking information",
                "Notify consignee"
            ],
            DocumentType.PACKING_LIST: [
                "Verify package contents",
                "Update inventory",
                "Attach to shipment",
                "Quality check"
            ],
            DocumentType.COMMERCIAL_INVOICE: [
                "Create invoice record",
                "Calculate duties/taxes",
                "Process payment",
                "Update accounting"
            ],
            DocumentType.PURCHASE_ORDER: [
                "Create procurement record",
                "Contact supplier",
                "Schedule delivery",
                "Update inventory"
            ],
            DocumentType.DELIVERY_NOTE: [
                "Update shipment status",
                "Record delivery confirmation",
                "Update inventory",
                "Generate receipt"
            ],
            DocumentType.RECEIPT: [
                "Record payment",
                "Update account balance",
                "Generate receipt",
                "Update invoice status"
            ]
        }
        
        return actions.get(doc_type, ["Review document", "File appropriately"])

    def _get_routing_path(self, target_module: TargetModule) -> str:
        """Get routing path for target module"""
        paths = {
            TargetModule.LOGISTICS: "/logistics/shipments",
            TargetModule.CRM: "/crm/companies",
            TargetModule.BILLING: "/billing/invoices",
            TargetModule.PROCUREMENT: "/procurement/orders",
            TargetModule.COMPLIANCE: "/compliance/documents",
            TargetModule.WAREHOUSE: "/warehouse/receipts"
        }
        
        return paths.get(target_module, "/documents")

    def _create_fallback_classification(self, filename: str) -> DocumentClassification:
        """Create fallback classification when AI fails"""
        return DocumentClassification(
            document_type=DocumentType.UNKNOWN,
            target_module=TargetModule.LOGISTICS,
            confidence=0.3,
            extracted_data={"filename": filename},
            suggested_actions=["Manual review required", "Classify document manually"],
            routing_path="/documents"
        )

    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type for file"""
        ext = filename.lower().split('.')[-1]
        mime_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'tiff': 'image/tiff',
            'txt': 'text/plain',
            'md': 'text/markdown'
        }
        return mime_types.get(ext, 'application/octet-stream')

    async def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF (basic implementation)"""
        # This would use a PDF library like PyPDF2 or pdfplumber
        # For now, return empty string - would need to install PDF library
        return ""

# Global classifier instance
document_classifier = DocumentClassifier()
