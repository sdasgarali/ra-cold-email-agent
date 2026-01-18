"""Contact schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.db.models.contact import PriorityLevel


class ContactBase(BaseModel):
    """Base contact schema."""
    client_name: str
    first_name: str
    last_name: str
    title: Optional[str] = None
    email: EmailStr
    location_state: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    priority_level: Optional[PriorityLevel] = None


class ContactCreate(ContactBase):
    """Schema for creating a contact."""
    pass


class ContactUpdate(BaseModel):
    """Schema for updating a contact."""
    client_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[EmailStr] = None
    location_state: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    priority_level: Optional[PriorityLevel] = None
    validation_status: Optional[str] = None
    last_outreach_date: Optional[str] = None


class ContactResponse(ContactBase):
    """Schema for contact response."""
    contact_id: int
    validation_status: Optional[str] = None
    last_outreach_date: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
