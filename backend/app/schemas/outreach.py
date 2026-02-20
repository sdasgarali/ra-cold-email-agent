"""Outreach schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.db.models.outreach import OutreachStatus, OutreachChannel


class OutreachEventCreate(BaseModel):
    """Schema for creating an outreach event."""
    contact_id: int
    lead_id: Optional[int] = None
    channel: OutreachChannel
    template_id: Optional[int] = None
    subject: Optional[str] = None
    status: OutreachStatus
    body_html: Optional[str] = None
    body_text: Optional[str] = None


class OutreachEventResponse(BaseModel):
    """Schema for outreach event response."""
    event_id: int
    contact_id: int
    lead_id: Optional[int] = None
    sent_at: datetime
    channel: OutreachChannel
    template_id: Optional[int] = None
    subject: Optional[str] = None
    status: OutreachStatus
    bounce_reason: Optional[str] = None
    reply_detected_at: Optional[datetime] = None
    skip_reason: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    reply_subject: Optional[str] = None
    reply_body: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
