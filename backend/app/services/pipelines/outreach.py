"""Outreach pipeline service."""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd
import structlog

from app.db.base import SessionLocal
from app.db.models.lead import LeadDetails, LeadStatus
from app.db.models.contact import ContactDetails
from app.db.models.email_validation import EmailValidationResult, ValidationStatus
from app.db.models.outreach import OutreachEvent, OutreachStatus, OutreachChannel
from app.db.models.suppression import SuppressionList
from app.db.models.job_run import JobRun, JobStatus
from app.core.config import settings
from app.services.adapters.email_sending.mock import MockEmailSendAdapter
from app.services.adapters.email_sending.smtp import SMTPAdapter

logger = structlog.get_logger()


def get_email_send_adapter():
    """Get the configured email sending adapter."""
    mode = settings.EMAIL_SEND_MODE

    if mode == "smtp":
        return SMTPAdapter()
    else:
        return MockEmailSendAdapter()


def check_send_eligibility(db, contact: ContactDetails) -> tuple[bool, str]:
    """
    Check if a contact is eligible for outreach.

    Returns (eligible, reason)
    """
    email = contact.email.lower()

    # Check suppression list
    suppressed = db.query(SuppressionList).filter(
        SuppressionList.email == email,
        (SuppressionList.expires_at.is_(None) | (SuppressionList.expires_at > datetime.utcnow()))
    ).first()
    if suppressed:
        return False, f"Suppressed: {suppressed.reason}"

    # Check validation status
    if contact.validation_status not in ["valid", "Valid"]:
        validation = db.query(EmailValidationResult).filter(
            EmailValidationResult.email == email
        ).order_by(EmailValidationResult.validated_at.desc()).first()

        if not validation or validation.status != ValidationStatus.VALID:
            return False, "Email not validated or invalid"

    # Check cooldown period
    cooldown_date = datetime.utcnow() - timedelta(days=settings.COOLDOWN_DAYS)
    recent_outreach = db.query(OutreachEvent).filter(
        OutreachEvent.contact_id == contact.contact_id,
        OutreachEvent.sent_at >= cooldown_date,
        OutreachEvent.status == OutreachStatus.SENT
    ).first()
    if recent_outreach:
        return False, f"Cooldown: sent on {recent_outreach.sent_at.date()}"

    # Check per-company per-job limit
    company_contacts_sent = db.query(OutreachEvent).join(ContactDetails).filter(
        ContactDetails.client_name == contact.client_name,
        OutreachEvent.status == OutreachStatus.SENT
    ).count()
    if company_contacts_sent >= settings.MAX_CONTACTS_PER_COMPANY_PER_JOB:
        return False, "Max contacts per company reached"

    return True, "Eligible"


def run_outreach_mailmerge_pipeline(
    triggered_by: str = "system"
) -> Dict[str, Any]:
    """
    Generate mail merge export package.

    Creates:
    1. Verified contacts CSV
    2. Word template guide
    """
    db = SessionLocal()
    counters = {"eligible": 0, "skipped": 0, "exported": 0}

    # Create job run record
    job_run = JobRun(
        pipeline_name="outreach_mailmerge",
        status=JobStatus.RUNNING,
        triggered_by=triggered_by
    )
    db.add(job_run)
    db.commit()

    try:
        logger.info("Starting mailmerge export")

        # Get validated contacts
        contacts = db.query(ContactDetails).filter(
            ContactDetails.validation_status == "valid"
        ).all()

        eligible_contacts = []
        for contact in contacts:
            eligible, reason = check_send_eligibility(db, contact)
            if eligible:
                eligible_contacts.append(contact)
                counters["eligible"] += 1
            else:
                counters["skipped"] += 1
                logger.debug("Contact skipped", email=contact.email, reason=reason)

        if not eligible_contacts:
            logger.info("No eligible contacts for mailmerge")
            job_run.status = JobStatus.COMPLETED
            job_run.ended_at = datetime.utcnow()
            job_run.counters_json = json.dumps(counters)
            db.commit()
            return counters

        # Create export directory
        os.makedirs(settings.EXPORT_PATH, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Export to CSV
        data = []
        for contact in eligible_contacts:
            data.append({
                "First Name": contact.first_name,
                "Last Name": contact.last_name,
                "Email": contact.email,
                "Title": contact.title,
                "Company": contact.client_name,
                "State": contact.location_state
            })

        df = pd.DataFrame(data)
        csv_path = os.path.join(settings.EXPORT_PATH, f"mailmerge_contacts_{timestamp}.csv")
        df.to_csv(csv_path, index=False)
        counters["exported"] = len(data)

        # Create template guide
        guide_content = f"""
MAIL MERGE GUIDE
================

Generated: {datetime.now().isoformat()}
Total Contacts: {len(data)}

MERGE FIELDS:
- {{First Name}} - Contact first name
- {{Last Name}} - Contact last name
- {{Email}} - Contact email address
- {{Title}} - Contact job title
- {{Company}} - Company name
- {{State}} - State

STEPS:
1. Open your Word template
2. Use Insert > Mail Merge > Start Mail Merge
3. Select the CSV file: {csv_path}
4. Insert merge fields into your template
5. Preview and send

COMPLIANCE NOTES:
- Always include unsubscribe link
- Include company mailing address: {settings.company_address if hasattr(settings, 'company_address') else 'Configure in settings'}
- Do not send to same contact within {settings.COOLDOWN_DAYS} days
"""

        guide_path = os.path.join(settings.EXPORT_PATH, f"mailmerge_guide_{timestamp}.txt")
        with open(guide_path, "w") as f:
            f.write(guide_content)

        # Record outreach events
        for contact in eligible_contacts:
            event = OutreachEvent(
                contact_id=contact.contact_id,
                channel=OutreachChannel.MAILMERGE,
                status=OutreachStatus.SENT,
                skip_reason=None
            )
            db.add(event)

            # Update contact last outreach date
            contact.last_outreach_date = datetime.now().isoformat()

        db.commit()

        # Update job run
        job_run.status = JobStatus.COMPLETED
        job_run.ended_at = datetime.utcnow()
        job_run.counters_json = json.dumps(counters)
        job_run.logs_path = csv_path
        db.commit()

        logger.info("Mailmerge export completed", counters=counters, csv_path=csv_path)
        return counters

    except Exception as e:
        logger.error("Mailmerge pipeline failed", error=str(e))
        job_run.status = JobStatus.FAILED
        job_run.error_message = str(e)
        job_run.ended_at = datetime.utcnow()
        db.commit()
        raise
    finally:
        db.close()


def run_outreach_send_pipeline(
    dry_run: bool = True,
    limit: int = 30,
    triggered_by: str = "system"
) -> Dict[str, Any]:
    """
    Send emails programmatically with rate limiting.
    """
    db = SessionLocal()
    counters = {"sent": 0, "skipped": 0, "errors": 0}

    # Create job run record
    job_run = JobRun(
        pipeline_name="outreach_send",
        status=JobStatus.RUNNING,
        triggered_by=triggered_by
    )
    db.add(job_run)
    db.commit()

    try:
        logger.info("Starting outreach send", dry_run=dry_run, limit=limit)

        adapter = get_email_send_adapter()

        # Check daily limit
        today = datetime.utcnow().date()
        today_sent = db.query(OutreachEvent).filter(
            OutreachEvent.sent_at >= datetime.combine(today, datetime.min.time()),
            OutreachEvent.status == OutreachStatus.SENT,
            OutreachEvent.channel != OutreachChannel.MAILMERGE
        ).count()

        remaining_limit = min(limit, settings.DAILY_SEND_LIMIT - today_sent)
        if remaining_limit <= 0:
            logger.info("Daily send limit reached")
            job_run.status = JobStatus.COMPLETED
            job_run.ended_at = datetime.utcnow()
            job_run.counters_json = json.dumps({"message": "Daily limit reached"})
            db.commit()
            return counters

        # Get validated contacts not yet sent
        contacts = db.query(ContactDetails).filter(
            ContactDetails.validation_status == "valid"
        ).all()

        messages_to_send = []
        for contact in contacts:
            if len(messages_to_send) >= remaining_limit:
                break

            eligible, reason = check_send_eligibility(db, contact)
            if not eligible:
                counters["skipped"] += 1
                continue

            messages_to_send.append({
                "contact": contact,
                "to_email": contact.email,
                "subject": f"Exciting Opportunity at {contact.client_name}",
                "body_html": f"""
                    <p>Dear {contact.first_name},</p>
                    <p>We noticed your company is hiring and wanted to reach out about our staffing solutions.</p>
                    <p>Best regards,<br>The Team</p>
                    <hr>
                    <small>To unsubscribe, reply with "UNSUBSCRIBE"</small>
                """,
                "body_text": f"Dear {contact.first_name},\n\nWe noticed your company is hiring...",
                "from_name": "Exzelon Team"
            })

        if not messages_to_send:
            logger.info("No messages to send")
            job_run.status = JobStatus.COMPLETED
            job_run.ended_at = datetime.utcnow()
            job_run.counters_json = json.dumps(counters)
            db.commit()
            return counters

        # Send emails (or simulate in dry run)
        for msg in messages_to_send:
            contact = msg["contact"]
            try:
                if dry_run:
                    logger.info("DRY RUN - Would send to", email=msg["to_email"])
                    status = OutreachStatus.SKIPPED
                    skip_reason = "dry_run"
                else:
                    result = adapter.send_email(
                        to_email=msg["to_email"],
                        subject=msg["subject"],
                        body_html=msg["body_html"],
                        body_text=msg["body_text"],
                        from_name=msg["from_name"]
                    )

                    if result["success"]:
                        status = OutreachStatus.SENT
                        skip_reason = None
                        counters["sent"] += 1
                    else:
                        status = OutreachStatus.SKIPPED
                        skip_reason = result.get("error", "Unknown error")
                        counters["errors"] += 1

                # Record event
                event = OutreachEvent(
                    contact_id=contact.contact_id,
                    channel=OutreachChannel.SMTP if not dry_run else OutreachChannel.MAILMERGE,
                    subject=msg["subject"],
                    status=status,
                    skip_reason=skip_reason
                )
                db.add(event)

                if status == OutreachStatus.SENT:
                    contact.last_outreach_date = datetime.now().isoformat()

            except Exception as e:
                logger.error("Error sending email", error=str(e), email=msg["to_email"])
                counters["errors"] += 1

        db.commit()

        # Update job run
        job_run.status = JobStatus.COMPLETED
        job_run.ended_at = datetime.utcnow()
        job_run.counters_json = json.dumps(counters)
        db.commit()

        logger.info("Outreach send completed", counters=counters)
        return counters

    except Exception as e:
        logger.error("Outreach send pipeline failed", error=str(e))
        job_run.status = JobStatus.FAILED
        job_run.error_message = str(e)
        job_run.ended_at = datetime.utcnow()
        db.commit()
        raise
    finally:
        db.close()
