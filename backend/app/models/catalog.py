from sqlalchemy import Column, String, Integer, Boolean
from app.models.base import Base, TenantModel

class Catalog(TenantModel):
    __tablename__ = "catalogs"

    title_en = Column(String, nullable=True)
    title_fa = Column(String, nullable=True)
    title_ar = Column(String, nullable=True)
    title_ru = Column(String, nullable=True)
    url = Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)
    keywords = Column(String, nullable=True)
    clicks = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    language = Column(String, default="en")
