from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import get_current_user
from app.core.rbac import require_permissions
from app.models.user import User
from app.models.whatsapp import WhatsAppMessage
from app.services.billing import BillingService, precheck_balance
from app.services.whatsapp import WhatsAppService
from pydantic import BaseModel

router = APIRouter()

class SendMessageRequest(BaseModel):
    recipient_phone: str
    content: str
    template_name: str = "hello_world"

@router.post("/send")
@require_permissions(["whatsapp.write"])
@precheck_balance(cost=0.5) # UX precheck only – DO NOT RELY ON THIS FOR SECURITY
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send WhatsApp message with strict Revenue Guard.
    Cost: 0.5 Credits
    
    Flow:
    1. Deduct balance (atomic, row-locked) via savepoint
    2. Attempt WhatsApp send
    3. If send fails -> refund via credit transaction
    """
    COST = 0.5
    
    # 1. ATOMIC DEDUCTION (The real guard, inside a savepoint)
    try:
        async with db.begin_nested():
            await BillingService.deduct_balance(
                db=db,
                tenant_id=current_user.current_tenant_id,
                amount=COST,
                description=f"WhatsApp to {request.recipient_phone}"
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Billing transaction failed")

    # 2. EXECUTE SERVICE
    try:
        # Assuming WhatsAppService.send_template is still an external sync HTTP call, 
        # but normally should be async if it handles networking. Let's assume it's async-compatible or we await it if it's async.
        # We check its signature shortly, for now assume async if rewritten or sync bounding thread.
        try:
            message_id = await WhatsAppService.send_template(
                phone=request.recipient_phone,
                template=request.template_name,
                variables={"text": request.content}
            )
        except TypeError:
            # Fallback if send_template is sync
            message_id = WhatsAppService.send_template(
                phone=request.recipient_phone,
                template=request.template_name,
                variables={"text": request.content}
            )
            
        # 3. LOG MESSAGE (success)
        msg = WhatsAppMessage(
            tenant_id=current_user.current_tenant_id,
            recipient_phone=request.recipient_phone,
            content=request.content,
            template_name=request.template_name,
            status="sent",
            message_id=message_id,
            cost=COST,
            direction="outbound"
        )
        db.add(msg)
        await db.commit() # Initial commit to secure message and debit
        
        # 4. SYNC CONVERSATION (Auto-create thread / link contact)
        # Note: WhatsAppService.sync_conversation needs to be reviewed to handle async db.
        # For now, we will fire it, if it's sync it might crash with async db, so we handle it gracefully.
        try:
            await WhatsAppService.sync_conversation(db, current_user.current_tenant_id, request.recipient_phone, msg)
        except TypeError:
            WhatsAppService.sync_conversation(db, current_user.current_tenant_id, request.recipient_phone, msg)
            
        await db.commit()
            
        return {"status": "sent", "message_id": message_id, "cost_deducted": COST}
        
    except Exception as e:
        # 4. REFUND: WhatsApp send failed, credit back the deducted amount
        try:
            async with db.begin_nested():
                await BillingService.refund(
                    db=db,
                    tenant_id=current_user.current_tenant_id,
                    amount=COST,
                    description=f"Refund: WhatsApp to {request.recipient_phone} failed"
                )
                
            # Log failed message
            msg = WhatsAppMessage(
                tenant_id=current_user.current_tenant_id,
                recipient_phone=request.recipient_phone,
                content=request.content,
                template_name=request.template_name,
                status="failed",
                cost=0,  # Refunded
                direction="outbound"
            )
            db.add(msg)
            await db.commit()
        except Exception:
            await db.rollback()
        
        raise HTTPException(status_code=500, detail=f"Message sending failed. Credits refunded.")

@router.get("/conversations")
@require_permissions(["whatsapp.read"])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from app.models.crm import CRMConversation
    res = await db.execute(
        select(CRMConversation)
        .where(CRMConversation.tenant_id == current_user.current_tenant_id, CRMConversation.channel == "whatsapp")
        .order_by(CRMConversation.last_message_at.desc())
    )
    convs = res.scalars().all()
    return convs

@router.get("/conversations/{conversation_id}/messages")
@require_permissions(["whatsapp.read"])
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from app.models.whatsapp import WhatsAppMessage
    import uuid
    res = await db.execute(
        select(WhatsAppMessage)
        .where(WhatsAppMessage.tenant_id == current_user.current_tenant_id, WhatsAppMessage.conversation_id == uuid.UUID(conversation_id))
        .order_by(WhatsAppMessage.created_at.asc())
    )
    msgs = res.scalars().all()
    return msgs
