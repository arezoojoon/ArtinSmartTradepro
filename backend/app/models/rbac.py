"""
RBAC Models — Phase 1 Architecture.
Permissions are global (system-wide), Roles are tenant-scoped.
Users are mapped to Roles via UserRole (many-to-many).
"""
from sqlalchemy import Column, String, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid


class Permission(Base):
    """System-wide permission (e.g. crm.read, crm.write, users.manage)."""
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)

    # Many-to-many with Role
    role_permissions = relationship("RolePermission", back_populates="permission")


class Role(Base):
    """Tenant-scoped role (e.g. Owner, Trade Manager, Sales Agent)."""
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_role_tenant_name"),
    )

    # Relationships
    tenant = relationship("Tenant")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    @property
    def permission_names(self):
        return [rp.permission.name for rp in self.role_permissions if rp.permission]


class RolePermission(Base):
    """Link table: Role <-> Permission."""
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")


class UserRole(Base):
    """Link table: User <-> Role (tenant-scoped)."""
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    user = relationship("User")
    role = relationship("Role", back_populates="user_roles")
