"""Contact management endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.db.models.contact import ContactDetails, PriorityLevel
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("", response_model=List[ContactResponse])
async def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    client_name: Optional[str] = None,
    priority_level: Optional[PriorityLevel] = None,
    validation_status: Optional[str] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List contacts with filtering."""
    query = db.query(ContactDetails)

    if client_name:
        query = query.filter(ContactDetails.client_name.ilike(f"%{client_name}%"))
    if priority_level:
        query = query.filter(ContactDetails.priority_level == priority_level)
    if validation_status:
        query = query.filter(ContactDetails.validation_status == validation_status)
    if state:
        query = query.filter(ContactDetails.location_state == state)
    if search:
        query = query.filter(
            (ContactDetails.first_name.ilike(f"%{search}%")) |
            (ContactDetails.last_name.ilike(f"%{search}%")) |
            (ContactDetails.email.ilike(f"%{search}%"))
        )

    contacts = query.order_by(ContactDetails.created_at.desc()).offset(skip).limit(limit).all()
    return [ContactResponse.model_validate(c) for c in contacts]


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get contact by ID."""
    contact = db.query(ContactDetails).filter(ContactDetails.contact_id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return ContactResponse.model_validate(contact)


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_in: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new contact."""
    # Check for duplicate email
    existing = db.query(ContactDetails).filter(ContactDetails.email == contact_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact with this email already exists"
        )

    contact = ContactDetails(**contact_in.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)

    return ContactResponse.model_validate(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact_in: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update contact."""
    contact = db.query(ContactDetails).filter(ContactDetails.contact_id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    update_data = contact_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)

    return ContactResponse.model_validate(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete contact."""
    contact = db.query(ContactDetails).filter(ContactDetails.contact_id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    db.delete(contact)
    db.commit()


@router.get("/stats/summary")
async def get_contact_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get contact statistics summary."""
    total = db.query(func.count(ContactDetails.contact_id)).scalar()

    by_priority = db.query(
        ContactDetails.priority_level,
        func.count(ContactDetails.contact_id)
    ).group_by(ContactDetails.priority_level).all()

    by_validation = db.query(
        ContactDetails.validation_status,
        func.count(ContactDetails.contact_id)
    ).group_by(ContactDetails.validation_status).all()

    return {
        "total": total,
        "by_priority": {str(p): c for p, c in by_priority if p},
        "by_validation": {v: c for v, c in by_validation if v}
    }
