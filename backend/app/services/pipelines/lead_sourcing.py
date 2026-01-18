"""Lead sourcing pipeline service."""
import json
import os
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd
import structlog

from app.db.base import SessionLocal
from app.db.models.lead import LeadDetails, LeadStatus
from app.db.models.client import ClientInfo, ClientCategory, ClientStatus
from app.db.models.job_run import JobRun, JobStatus
from app.core.config import settings
from app.services.adapters.job_sources.mock import MockJobSourceAdapter

logger = structlog.get_logger()


def get_job_source_adapter(source: str):
    """Get the appropriate job source adapter."""
    # For now, use mock adapter for all sources
    # In production, implement LinkedIn, Indeed, Glassdoor adapters
    return MockJobSourceAdapter()


def run_lead_sourcing_pipeline(
    sources: List[str],
    triggered_by: str = "system"
) -> Dict[str, Any]:
    """
    Run the lead sourcing pipeline.

    Steps:
    1. Fetch jobs from enabled sources
    2. Normalize and deduplicate
    3. Store in lead_details
    4. Update client_info
    5. Export to XLSX if file mode enabled
    """
    db = SessionLocal()
    counters = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Create job run record
    job_run = JobRun(
        pipeline_name="lead_sourcing",
        status=JobStatus.RUNNING,
        triggered_by=triggered_by
    )
    db.add(job_run)
    db.commit()

    try:
        logger.info("Starting lead sourcing pipeline", sources=sources)

        all_jobs = []

        # Fetch from each source
        for source in sources:
            try:
                adapter = get_job_source_adapter(source)
                jobs = adapter.fetch_jobs(
                    location="United States",
                    posted_within_days=1,
                    industries=settings.TARGET_INDUSTRIES,
                    exclude_keywords=settings.EXCLUDE_IT_KEYWORDS + settings.EXCLUDE_STAFFING_KEYWORDS
                )
                logger.info(f"Fetched {len(jobs)} jobs from {source}")
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"Error fetching from {source}", error=str(e))
                counters["errors"] += 1

        # Process and deduplicate jobs
        for job_data in all_jobs:
            try:
                # Check for duplicate by job_link
                if job_data.get("job_link"):
                    existing = db.query(LeadDetails).filter(
                        LeadDetails.job_link == job_data["job_link"]
                    ).first()
                    if existing:
                        counters["skipped"] += 1
                        continue

                # Check for duplicate by company+title+state+date
                existing = db.query(LeadDetails).filter(
                    LeadDetails.client_name == job_data["client_name"],
                    LeadDetails.job_title == job_data["job_title"],
                    LeadDetails.state == job_data.get("state"),
                    LeadDetails.posting_date == job_data.get("posting_date")
                ).first()
                if existing:
                    counters["skipped"] += 1
                    continue

                # Create new lead
                lead = LeadDetails(
                    client_name=job_data["client_name"],
                    job_title=job_data["job_title"],
                    state=job_data.get("state"),
                    posting_date=job_data.get("posting_date"),
                    job_link=job_data.get("job_link"),
                    salary_min=job_data.get("salary_min"),
                    salary_max=job_data.get("salary_max"),
                    source=job_data.get("source"),
                    lead_status=LeadStatus.NEW
                )
                db.add(lead)
                counters["inserted"] += 1

                # Upsert client_info
                upsert_client(db, job_data["client_name"])

            except Exception as e:
                logger.error("Error processing job", error=str(e), job=job_data)
                counters["errors"] += 1

        db.commit()

        # Export to XLSX if configured
        if settings.DATA_STORAGE == "files" or True:  # Always export for convenience
            export_leads_to_xlsx(db)

        # Update job run
        job_run.status = JobStatus.COMPLETED
        job_run.ended_at = datetime.utcnow()
        job_run.counters_json = json.dumps(counters)
        db.commit()

        logger.info("Lead sourcing completed", counters=counters)
        return counters

    except Exception as e:
        logger.error("Lead sourcing pipeline failed", error=str(e))
        job_run.status = JobStatus.FAILED
        job_run.error_message = str(e)
        job_run.ended_at = datetime.utcnow()
        db.commit()
        raise
    finally:
        db.close()


def upsert_client(db, client_name: str):
    """Create or update client_info record."""
    client = db.query(ClientInfo).filter(ClientInfo.client_name == client_name).first()

    if not client:
        client = ClientInfo(
            client_name=client_name,
            status=ClientStatus.ACTIVE,
            start_date=date.today(),
            service_count=1,
            client_category=ClientCategory.PROSPECT
        )
        db.add(client)
    else:
        client.service_count += 1

        # Compute client category based on posting frequency
        three_months_ago = date.today() - timedelta(days=90)
        unique_dates = db.query(LeadDetails.posting_date).filter(
            LeadDetails.client_name == client_name,
            LeadDetails.posting_date >= three_months_ago
        ).distinct().count()

        if unique_dates > 3:
            client.client_category = ClientCategory.REGULAR
        elif unique_dates > 0:
            client.client_category = ClientCategory.OCCASIONAL
        else:
            client.client_category = ClientCategory.PROSPECT


def export_leads_to_xlsx(db, filepath: Optional[str] = None):
    """Export leads to XLSX file."""
    if not filepath:
        os.makedirs(settings.EXPORT_PATH, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(settings.EXPORT_PATH, f"Job_requirements_{timestamp}.xlsx")

    leads = db.query(LeadDetails).order_by(LeadDetails.created_at.desc()).limit(1000).all()

    data = []
    for lead in leads:
        data.append({
            "Lead ID": lead.lead_id,
            "Company": lead.client_name,
            "Job Title": lead.job_title,
            "State": lead.state,
            "Posting Date": lead.posting_date.isoformat() if lead.posting_date else None,
            "Job Link": lead.job_link,
            "Salary Min": float(lead.salary_min) if lead.salary_min else None,
            "Salary Max": float(lead.salary_max) if lead.salary_max else None,
            "Source": lead.source,
            "First Name": lead.first_name,
            "Last Name": lead.last_name,
            "Contact Title": lead.contact_title,
            "Contact Email": lead.contact_email,
            "Contact Phone": lead.contact_phone,
            "Status": lead.lead_status.value if lead.lead_status else None
        })

    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)
    logger.info(f"Exported {len(data)} leads to {filepath}")

    return filepath


def import_leads_from_file(
    filepath: str,
    triggered_by: str = "system"
) -> Dict[str, Any]:
    """Import leads from XLSX file."""
    db = SessionLocal()
    counters = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

    try:
        df = pd.read_excel(filepath)
        logger.info(f"Reading {len(df)} rows from {filepath}")

        for _, row in df.iterrows():
            try:
                client_name = str(row.get("Company", row.get("client_name", "")))
                job_title = str(row.get("Job Title", row.get("job_title", "")))

                if not client_name or not job_title:
                    counters["skipped"] += 1
                    continue

                # Check for existing
                existing = db.query(LeadDetails).filter(
                    LeadDetails.client_name == client_name,
                    LeadDetails.job_title == job_title
                ).first()

                if existing:
                    counters["skipped"] += 1
                    continue

                lead = LeadDetails(
                    client_name=client_name,
                    job_title=job_title,
                    state=str(row.get("State", row.get("state", ""))) if pd.notna(row.get("State", row.get("state"))) else None,
                    source="file_import",
                    lead_status=LeadStatus.NEW
                )
                db.add(lead)
                counters["inserted"] += 1

                upsert_client(db, client_name)

            except Exception as e:
                logger.error("Error importing row", error=str(e))
                counters["errors"] += 1

        db.commit()
        return counters

    except Exception as e:
        logger.error("Import failed", error=str(e))
        raise
    finally:
        db.close()
