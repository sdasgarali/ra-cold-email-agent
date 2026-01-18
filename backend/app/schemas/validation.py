"""Validation schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.db.models.email_validation import ValidationStatus


class ValidationResult(BaseModel):
    """Schema for validation result."""
    validation_id: int
    email: str
    provider: str
    status: ValidationStatus
    sub_status: Optional[str] = None
    validated_at: datetime

    class Config:
        from_attributes = True


class ValidationBulkRequest(BaseModel):
    """Schema for bulk validation request."""
    emails: List[EmailStr]
    provider: Optional[str] = None  # Use configured provider if not specified
