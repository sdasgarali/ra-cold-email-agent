"""Lead management endpoints."""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.db.models.lead import LeadDetails, LeadStatus
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, LeadListResponse

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    status: Optional[LeadStatus] = None,
    source: Optional[str] = None,
    state: Optional[str] = None,
    client_name: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List leads with filtering and pagination."""
    query = db.query(LeadDetails)

    # Apply filters
    if status:
        query = query.filter(LeadDetails.lead_status == status)
    if source:
        query = query.filter(LeadDetails.source == source)
    if state:
        query = query.filter(LeadDetails.state == state)
    if client_name:
        query = query.filter(LeadDetails.client_name.ilike(f"%{client_name}%"))
    if from_date:
        query = query.filter(LeadDetails.posting_date >= from_date)
    if to_date:
        query = query.filter(LeadDetails.posting_date <= to_date)
    if search:
        query = query.filter(
            (LeadDetails.client_name.ilike(f"%{search}%")) |
            (LeadDetails.job_title.ilike(f"%{search}%"))
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    leads = query.order_by(LeadDetails.created_at.desc()).offset(offset).limit(page_size).all()

    pages = (total + page_size - 1) // page_size

    return LeadListResponse(
        items=[LeadResponse.model_validate(lead) for lead in leads],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get lead by ID."""
    lead = db.query(LeadDetails).filter(LeadDetails.lead_id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return LeadResponse.model_validate(lead)


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_in: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new lead."""
    # Check for duplicate by job_link
    if lead_in.job_link:
        existing = db.query(LeadDetails).filter(LeadDetails.job_link == lead_in.job_link).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lead with this job link already exists"
            )

    lead = LeadDetails(**lead_in.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)

    return LeadResponse.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_in: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update lead."""
    lead = db.query(LeadDetails).filter(LeadDetails.lead_id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    update_data = lead_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)

    return LeadResponse.model_validate(lead)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete lead."""
    lead = db.query(LeadDetails).filter(LeadDetails.lead_id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    db.delete(lead)
    db.commit()


@router.get("/stats/summary")
async def get_lead_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get lead statistics summary."""
    total = db.query(func.count(LeadDetails.lead_id)).scalar()

    by_status = db.query(
        LeadDetails.lead_status,
        func.count(LeadDetails.lead_id)
    ).group_by(LeadDetails.lead_status).all()

    by_source = db.query(
        LeadDetails.source,
        func.count(LeadDetails.lead_id)
    ).group_by(LeadDetails.source).all()

    return {
        "total": total,
        "by_status": {str(s): c for s, c in by_status if s},
        "by_source": {s: c for s, c in by_source if s}
    }
