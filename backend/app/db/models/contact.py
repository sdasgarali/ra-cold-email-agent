"""Contact details model for discovered contacts."""
from sqlalchemy import Column, Integer, String, Enum, Index, ForeignKey
from enum import Enum as PyEnum
from app.db.base import Base


class PriorityLevel(str, PyEnum):
    """Contact priority level based on decision-maker hierarchy."""
    P1_JOB_POSTER = "p1_job_poster"
    P2_HR_TA_RECRUITER = "p2_hr_ta_recruiter"
    P3_HR_MANAGER = "p3_hr_manager"
    P4_OPS_LEADER = "p4_ops_leader"
    P5_FUNCTIONAL_MANAGER = "p5_functional_manager"


class ContactDetails(Base):
    """Contact details model - Discovered contacts for outreach."""

    __tablename__ = "contact_details"

    contact_id = Column(Integer, primary_key=True, autoincrement=True)

    # Company link
    client_name = Column(String(255), nullable=False, index=True)

    # Contact information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    location_state = Column(String(50), nullable=True)  # 2-letter state code
    phone = Column(String(50), nullable=True)

    # Discovery metadata
    source = Column(String(50), nullable=True)  # apollo, seamless
    priority_level = Column(Enum(PriorityLevel), nullable=True)

    # Validation status (denormalized for convenience)
    validation_status = Column(String(50), nullable=True)  # Valid, Invalid, Catch-all, Unknown

    # Last outreach tracking for cooldown enforcement
    last_outreach_date = Column(String(50), nullable=True)

    __table_args__ = (
        Index('idx_contact_client', 'client_name'),
        Index('idx_contact_email', 'email'),
        Index('idx_contact_priority', 'priority_level'),
    )

    def __repr__(self) -> str:
        return f"<ContactDetails(contact_id={self.contact_id}, name='{self.first_name} {self.last_name}', email='{self.email}')>"
