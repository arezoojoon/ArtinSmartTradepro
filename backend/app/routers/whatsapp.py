from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.whatsapp import WhatsAppMessage
from app.middleware.auth import get_current_active_user
from app.middleware.plan_gate import require_feature
from app.constants import Feature
from app.services.billing import BillingService, precheck_balance
from app.services.whatsapp import WhatsAppService
from pydantic import BaseModel

router = APIRouter()

class SendMessageRequest(BaseModel):
    recipient_phone: str
    content: str
    template_name: str = "hello_world"

@router.post("/send")
@require_feature(Feature.WHATSAPP_SINGLE)
@precheck_balance(cost=0.5) # UX precheck only – DO NOT RELY ON THIS FOR SECURITY
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send WhatsApp message with strict Revenue Guard.
    Cost: 0.5 Credits
    
    Flow:
    1. Deduct balance (atomic, row-locked)
    2. Attempt WhatsApp send
    3. If send fails -> refund via credit transaction
    """
    COST = 0.5
    tx = None
    
    # 1. ATOMIC DEDUCTION (The real guard, inside a savepoint)
    try:
        with db.begin_nested():
            tx = BillingService.deduct_balance(
                db=db,
                tenant_id=current_user.tenant_id,
                amount=COST,
                description=f"WhatsApp to {request.recipient_phone}"
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Billing transaction failed")

    # 2. EXECUTE SERVICE
    try:
        message_id = WhatsAppService.send_template(
            phone=request.recipient_phone,
            template=request.template_name,
            variables={"text": request.content}
        )
        
        # 3. LOG MESSAGE (success)
        msg = WhatsAppMessage(
            tenant_id=current_user.tenant_id,
            recipient_phone=request.recipient_phone,
            content=request.content,
            template_name=request.template_name,
            status="sent",
            message_id=message_id,
            cost=COST
        )
        db.add(msg)
        
        # 4. SYNC CONVERSATION (Auto-create thread / link contact)
        WhatsAppService.sync_conversation(db, current_user.tenant_id, request.recipient_phone, msg)
        
        # Commit happens inside sync_conversation or here if needed
        # sync_conversation does commit, but let's be safe if it changes
        if db.in_transaction():
            db.commit()
            
        return {"status": "sent", "message_id": message_id, "cost_deducted": COST}
        
    except Exception as e:
        # 4. REFUND: WhatsApp send failed, credit back the deducted amount
        try:
            BillingService.refund(
                db=db,
                tenant_id=current_user.tenant_id,
                amount=COST,
                description=f"Refund: WhatsApp to {request.recipient_phone} failed"
            )
            # Log failed message
            msg = WhatsAppMessage(
                tenant_id=current_user.tenant_id,
                recipient_phone=request.recipient_phone,
                content=request.content,
                template_name=request.template_name,
                status="failed",
                cost=0  # Refunded
            )
            db.add(msg)
            db.commit()
        except Exception:
            db.rollback()
        
        raise HTTPException(status_code=500, detail=f"Message sending failed. Credits refunded.")
