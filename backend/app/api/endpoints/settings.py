"""Settings management endpoints."""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.db.models.user import User, UserRole
from app.db.models.settings import Settings
from app.schemas.settings import SettingUpdate, SettingResponse

router = APIRouter(prefix="/settings", tags=["Settings"])

# Default settings for seed data
DEFAULT_SETTINGS = {
    "data_storage": {"value": "database", "type": "string", "description": "Storage mode: database or files"},
    "daily_send_limit": {"value": 30, "type": "integer", "description": "Max emails per day per mailbox"},
    "cooldown_days": {"value": 10, "type": "integer", "description": "Days between emails to same contact"},
    "max_contacts_per_company_job": {"value": 4, "type": "integer", "description": "Max contacts per company per job"},
    "min_salary_threshold": {"value": 40000, "type": "integer", "description": "Minimum salary threshold"},
    "contact_provider": {"value": "mock", "type": "string", "description": "Contact discovery provider"},
    "email_validation_provider": {"value": "mock", "type": "string", "description": "Email validation provider"},
    "email_send_mode": {"value": "mailmerge", "type": "string", "description": "Email send mode"},
    "catch_all_policy": {"value": "exclude", "type": "string", "description": "Policy for catch-all emails"},
    "unsubscribe_footer": {"value": True, "type": "boolean", "description": "Include unsubscribe footer"},
    "company_address": {"value": "123 Business St, City, State 12345", "type": "string", "description": "Company mailing address for footer"},
    "enabled_sources": {"value": ["linkedin", "indeed", "glassdoor"], "type": "list", "description": "Enabled job sources"},
    "target_industries": {
        "value": [
            "Healthcare", "Manufacturing", "Logistics", "Retail", "BFSI",
            "Education", "Engineering", "Automotive", "Construction"
        ],
        "type": "list",
        "description": "Target industries for leads"
    }
}


@router.get("", response_model=List[SettingResponse])
async def list_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR]))
):
    """List all settings."""
    settings = db.query(Settings).order_by(Settings.key).all()
    return [SettingResponse.model_validate(s) for s in settings]


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR]))
):
    """Get setting by key."""
    setting = db.query(Settings).filter(Settings.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )
    return SettingResponse.model_validate(setting)


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    setting_in: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update setting (Admin only)."""
    setting = db.query(Settings).filter(Settings.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )

    setting.value_json = json.dumps(setting_in.value)
    if setting_in.description:
        setting.description = setting_in.description
    setting.updated_by = current_user.email

    db.commit()
    db.refresh(setting)

    return SettingResponse.model_validate(setting)


@router.post("/initialize")
async def initialize_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Initialize default settings (Admin only)."""
    created = 0
    for key, config in DEFAULT_SETTINGS.items():
        existing = db.query(Settings).filter(Settings.key == key).first()
        if not existing:
            setting = Settings(
                key=key,
                value_json=json.dumps(config["value"]),
                type=config["type"],
                description=config.get("description"),
                updated_by=current_user.email
            )
            db.add(setting)
            created += 1

    db.commit()

    return {"message": f"Initialized {created} settings", "total": len(DEFAULT_SETTINGS)}


@router.post("/test-connection/{provider}")
async def test_provider_connection(
    provider: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR]))
):
    """Test connection to a provider."""
    # Import adapters and test connection
    try:
        if provider == "apollo":
            from app.services.adapters.contact_discovery.apollo import ApolloAdapter
            adapter = ApolloAdapter()
            result = adapter.test_connection()
        elif provider == "seamless":
            from app.services.adapters.contact_discovery.seamless import SeamlessAdapter
            adapter = SeamlessAdapter()
            result = adapter.test_connection()
        elif provider == "neverbounce":
            from app.services.adapters.email_validation.neverbounce import NeverBounceAdapter
            adapter = NeverBounceAdapter()
            result = adapter.test_connection()
        elif provider == "zerobounce":
            from app.services.adapters.email_validation.zerobounce import ZeroBounceAdapter
            adapter = ZeroBounceAdapter()
            result = adapter.test_connection()
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}

        return {"status": "success" if result else "failed", "provider": provider}
    except Exception as e:
        return {"status": "error", "message": str(e), "provider": provider}
