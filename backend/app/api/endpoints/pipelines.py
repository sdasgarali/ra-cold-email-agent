"""Pipeline management endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.db.models.user import User, UserRole
from app.db.models.job_run import JobRun, JobStatus

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])


@router.get("/runs")
async def list_job_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    pipeline_name: Optional[str] = None,
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List pipeline job runs."""
    query = db.query(JobRun)

    if pipeline_name:
        query = query.filter(JobRun.pipeline_name == pipeline_name)
    if status_filter:
        query = query.filter(JobRun.status == status_filter)

    runs = query.order_by(JobRun.started_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "run_id": r.run_id,
            "pipeline_name": r.pipeline_name,
            "started_at": r.started_at,
            "ended_at": r.ended_at,
            "status": r.status.value if r.status else None,
            "counters": r.counters_json,
            "error_message": r.error_message,
            "triggered_by": r.triggered_by
        }
        for r in runs
    ]


@router.get("/runs/{run_id}")
async def get_job_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get job run details."""
    run = db.query(JobRun).filter(JobRun.run_id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job run not found"
        )

    return {
        "run_id": run.run_id,
        "pipeline_name": run.pipeline_name,
        "started_at": run.started_at,
        "ended_at": run.ended_at,
        "status": run.status.value if run.status else None,
        "counters": run.counters_json,
        "logs_path": run.logs_path,
        "error_message": run.error_message,
        "triggered_by": run.triggered_by
    }


@router.post("/lead-sourcing/run")
async def run_lead_sourcing(
    background_tasks: BackgroundTasks,
    sources: List[str] = Query(default=["linkedin", "indeed"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR]))
):
    """Run lead sourcing pipeline."""
    from app.services.pipelines.lead_sourcing import run_lead_sourcing_pipeline

    background_tasks.add_task(
        run_lead_sourcing_pipeline,
        sources=sources,
        triggered_by=current_user.email
    )

    return {
        "message": f"Lead sourcing started for sources: {sources}",
        "status": "processing"
    }


@router.post("/lead-sourcing/upload")
async def upload_leads_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR]))
):
    """Upload leads from XLSX file."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be .xlsx or .xls format"
        )

    from app.services.pipelines.lead_sourcing import import_leads_from_file
    import os
    from app.core.config import settings

    # Save uploaded file
    os.makedirs(settings.EXPORT_PATH, exist_ok=True)
    file_path = os.path.join(settings.EXPORT_PATH, f"upload_{file.filename}")

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Import leads
    result = import_leads_from_file(file_path, triggered_by=current_user.email)

    return result


@router.post("/contact-enrichment/run")
async def run_contact_enrichment(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR]))
):
    """Run contact enrichment pipeline."""
    from app.services.pipelines.contact_enrichment import run_contact_enrichment_pipeline

    background_tasks.add_task(
        run_contact_enrichment_pipeline,
        triggered_by=current_user.email
    )

    return {
        "message": "Contact enrichment started",
        "status": "processing"
    }


@router.post("/email-validation/run")
async def run_email_validation(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR]))
):
    """Run email validation pipeline."""
    from app.services.pipelines.email_validation import run_email_validation_pipeline

    background_tasks.add_task(
        run_email_validation_pipeline,
        emails=None,  # Will validate all unvalidated contacts
        provider=None,
        triggered_by=current_user.email
    )

    return {
        "message": "Email validation started",
        "status": "processing"
    }


@router.post("/outreach/run")
async def run_outreach(
    background_tasks: BackgroundTasks,
    mode: str = Query("mailmerge", description="Send mode: mailmerge or send"),
    dry_run: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR]))
):
    """Run outreach pipeline."""
    if mode == "mailmerge":
        from app.services.pipelines.outreach import run_outreach_mailmerge_pipeline
        background_tasks.add_task(
            run_outreach_mailmerge_pipeline,
            triggered_by=current_user.email
        )
    else:
        from app.services.pipelines.outreach import run_outreach_send_pipeline
        background_tasks.add_task(
            run_outreach_send_pipeline,
            dry_run=dry_run,
            limit=30,
            triggered_by=current_user.email
        )

    return {
        "message": f"Outreach pipeline started (mode={mode}, dry_run={dry_run})",
        "status": "processing"
    }
