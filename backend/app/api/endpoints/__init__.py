"""API endpoints package."""
from app.api.endpoints import auth, users, leads, clients, contacts, validation, outreach, settings, pipelines, dashboard

__all__ = [
    "auth", "users", "leads", "clients", "contacts",
    "validation", "outreach", "settings", "pipelines", "dashboard"
]
