from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Union

class InsightWrapper(BaseModel):
    """
    Standardized wrapper for any data-driven insight.
    Ensures every claim has a source, timestamp, and confidence level.
    """
    source: str = Field(..., description="Name of the data source (e.g., 'UN Comtrade', 'WAHA')")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the data was collected or analyzed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0-1)")
    reasoning: Optional[Union[str, List[str]]] = Field(None, description="Explanation for the confidence score or insight")
    source_url: Optional[str] = Field(None, description="Optional link to the raw data source")

class HighlyTraceableInsight(InsightWrapper):
    """Extended version with more metadata for critical decisions"""
    dataset_version: Optional[str] = None
    collectors: Optional[List[str]] = None  # Scrapers or agents involved
    raw_evidence_snippet: Optional[str] = None
