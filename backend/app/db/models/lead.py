"""Lead details model for job posts and leads."""
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, Enum, Index
from app.db.base import Base


class LeadStatus(str, PyEnum):
    """Lead processing status."""
    NEW = "new"
    ENRICHED = "enriched"
    VALIDATED = "validated"
    SENT = "sent"
    SKIPPED = "skipped"


class LeadDetails(Base):
    """Lead details model - Job posts and lead rows sourced from job boards."""

    __tablename__ = "lead_details"

    lead_id = Column(Integer, primary_key=True, autoincrement=True)

    # Company/Client information
    client_name = Column(String(255), nullable=False, index=True)

    # Job information
    job_title = Column(String(255), nullable=False)
    state = Column(String(50), nullable=True)  # 2-letter state code
    posting_date = Column(Date, nullable=True)
    job_link = Column(String(500), nullable=True, unique=True)
    salary_min = Column(Numeric(10, 2), nullable=True)
    salary_max = Column(Numeric(10, 2), nullable=True)
    source = Column(String(50), nullable=True)  # linkedin, indeed, glassdoor, simplyhired

    # Contact information (blank until enrichment)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    contact_title = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_source = Column(String(50), nullable=True)  # apollo, seamless

    # Status tracking
    lead_status = Column(Enum(LeadStatus), default=LeadStatus.NEW, nullable=False)
    skip_reason = Column(Text, nullable=True)

    # Research analyst tracking
    ra_name = Column(String(100), nullable=True)

    __table_args__ = (
        Index('idx_lead_client_job', 'client_name', 'job_title', 'state', 'posting_date'),
        Index('idx_lead_status', 'lead_status'),
        Index('idx_lead_posting_date', 'posting_date'),
    )

    def __repr__(self) -> str:
        return f"<LeadDetails(lead_id={self.lead_id}, client='{self.client_name}', job='{self.job_title}')>"
