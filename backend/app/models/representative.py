from sqlalchemy import Column, String, Boolean, Enum
from app.models.base import Base, TenantModel

class Representative(TenantModel):
    __tablename__ = "representatives"

    country = Column(String, index=True)
    city = Column(String)
    address = Column(String)
    phone = Column(String)
    email = Column(String)
    contact_person = Column(String)
    is_active = Column(Boolean, default=True)
    business_card_url = Column(String, nullable=True)
    rep_type = Column(String, default="personal") # 'personal' | 'office'
    office_name = Column(String, nullable=True)
