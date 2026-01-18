"""Contact enrichment pipeline service."""
import json
from datetime import datetime
from typing import Dict, Any
import structlog

from app.db.base import SessionLocal
from app.db.models.lead import LeadDetails, LeadStatus
from app.db.models.contact import ContactDetails
from app.db.models.client import ClientInfo
from app.db.models.job_run import JobRun, JobStatus
from app.core.config import settings
from app.services.adapters.contact_discovery.mock import MockContactDiscoveryAdapter
from app.services.adapters.contact_discovery.apollo import ApolloAdapter
from app.services.adapters.contact_discovery.seamless import SeamlessAdapter

logger = structlog.get_logger()


def get_contact_discovery_adapter():
    """Get the configured contact discovery adapter."""
    provider = settings.CONTACT_PROVIDER

    if provider == "apollo":
        return ApolloAdapter()
    elif provider == "seamless":
        return SeamlessAdapter()
    else:
        return MockContactDiscoveryAdapter()


def run_contact_enrichment_pipeline(
    triggered_by: str = "system"
) -> Dict[str, Any]:
    """
    Run the contact enrichment pipeline.

    Steps:
    1. Select leads with blank contact info
    2. Search for decision-makers using provider
    3. Store contacts with priority levels
    4. Update lead records
    """
    db = SessionLocal()
    counters = {"contacts_found": 0, "leads_enriched": 0, "skipped": 0, "errors": 0}

    # Create job run record
    job_run = JobRun(
        pipeline_name="contact_enrichment",
        status=JobStatus.RUNNING,
        triggered_by=triggered_by
    )
    db.add(job_run)
    db.commit()

    try:
        logger.info("Starting contact enrichment pipeline")

        adapter = get_contact_discovery_adapter()
        max_contacts_per_job = settings.MAX_CONTACTS_PER_COMPANY_PER_JOB

        # Get leads needing enrichment
        leads = db.query(LeadDetails).filter(
            LeadDetails.first_name.is_(None),
            LeadDetails.lead_status == LeadStatus.NEW
        ).limit(100).all()

        logger.info(f"Found {len(leads)} leads to enrich")

        for lead in leads:
            try:
                # Check how many contacts we already have for this company/job
                existing_count = db.query(ContactDetails).filter(
                    ContactDetails.client_name == lead.client_name
                ).count()

                if existing_count >= max_contacts_per_job:
                    counters["skipped"] += 1
                    continue

                # Search for contacts
                contacts = adapter.search_contacts(
                    company_name=lead.client_name,
                    job_title=lead.job_title,
                    state=lead.state,
                    limit=max_contacts_per_job - existing_count
                )

                if not contacts:
                    counters["skipped"] += 1
                    continue

                # Store contacts
                for contact_data in contacts:
                    # Check for duplicate email
                    existing = db.query(ContactDetails).filter(
                        ContactDetails.email == contact_data["email"]
                    ).first()

                    if existing:
                        continue

                    contact = ContactDetails(
                        client_name=lead.client_name,
                        first_name=contact_data["first_name"],
                        last_name=contact_data["last_name"],
                        title=contact_data.get("title"),
                        email=contact_data["email"],
                        location_state=contact_data.get("location_state") or lead.state,
                        phone=contact_data.get("phone"),
                        source=contact_data.get("source"),
                        priority_level=contact_data.get("priority_level")
                    )
                    db.add(contact)
                    counters["contacts_found"] += 1

                # Update lead with first contact info
                if contacts:
                    first_contact = contacts[0]
                    lead.first_name = first_contact["first_name"]
                    lead.last_name = first_contact["last_name"]
                    lead.contact_title = first_contact.get("title")
                    lead.contact_email = first_contact["email"]
                    lead.contact_phone = first_contact.get("phone")
                    lead.contact_source = first_contact.get("source")
                    lead.lead_status = LeadStatus.ENRICHED
                    counters["leads_enriched"] += 1

            except Exception as e:
                logger.error("Error enriching lead", error=str(e), lead_id=lead.lead_id)
                counters["errors"] += 1

        db.commit()

        # Update job run
        job_run.status = JobStatus.COMPLETED
        job_run.ended_at = datetime.utcnow()
        job_run.counters_json = json.dumps(counters)
        db.commit()

        logger.info("Contact enrichment completed", counters=counters)
        return counters

    except Exception as e:
        logger.error("Contact enrichment pipeline failed", error=str(e))
        job_run.status = JobStatus.FAILED
        job_run.error_message = str(e)
        job_run.ended_at = datetime.utcnow()
        db.commit()
        raise
    finally:
        db.close()
