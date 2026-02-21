from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.crm import CRMPipeline
from app.core.rbac import DEFAULT_ROLES

async def seed_new_tenant(db: AsyncSession, tenant_id: UUID, user_id: UUID = None):
    """
    Called immediately after a new tenant is created.
    1. Seeds default roles and permissions for the tenant.
    2. Assigns the 'Owner' role to the creator (user_id).
    3. Creates a default CRM pipeline.
    """
    
    # 1. Fetch all global permissions (they should have been seeded by Alembic)
    result = await db.execute(select(Permission))
    all_permissions = result.scalars().all()
    perm_map = {p.name: p.id for p in all_permissions}
    
    owner_role_id = None
    
    # 2. Create the default roles for this tenant
    for role_name, required_perms in DEFAULT_ROLES.items():
        role = Role(
            tenant_id=tenant_id,
            name=role_name,
            description=f"Default {role_name} role"
        )
        db.add(role)
        await db.commit()
        await db.refresh(role)
        
        if role_name == "Owner":
            owner_role_id = role.id
            
        # Assign permissions to the role
        for perm_name in required_perms:
            perm_id = perm_map.get(perm_name)
            if perm_id:
                rp = RolePermission(role_id=role.id, permission_id=perm_id)
                db.add(rp)
    
    await db.commit()
    
    # 3. Assign the creator as the Owner
    if user_id and owner_role_id:
        user_role = UserRole(user_id=user_id, role_id=owner_role_id)
        db.add(user_role)
        await db.commit()
        
    # 4. Create default CRM Pipeline
    default_pipeline = CRMPipeline(
        tenant_id=tenant_id,
        name="Sales Pipeline",
        stages=[
            {"id": "lead", "name": "Lead"},
            {"id": "contacted", "name": "Contacted"},
            {"id": "proposal", "name": "Proposal"},
            {"id": "negotiation", "name": "Negotiation"},
            {"id": "won", "name": "Won"},
            {"id": "lost", "name": "Lost"}
        ],
        is_default=1
    )
    db.add(default_pipeline)
    await db.commit()
