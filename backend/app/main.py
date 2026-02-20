"""Main FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import structlog

from app.core.config import settings
from app.api.router import api_router
from app.db.base import engine, Base

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def _seed_warmup_profiles():
    import json
    from app.db.base import SessionLocal
    from app.db.models.warmup_profile import WarmupProfile
    db = SessionLocal()
    try:
        existing = db.query(WarmupProfile).filter(WarmupProfile.is_system == True).count()
        if existing > 0:
            return
        profiles = [
            {
                "name": "Conservative",
                "description": "Slow and safe warmup over 45 days. Best for new domains.",
                "config_json": json.dumps({
                    "total_days": 45,
                    "phase_1": {"days": 10, "min_emails": 1, "max_emails": 3},
                    "phase_2": {"days": 10, "min_emails": 3, "max_emails": 8},
                    "phase_3": {"days": 10, "min_emails": 8, "max_emails": 15},
                    "phase_4": {"days": 15, "min_emails": 15, "max_emails": 25},
                }),
            },
            {
                "name": "Standard",
                "description": "Balanced warmup over 30 days. Recommended for most use cases.",
                "is_default": True,
                "config_json": json.dumps({
                    "total_days": 30,
                    "phase_1": {"days": 7, "min_emails": 2, "max_emails": 5},
                    "phase_2": {"days": 7, "min_emails": 5, "max_emails": 15},
                    "phase_3": {"days": 7, "min_emails": 15, "max_emails": 25},
                    "phase_4": {"days": 9, "min_emails": 25, "max_emails": 35},
                }),
            },
            {
                "name": "Aggressive",
                "description": "Fast warmup over 20 days. For established domains with good reputation.",
                "config_json": json.dumps({
                    "total_days": 20,
                    "phase_1": {"days": 5, "min_emails": 3, "max_emails": 8},
                    "phase_2": {"days": 5, "min_emails": 8, "max_emails": 20},
                    "phase_3": {"days": 5, "min_emails": 20, "max_emails": 35},
                    "phase_4": {"days": 5, "min_emails": 35, "max_emails": 50},
                }),
            },
        ]
        for p in profiles:
            profile = WarmupProfile(
                name=p["name"],
                description=p["description"],
                is_system=True,
                is_default=p.get("is_default", False),
                config_json=p["config_json"],
            )
            db.add(profile)
        db.commit()
        logger.info("Seeded 3 system warmup profiles")
    except Exception as e:
        logger.error("Failed to seed warmup profiles", error=str(e))
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application", app_name=settings.APP_NAME, env=settings.APP_ENV)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    _seed_warmup_profiles()

    # Start warmup scheduler
    try:
        from app.services.warmup.scheduler import init_scheduler
        init_scheduler()
    except Exception as e:
        logger.error("Failed to start warmup scheduler", error=str(e))

    yield

    # Shutdown
    try:
        from app.services.warmup.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.APP_NAME,
    description="Cold-Email Automation System for Research Analysts",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004", "http://127.0.0.1:3000", "http://127.0.0.1:3003", "http://127.0.0.1:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Tracking pixel endpoint
@app.get("/t/{tracking_id}/px.gif")
async def tracking_pixel(tracking_id: str):
    from app.db.base import SessionLocal
    db = SessionLocal()
    try:
        from app.services.warmup.tracking import record_open
        record_open(tracking_id, db)
    except Exception:
        pass
    finally:
        db.close()
    # Return 1x1 transparent GIF
    gif = bytes([0x47,0x49,0x46,0x38,0x39,0x61,0x01,0x00,0x01,0x00,0x80,0x00,0x00,0xff,0xff,0xff,0x00,0x00,0x00,0x21,0xf9,0x04,0x00,0x00,0x00,0x00,0x00,0x2c,0x00,0x00,0x00,0x00,0x01,0x00,0x01,0x00,0x00,0x02,0x02,0x44,0x01,0x00,0x3b])
    return Response(content=gif, media_type="image/gif")


# Tracking link redirect endpoint
@app.get("/t/{tracking_id}/l")
async def tracking_link(tracking_id: str, url: str = ""):
    from app.db.base import SessionLocal
    from fastapi.responses import RedirectResponse
    db = SessionLocal()
    try:
        from app.services.warmup.tracking import record_click
        record_click(tracking_id, url, db)
    except Exception:
        pass
    finally:
        db.close()
    if url:
        import urllib.parse
        decoded_url = urllib.parse.unquote(url)
        return RedirectResponse(url=decoded_url)
    return {"error": "No URL provided"}


@app.get("/")
async def root():
    return {"app": settings.APP_NAME, "version": "2.0.0", "docs": "/api/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "env": settings.APP_ENV}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
