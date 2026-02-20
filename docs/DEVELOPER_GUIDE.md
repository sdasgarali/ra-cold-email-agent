# Developer Guide - Cold-Email Automation System

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Starting the Application

```bash
# Clone and navigate to project
cd RA-01182026

# Start all services
docker compose up -d

# Verify services are running
docker ps
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3003 | admin@exzelon.com / admin123 |
| Backend API | http://localhost:8000 | JWT Token required |
| API Docs | http://localhost:8000/docs | Swagger UI |
| MySQL | localhost:3307 | root / rootpassword |
| Redis | localhost:6380 | No auth |

---

## Project Structure

```
RA-01182026/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/        # API endpoint handlers
│   │   │       ├── auth.py
│   │   │       ├── leads.py
│   │   │       ├── clients.py
│   │   │       ├── contacts.py
│   │   │       ├── validation.py
│   │   │       ├── outreach.py
│   │   │       ├── pipelines.py
│   │   │       ├── dashboard.py
│   │   │       └── settings.py
│   │   ├── core/
│   │   │   ├── config.py      # Configuration settings
│   │   │   ├── security.py    # JWT & password hashing
│   │   │   └── deps.py        # Dependency injection
│   │   ├── db/
│   │   │   ├── models/        # SQLAlchemy models
│   │   │   │   ├── lead.py
│   │   │   │   ├── client.py
│   │   │   │   ├── contact.py
│   │   │   │   ├── outreach.py
│   │   │   │   ├── email_validation.py
│   │   │   │   ├── suppression.py
│   │   │   │   ├── job_run.py
│   │   │   │   ├── settings.py
│   │   │   │   └── user.py
│   │   │   └── session.py     # Database session
│   │   ├── services/
│   │   │   └── pipelines/     # Pipeline services
│   │   │       ├── lead_sourcing.py
│   │   │       ├── contact_enrichment.py
│   │   │       ├── email_validation.py
│   │   │       └── outreach.py
│   │   ├── services/adapters/ # External service adapters
│   │   │   ├── job_sources/   # JSearch, Indeed, Mock
│   │   │   ├── contact_discovery/  # Apollo, Seamless, Mock
│   │   │   ├── email_validation/   # NeverBounce, ZeroBounce, Mock
│   │   │   ├── email_send/    # SMTP, Mock
│   │   │   └── ai/            # Groq, OpenAI, Anthropic, Gemini
│   │   ├── schemas/           # Pydantic schemas
│   │   └── main.py            # FastAPI app entry
│   ├── tests/                 # Test files
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── dashboard/     # Dashboard pages
│   │   │   │   ├── page.tsx           # Main dashboard
│   │   │   │   ├── leads/page.tsx
│   │   │   │   ├── clients/page.tsx
│   │   │   │   ├── contacts/page.tsx
│   │   │   │   ├── validation/page.tsx
│   │   │   │   ├── outreach/page.tsx
│   │   │   │   ├── pipelines/page.tsx
│   │   │   │   └── settings/page.tsx
│   │   │   └── login/page.tsx
│   │   ├── components/        # Reusable components
│   │   └── lib/
│   │       ├── api.ts         # API client
│   │       └── store.ts       # Zustand state
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml          # Service orchestration
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   └── DEVELOPER_GUIDE.md
└── data/                       # Data files & exports
```

---

## Development Workflow

### Local Backend Development

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=mysql+pymysql://root:rootpassword@localhost:3307/ra_db
export REDIS_URL=redis://localhost:6380/0
export SECRET_KEY=dev-secret-key

# Run backend
uvicorn app.main:app --reload --port 8000
```

### Local Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Run frontend
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest -v

# Frontend tests
cd frontend
npm test
```

---

## Adding New Features

### Adding a New API Endpoint

1. **Create/Update Route** (`backend/app/api/routes/`)

```python
# backend/app/api/routes/example.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user

router = APIRouter()

@router.get("/")
def list_items(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Implementation
    return {"items": []}
```

2. **Register Route** (`backend/app/main.py`)

```python
from app.api.routes import example
app.include_router(example.router, prefix="/api/v1/example", tags=["example"])
```

3. **Add Schema** (`backend/app/schemas/`)

```python
# backend/app/schemas/example.py
from pydantic import BaseModel

class ExampleCreate(BaseModel):
    name: str
    value: int

class ExampleResponse(BaseModel):
    id: int
    name: str
    value: int

    class Config:
        from_attributes = True
```

### Adding a New Database Model

1. **Create Model** (`backend/app/db/models/`)

```python
# backend/app/db/models/example.py
from sqlalchemy import Column, Integer, String, DateTime
from app.db.session import Base

class Example(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    value = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
```

2. **Export Model** (`backend/app/db/models/__init__.py`)

```python
from .example import Example
```

3. **Create Migration** (if using Alembic)

```bash
alembic revision --autogenerate -m "Add example table"
alembic upgrade head
```

### Adding a New Provider Adapter

1. **Create Adapter** (`backend/app/providers/`)

```python
# backend/app/providers/example/new_provider.py
from .base import ExampleAdapter

class NewProviderAdapter(ExampleAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.newprovider.com"

    async def fetch_data(self, params: dict) -> list:
        # Implementation
        pass

    def normalize(self, raw_data: dict) -> dict:
        # Normalize to standard format
        pass
```

2. **Register in Factory**

```python
def get_example_adapter(provider: str) -> ExampleAdapter:
    if provider == "new_provider":
        return NewProviderAdapter(settings.NEW_PROVIDER_API_KEY)
    # ... other providers
```

### Adding a New AI/LLM Provider

AI providers are used for generating personalized email content. Here's how to add a new one:

1. **Create Adapter** (`backend/app/services/adapters/ai/`)

```python
# backend/app/services/adapters/ai/new_ai_provider.py
from typing import List, Dict, Any, Optional
import httpx
from app.services.adapters.base import AIAdapter
from app.core.config import settings


class NewAIProviderAdapter(AIAdapter):
    """Adapter for New AI Provider API."""

    BASE_URL = "https://api.newprovider.com/v1"

    MODELS = {
        "model-large": "Large model - best quality",
        "model-small": "Small model - faster",
    }

    DEFAULT_MODEL = "model-large"

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or getattr(settings, 'NEW_PROVIDER_API_KEY', None)
        self.model = model or self.DEFAULT_MODEL

    def test_connection(self) -> bool:
        """Test connection to API."""
        if not self.api_key:
            return False
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.BASE_URL}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10
                )
                return response.status_code == 200
        except Exception:
            return False

    def generate_email(
        self,
        contact_name: str,
        contact_title: str,
        company_name: str,
        job_title: str,
        template: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate personalized cold email content."""
        # Implementation here
        pass

    def generate_subject_variations(
        self,
        base_subject: str,
        count: int = 3
    ) -> List[str]:
        """Generate subject line variations."""
        # Implementation here
        pass

    def analyze_response(
        self,
        email_content: str,
        response_content: str
    ) -> Dict[str, Any]:
        """Analyze email response intent."""
        # Implementation here
        pass
```

2. **Register in `__init__.py`**

```python
# backend/app/services/adapters/ai/__init__.py
from app.services.adapters.ai.new_ai_provider import NewAIProviderAdapter

__all__ = [..., "NewAIProviderAdapter"]
```

3. **Add to Settings Endpoint** (`backend/app/api/endpoints/settings.py`)

```python
elif provider == "new_provider":
    api_key = get_setting_value(db, "new_provider_api_key")
    if not api_key:
        return {"status": "error", "message": "API key not configured"}
    from app.services.adapters.ai.new_ai_provider import NewAIProviderAdapter
    adapter = NewAIProviderAdapter(api_key=api_key)
    result = adapter.test_connection()
    return {"status": "success" if result else "failed", ...}
```

4. **Update Frontend Settings Page** - Add the new provider option to the AI/LLM tab

### Adding a New Frontend Page

1. **Create Page** (`frontend/src/app/dashboard/`)

```tsx
// frontend/src/app/dashboard/example/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

export default function ExamplePage() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const response = await api.get('/example')
      setData(response.data)
    } catch (error) {
      console.error('Failed to fetch:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold">Example Page</h1>
      {/* Content */}
    </div>
  )
}
```

2. **Add to Navigation** (`frontend/src/app/dashboard/layout.tsx`)

```tsx
const navigation = [
  // ... existing items
  { name: 'Example', href: '/dashboard/example', icon: IconComponent },
]
```

---

## Common Tasks

### Resetting the Database

```bash
# Stop services and remove volumes
docker compose down -v

# Restart services (creates fresh database)
docker compose up -d

# Re-seed data
docker compose exec api python -c "from app.db.seed import seed_database; seed_database()"
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f web
docker compose logs -f mysql
```

### Running a Pipeline Manually

```bash
# Via API
curl -X POST "http://localhost:8000/api/v1/pipelines/lead-sourcing/run" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Via Python shell
docker compose exec api python
>>> from app.services.pipelines.lead_sourcing import run_lead_sourcing_pipeline
>>> from app.db.session import SessionLocal
>>> db = SessionLocal()
>>> run_lead_sourcing_pipeline(db, ["indeed", "linkedin"])
```

### Checking Pipeline Status

```bash
# Get all runs
curl "http://localhost:8000/api/v1/pipelines/runs" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get specific run
curl "http://localhost:8000/api/v1/pipelines/runs/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Debugging

### Common Issues

**1. Port Conflicts**
```bash
# Check what's using a port
netstat -ano | findstr :3000  # Windows
lsof -i :3000                 # Mac/Linux

# Update docker-compose.yml ports
```

**2. Database Connection Issues**
```bash
# Check MySQL is running
docker compose ps mysql

# Check logs
docker compose logs mysql

# Verify connection
docker compose exec mysql mysql -u root -p
```

**3. CORS Errors**
- Check `backend/app/main.py` CORS configuration
- Ensure frontend URL is in allowed origins

**4. Authentication Issues**
```bash
# Test login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@exzelon.com&password=admin123"
```

### Useful Docker Commands

```bash
# Enter container shell
docker compose exec api bash
docker compose exec web sh

# Run one-off command
docker compose exec api python -c "print('hello')"

# Rebuild specific service
docker compose build api
docker compose up -d api

# View resource usage
docker stats
```

---

## API Testing with cURL

### Authentication

```bash
# Login and get token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@exzelon.com&password=admin123" | jq -r '.access_token')

echo $TOKEN
```

### CRUD Operations

```bash
# List leads
curl "http://localhost:8000/api/v1/leads" \
  -H "Authorization: Bearer $TOKEN"

# Create lead
curl -X POST "http://localhost:8000/api/v1/leads" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"client_name": "Test Corp", "job_title": "Developer", "state": "CA"}'

# Update lead
curl -X PUT "http://localhost:8000/api/v1/leads/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"lead_status": "ENRICHED"}'

# Delete lead
curl -X DELETE "http://localhost:8000/api/v1/leads/1" \
  -H "Authorization: Bearer $TOKEN"
```

### Pipeline Operations

```bash
# Run lead sourcing
curl -X POST "http://localhost:8000/api/v1/pipelines/lead-sourcing/run?sources=indeed&sources=linkedin" \
  -H "Authorization: Bearer $TOKEN"

# Run contact enrichment
curl -X POST "http://localhost:8000/api/v1/pipelines/contact-enrichment/run" \
  -H "Authorization: Bearer $TOKEN"

# Run email validation
curl -X POST "http://localhost:8000/api/v1/pipelines/email-validation/run" \
  -H "Authorization: Bearer $TOKEN"

# Run outreach (mailmerge mode)
curl -X POST "http://localhost:8000/api/v1/pipelines/outreach/run?mode=mailmerge&dry_run=true" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Environment Configuration

### Development (.env.development)

```bash
# Database
DATABASE_URL=mysql+pymysql://root:rootpassword@localhost:3307/ra_db

# Redis
REDIS_URL=redis://localhost:6380/0

# Auth
SECRET_KEY=dev-secret-key-not-for-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Providers (use mock for development)
JOB_SOURCE_PROVIDER=mock
CONTACT_PROVIDER=mock
EMAIL_VALIDATION_PROVIDER=mock
EMAIL_SEND_MODE=mock

# AI/LLM (Groq is free and recommended for development)
AI_PROVIDER=groq
GROQ_API_KEY=<your-groq-key>  # Get free key at https://console.groq.com

# Debug
DEBUG=true
LOG_LEVEL=DEBUG
```

### Production (.env.production)

```bash
# Database
DATABASE_URL=mysql+pymysql://user:securepass@db-host:3306/ra_db

# Redis
REDIS_URL=redis://redis-host:6379/0

# Auth
SECRET_KEY=<generate-secure-key>
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Job Sources (use JSearch for aggregated job data)
JOB_SOURCE_PROVIDER=jsearch
JSEARCH_API_KEY=<your-rapidapi-key>

# AI/LLM (Groq is free, or use paid providers for higher limits)
AI_PROVIDER=groq
GROQ_API_KEY=<your-key>
# Alternative AI providers (configure one):
# OPENAI_API_KEY=<your-key>
# ANTHROPIC_API_KEY=<your-key>
# GEMINI_API_KEY=<your-key>

# Contact Discovery
CONTACT_PROVIDER=apollo
APOLLO_API_KEY=<your-key>

# Email Validation
EMAIL_VALIDATION_PROVIDER=neverbounce
NEVERBOUNCE_API_KEY=<your-key>

# Email Sending
EMAIL_SEND_MODE=smtp
SMTP_HOST=smtp.provider.com
SMTP_PORT=587
SMTP_USER=<user>
SMTP_PASSWORD=<password>

# Debug
DEBUG=false
LOG_LEVEL=INFO
```

---

## Code Style Guidelines

### Python (Backend)

- Follow PEP 8
- Use type hints
- Docstrings for public functions
- Keep functions small and focused

```python
def process_lead(
    db: Session,
    lead_data: LeadCreate,
    *,
    validate: bool = True
) -> Lead:
    """
    Process and store a new lead.

    Args:
        db: Database session
        lead_data: Lead creation data
        validate: Whether to validate before insert

    Returns:
        Created Lead object

    Raises:
        ValueError: If validation fails
    """
    if validate:
        _validate_lead_data(lead_data)

    lead = Lead(**lead_data.dict())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead
```

### TypeScript (Frontend)

- Use TypeScript strict mode
- Define interfaces for all data
- Use functional components with hooks

```tsx
interface Lead {
  lead_id: number
  client_name: string
  job_title: string
  lead_status: 'NEW' | 'ENRICHED' | 'VALIDATED' | 'SENT'
}

interface LeadsPageProps {
  initialData?: Lead[]
}

export default function LeadsPage({ initialData = [] }: LeadsPageProps) {
  const [leads, setLeads] = useState<Lead[]>(initialData)

  // Component logic
}
```

---

*Document Version: 1.1*
*Last Updated: January 2026*
