# Cold-Email Automation System - Architecture & Data Flow Documentation

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Database Schema & Relationships](#4-database-schema--relationships)
5. [Pipeline Architecture](#5-pipeline-architecture)
6. [Data Flow - Stage by Stage](#6-data-flow---stage-by-stage)
7. [Provider Adapter System](#7-provider-adapter-system)
8. [API Endpoints](#8-api-endpoints)
9. [Business Rules & Compliance](#9-business-rules--compliance)
10. [Module Interconnections](#10-module-interconnections)
11. [Frontend Pages](#11-frontend-pages)
12. [Configuration & Settings](#12-configuration--settings)

---

## 1. System Overview

The Cold-Email Automation System is a comprehensive platform designed for Exzelon Research Analysts to automate the process of:

- **Lead Sourcing**: Scraping job postings from multiple job boards
- **Contact Discovery**: Finding decision-makers at target companies
- **Email Validation**: Verifying email addresses before outreach
- **Outreach Execution**: Sending personalized emails with compliance controls

### Key Features

- Multi-source job board integration (LinkedIn, Indeed, Glassdoor, Simply Hired)
- Contact enrichment via Apollo.io and Seamless.ai
- Email validation through NeverBounce and ZeroBounce
- Compliance controls (bounce rate, cooldown, suppression lists)
- Role-Based Access Control (RBAC)
- Real-time dashboard with KPIs
- Pipeline execution tracking and monitoring

---

## 2. Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | REST API server |
| ORM | SQLAlchemy | Database operations |
| Authentication | JWT + Argon2 | Secure auth & password hashing |
| Task Queue | BackgroundTasks | Async pipeline execution |
| Validation | Pydantic | Request/response validation |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 14 | React-based web application |
| Styling | Tailwind CSS | Utility-first CSS |
| State | Zustand | Client-side state management |
| HTTP Client | Axios | API communication |

### Infrastructure
| Component | Technology | Purpose |
|-----------|------------|---------|
| Database | MySQL 8.0 | Primary data storage |
| Cache | Redis 7 | Session & rate limit caching |
| Containerization | Docker Compose | Service orchestration |

---

## 3. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Next.js)                               │
│                                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │Dashboard │ │  Leads   │ │ Clients  │ │ Contacts │ │Validation│        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                                   │
│  │ Outreach │ │Pipelines │ │ Settings │                                   │
│  └──────────┘ └──────────┘ └──────────┘                                   │
└─────────────────────────────────┬──────────────────────────────────────────┘
                                  │ REST API (HTTP/JSON)
                                  │
┌─────────────────────────────────▼──────────────────────────────────────────┐
│                           BACKEND (FastAPI)                                │
│                                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   API Layer     │  │  Service Layer  │  │  Provider Layer │            │
│  │                 │  │                 │  │                 │            │
│  │ /api/v1/leads   │  │ lead_sourcing   │  │ JobSourceAdapter│            │
│  │ /api/v1/clients │  │ contact_enrich  │  │ ContactAdapter  │            │
│  │ /api/v1/contacts│  │ email_validate  │  │ ValidationAdapter│           │
│  │ /api/v1/outreach│  │ outreach        │  │ EmailSendAdapter│            │
│  │ /api/v1/pipeline│  │                 │  │                 │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│           │                    │                    │                      │
│  ┌────────▼────────────────────▼────────────────────▼────────┐            │
│  │                    Database Layer (SQLAlchemy)            │            │
│  └───────────────────────────┬───────────────────────────────┘            │
└──────────────────────────────┼─────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────────────────────┐
│                         DATA LAYER                                         │
│  ┌─────────────┐  ┌─────────────┐                                         │
│  │   MySQL     │  │   Redis     │                                         │
│  │  Database   │  │   Cache     │                                         │
│  └─────────────┘  └─────────────┘                                         │
└────────────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                                     │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │ LinkedIn  │ │  Indeed   │ │  Apollo   │ │NeverBounce│ │   SMTP    │   │
│  │ Jobs API  │ │ Jobs API  │ │    API    │ │    API    │ │  Server   │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema & Relationships

### Entity Relationship Diagram

```
┌──────────────────────┐         ┌──────────────────────┐
│     ClientInfo       │         │     LeadDetails      │
│    (Companies)       │◄───────►│   (Job Postings)     │
├──────────────────────┤  1:N    ├──────────────────────┤
│ PK: client_id        │         │ PK: lead_id          │
│ client_name (unique) │─────────│ FK: client_name      │
│ status               │         │ job_title            │
│ client_category      │         │ state                │
│ industry             │         │ lead_status          │
│ company_size         │         │ posting_date         │
│ location_state       │         │ job_link (unique)    │
│ service_count        │         │ salary_min/max       │
│ start_date           │         │ contact_email        │
│ end_date             │         │ first_name           │
└──────────────────────┘         │ last_name            │
         │                       │ source               │
         │                       └──────────┬───────────┘
         │ 1:N                              │ 1:N
         ▼                                  │
┌──────────────────────┐                    │
│   ContactDetails     │◄───────────────────┘
│  (Decision Makers)   │
├──────────────────────┤         ┌──────────────────────┐
│ PK: contact_id       │         │ EmailValidationResult│
│ FK: client_name      │    1:1  │   (Email Checks)     │
│ first_name           │         ├──────────────────────┤
│ last_name            │         │ PK: validation_id    │
│ title                │         │ email (indexed)      │
│ email ───────────────┼────────►│ provider             │
│ phone                │         │ status               │
│ location_state       │         │ sub_status           │
│ priority_level       │         │ raw_response_json    │
│ validation_status    │◄────────│ validated_at         │
│ last_outreach_at     │         └──────────────────────┘
│ source               │
└──────────┬───────────┘
           │
           │ 1:N
           ▼
┌──────────────────────┐         ┌──────────────────────┐
│   OutreachEvent      │         │   SuppressionList    │
│   (Email Sends)      │         │  (Do Not Contact)    │
├──────────────────────┤         ├──────────────────────┤
│ PK: event_id         │         │ PK: suppression_id   │
│ FK: contact_id       │         │ email (unique)       │
│ FK: lead_id          │         │ reason               │
│ sent_at              │         │ expires_at           │
│ channel              │         └──────────────────────┘
│ template_id          │
│ subject              │         ┌──────────────────────┐
│ status               │         │      JobRun          │
│ bounce_reason        │         │  (Pipeline Runs)     │
│ reply_detected_at    │         ├──────────────────────┤
│ skip_reason          │         │ PK: run_id           │
└──────────────────────┘         │ pipeline_name        │
                                 │ status               │
┌──────────────────────┐         │ started_at           │
│       User           │         │ ended_at             │
│  (Authentication)    │         │ counters_json        │
├──────────────────────┤         │ error_message        │
│ PK: user_id          │         │ triggered_by         │
│ email (unique)       │         └──────────────────────┘
│ password_hash        │
│ full_name            │         ┌──────────────────────┐
│ role (RBAC)          │         │      Settings        │
│ is_active            │         │  (Configuration)     │
│ last_login_at        │         ├──────────────────────┤
└──────────────────────┘         │ PK: key              │
                                 │ value_json           │
                                 │ type                 │
                                 │ description          │
                                 │ updated_by           │
                                 └──────────────────────┘
```

### Model Definitions

#### LeadDetails
Stores job postings scraped from various sources.

| Field | Type | Description |
|-------|------|-------------|
| lead_id | INT (PK) | Auto-increment primary key |
| client_name | VARCHAR(255) | Company name (indexed) |
| job_title | VARCHAR(255) | Position title |
| state | VARCHAR(2) | US state code |
| posting_date | DATE | When job was posted |
| job_link | VARCHAR(500) | Unique URL to job posting |
| salary_min | DECIMAL | Minimum salary |
| salary_max | DECIMAL | Maximum salary |
| lead_status | ENUM | NEW, ENRICHED, VALIDATED, SENT, SKIPPED |
| contact_email | VARCHAR(255) | Discovered contact email |
| first_name | VARCHAR(100) | Contact first name |
| last_name | VARCHAR(100) | Contact last name |
| contact_title | VARCHAR(255) | Contact job title |
| source | VARCHAR(50) | linkedin, indeed, glassdoor, etc. |

#### ClientInfo
Tracks companies and their engagement category.

| Field | Type | Description |
|-------|------|-------------|
| client_id | INT (PK) | Auto-increment primary key |
| client_name | VARCHAR(255) | Unique company name |
| status | ENUM | ACTIVE, INACTIVE |
| client_category | ENUM | REGULAR, OCCASIONAL, PROSPECT, DORMANT |
| industry | VARCHAR(100) | Industry classification |
| company_size | VARCHAR(50) | Employee count range |
| service_count | INT | Number of services used |

**Category Calculation Logic** (based on last 90 days):
- **REGULAR**: >3 unique posting dates
- **OCCASIONAL**: 1-3 unique posting dates
- **PROSPECT**: No recent activity but exists
- **DORMANT**: Inactive for extended period

#### ContactDetails
Decision-makers discovered at companies.

| Field | Type | Description |
|-------|------|-------------|
| contact_id | INT (PK) | Auto-increment primary key |
| client_name | VARCHAR(255) | Company name (FK) |
| first_name | VARCHAR(100) | Contact first name |
| last_name | VARCHAR(100) | Contact last name |
| title | VARCHAR(255) | Job title |
| email | VARCHAR(255) | Email address (indexed) |
| phone | VARCHAR(50) | Phone number |
| location_state | VARCHAR(2) | US state code |
| priority_level | ENUM | P1-P5 (decision-maker hierarchy) |
| validation_status | ENUM | valid, invalid, catch_all, unknown |
| last_outreach_at | DATETIME | Last email sent date |
| source | VARCHAR(50) | apollo, seamless |

**Priority Level Hierarchy**:
| Level | Title Keywords | Description |
|-------|---------------|-------------|
| P1 | Hiring Manager, Talent Acquisition | Direct decision makers |
| P2 | Recruiter, HR Coordinator | Talent team members |
| P3 | HR Manager, HR Director, HRBP | HR leadership |
| P4 | Operations, Plant Manager | Operations leadership |
| P5 | Other titles | Functional managers |

#### OutreachEvent
Records every email send attempt.

| Field | Type | Description |
|-------|------|-------------|
| event_id | INT (PK) | Auto-increment primary key |
| contact_id | INT (FK) | Reference to contact |
| lead_id | INT (FK) | Reference to lead (optional) |
| sent_at | DATETIME | When email was sent |
| channel | ENUM | MAILMERGE, SMTP, M365, GMAIL, API |
| template_id | VARCHAR(100) | Email template used |
| subject | VARCHAR(255) | Email subject line |
| status | ENUM | SENT, REPLIED, BOUNCED, SKIPPED |
| bounce_reason | TEXT | Why email bounced |
| reply_detected_at | DATETIME | When reply was received |
| skip_reason | TEXT | Why contact was skipped |

---

## 5. Pipeline Architecture

### Pipeline Overview

The system uses a sequential 4-stage pipeline architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE EXECUTION FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   STAGE 1   │    │   STAGE 2   │    │   STAGE 3   │    │   STAGE 4   │ │
│  │             │    │             │    │             │    │             │ │
│  │    LEAD     │───►│   CONTACT   │───►│    EMAIL    │───►│  OUTREACH   │ │
│  │  SOURCING   │    │ ENRICHMENT  │    │ VALIDATION  │    │             │ │
│  │             │    │             │    │             │    │             │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘ │
│        │                  │                  │                  │         │
│        ▼                  ▼                  ▼                  ▼         │
│   lead_details      contact_details    email_validation   outreach_events │
│   client_info                             _results                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pipeline Service Files

| Pipeline | Service File | Purpose |
|----------|-------------|---------|
| Lead Sourcing | `lead_sourcing.py` | Fetch and store job postings |
| Contact Enrichment | `contact_enrichment.py` | Find decision-makers |
| Email Validation | `email_validation.py` | Verify email addresses |
| Outreach | `outreach.py` | Send emails or export for mail merge |

### Pipeline Run Tracking

Every pipeline execution is recorded in `job_run` table:

```python
{
    "run_id": 1,
    "pipeline_name": "lead-sourcing",
    "status": "completed",  # pending, running, completed, failed
    "started_at": "2024-01-15T10:00:00Z",
    "ended_at": "2024-01-15T10:05:30Z",
    "counters_json": {
        "inserted": 45,
        "updated": 12,
        "skipped": 3,
        "errors": 0
    },
    "triggered_by": "admin@example.com"
}
```

---

## 6. Data Flow - Stage by Stage

### Stage 1: Lead Sourcing

**Purpose**: Fetch job postings from multiple job boards and normalize data.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LEAD SOURCING PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   INPUTS:                                                                   │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│   │  LinkedIn   │  │   Indeed    │  │  Glassdoor  │  │Simply Hired │       │
│   │   Jobs      │  │   Jobs      │  │    Jobs     │  │    Jobs     │       │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│          │                │                │                │               │
│          └────────────────┼────────────────┼────────────────┘               │
│                           ▼                                                 │
│                  ┌─────────────────────┐                                    │
│                  │  JobSourceAdapter   │                                    │
│                  │  - fetch_jobs()     │                                    │
│                  │  - normalize()      │                                    │
│                  └──────────┬──────────┘                                    │
│                             ▼                                               │
│   PROCESSING:                                                               │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  1. Normalize job data to standard format                        │      │
│   │  2. Deduplicate by:                                              │      │
│   │     - Primary: job_link (if available)                           │      │
│   │     - Fallback: client_name + job_title + state + posting_date   │      │
│   │  3. Calculate client category based on posting frequency         │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                             ▼                                               │
│   OUTPUTS:                                                                  │
│   ┌──────────────────────┐    ┌──────────────────────┐                     │
│   │    lead_details      │    │    client_info       │                     │
│   │   (status = NEW)     │    │  (upsert company)    │                     │
│   └──────────────────────┘    └──────────────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Functions**:
- `run_lead_sourcing_pipeline()`: Main orchestration
- `get_job_source_adapter()`: Factory for job source providers
- `upsert_client()`: Create or update client record
- `export_leads_to_xlsx()`: Export leads to Excel

**Counters Tracked**: inserted, updated, skipped, errors

---

### Stage 2: Contact Enrichment

**Purpose**: Find decision-makers at companies based on job postings.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CONTACT ENRICHMENT PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   INPUT:                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  SELECT * FROM lead_details                                      │      │
│   │  WHERE lead_status = 'NEW' AND first_name IS NULL                │      │
│   └────────────────────────────────┬────────────────────────────────┘      │
│                                    ▼                                        │
│   FOR EACH LEAD:                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  Search for contacts at company using provider API               │      │
│   │                                                                  │      │
│   │  ┌─────────────────────┐    ┌─────────────────────┐             │      │
│   │  │     Apollo.io       │ OR │    Seamless.ai      │             │      │
│   │  │  ContactAdapter     │    │   ContactAdapter    │             │      │
│   │  └──────────┬──────────┘    └──────────┬──────────┘             │      │
│   │             │                          │                         │      │
│   │             └────────────┬─────────────┘                         │      │
│   │                          ▼                                       │      │
│   │             ┌─────────────────────────┐                          │      │
│   │             │  search_contacts()      │                          │      │
│   │             │  - company_name         │                          │      │
│   │             │  - title keywords       │                          │      │
│   │             │  - state filter         │                          │      │
│   │             └─────────────────────────┘                          │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                    ▼                                        │
│   PROCESSING:                                                               │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  1. Receive contact list from provider                           │      │
│   │  2. Assign priority levels (P1-P5) based on title analysis       │      │
│   │  3. Limit to MAX_CONTACTS_PER_COMPANY_PER_JOB (default: 4)       │      │
│   │  4. Check for duplicate emails before inserting                  │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                    ▼                                        │
│   OUTPUTS:                                                                  │
│   ┌──────────────────────┐    ┌──────────────────────┐                     │
│   │   contact_details    │    │    lead_details      │                     │
│   │  (new contacts)      │    │ status = ENRICHED    │                     │
│   │  (with priority)     │    │ contact_email = X    │                     │
│   └──────────────────────┘    └──────────────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Priority Assignment Logic**:
```python
def determine_priority(title: str) -> str:
    title_lower = title.lower()

    # P1: Direct hiring decision makers
    if any(kw in title_lower for kw in ['hiring manager', 'talent acquisition']):
        return 'P1_JOB_POSTER'

    # P2: Recruiting team
    if any(kw in title_lower for kw in ['recruiter', 'hr coordinator', 'talent']):
        return 'P2_HR_TA'

    # P3: HR leadership
    if any(kw in title_lower for kw in ['hr manager', 'hr director', 'hrbp', 'vp hr']):
        return 'P3_HR_MANAGER'

    # P4: Operations
    if any(kw in title_lower for kw in ['operations', 'plant manager', 'production']):
        return 'P4_OPS_LEADER'

    # P5: Default
    return 'P5_FUNCTIONAL'
```

**Counters Tracked**: contacts_found, leads_enriched, skipped, errors

---

### Stage 3: Email Validation

**Purpose**: Verify email addresses are valid and deliverable before outreach.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EMAIL VALIDATION PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   INPUT:                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  SELECT email FROM contact_details                               │      │
│   │  WHERE validation_status IS NULL                                 │      │
│   └────────────────────────────────┬────────────────────────────────┘      │
│                                    ▼                                        │
│   FOR EACH EMAIL:                                                           │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  1. Clean email (lowercase, trim whitespace)                     │      │
│   │  2. Check if already validated (skip if exists)                  │      │
│   │  3. Send to validation provider                                  │      │
│   │                                                                  │      │
│   │  ┌─────────────────────┐    ┌─────────────────────┐             │      │
│   │  │    NeverBounce      │ OR │    ZeroBounce       │             │      │
│   │  │ ValidationAdapter   │    │  ValidationAdapter  │             │      │
│   │  └──────────┬──────────┘    └──────────┬──────────┘             │      │
│   │             │                          │                         │      │
│   │             └────────────┬─────────────┘                         │      │
│   │                          ▼                                       │      │
│   │             ┌─────────────────────────┐                          │      │
│   │             │  validate_email()       │                          │      │
│   │             │  Returns: status,       │                          │      │
│   │             │  sub_status, raw_json   │                          │      │
│   │             └─────────────────────────┘                          │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                    ▼                                        │
│   STATUS MAPPING:                                                           │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  Provider Result    →    System Status    →    Action            │      │
│   │  ─────────────────────────────────────────────────────────────   │      │
│   │  valid              →    VALID            →    Safe to send      │      │
│   │  invalid/disposable →    INVALID          →    Do not send       │      │
│   │  catchall           →    CATCH_ALL        →    Risky (optional)  │      │
│   │  unknown            →    UNKNOWN          →    Manual review     │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                    ▼                                        │
│   OUTPUTS:                                                                  │
│   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐   │
│   │email_validation_   │  │  contact_details   │  │   lead_details     │   │
│   │    results         │  │ validation_status  │  │ status=VALIDATED   │   │
│   │ (full record)      │  │    = "valid"       │  │ (if has valid)     │   │
│   └────────────────────┘  └────────────────────┘  └────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Validation Status Values**:
| Status | Description | Outreach Action |
|--------|-------------|-----------------|
| VALID | Email exists and accepts mail | Safe to send |
| INVALID | Email does not exist | Do not send |
| CATCH_ALL | Domain accepts all addresses | Risky - may bounce |
| UNKNOWN | Could not determine | Manual review needed |

**Counters Tracked**: validated, valid, invalid, catch_all, unknown, errors, estimated_bounce_rate

---

### Stage 4: Outreach

**Purpose**: Execute email outreach with compliance controls.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OUTREACH PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ELIGIBILITY CHECKS:                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │  For each contact, verify ALL conditions:                        │      │
│   │                                                                  │      │
│   │  ┌─────────────────────────────────────────────────────────┐    │      │
│   │  │ ✓ Check 1: NOT in suppression_list                      │    │      │
│   │  │   └─ If suppressed: SKIP with reason                    │    │      │
│   │  ├─────────────────────────────────────────────────────────┤    │      │
│   │  │ ✓ Check 2: validation_status = 'valid'                  │    │      │
│   │  │   └─ If invalid/null: SKIP - must validate first        │    │      │
│   │  ├─────────────────────────────────────────────────────────┤    │      │
│   │  │ ✓ Check 3: Cooldown period (10 days default)            │    │      │
│   │  │   └─ If last_outreach_at > (now - 10 days): SKIP        │    │      │
│   │  ├─────────────────────────────────────────────────────────┤    │      │
│   │  │ ✓ Check 4: Per-company limit (4 contacts/job)           │    │      │
│   │  │   └─ If already sent to 4 contacts: SKIP                │    │      │
│   │  └─────────────────────────────────────────────────────────┘    │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                    ▼                                        │
│   MODE SELECTION:                                                           │
│   ┌─────────────────────────────┬───────────────────────────────────┐      │
│   │       MAILMERGE MODE        │       PROGRAMMATIC SEND MODE      │      │
│   ├─────────────────────────────┼───────────────────────────────────┤      │
│   │                             │                                   │      │
│   │  Export eligible contacts   │  Send via SMTP/API directly      │      │
│   │  to CSV file for external   │                                   │      │
│   │  mail merge tools           │  Rate Limits:                     │      │
│   │                             │  - DAILY_SEND_LIMIT: 30           │      │
│   │  Output:                    │  - Per-run limit configurable     │      │
│   │  - contacts.csv             │                                   │      │
│   │  - template_guide.docx      │  Options:                         │      │
│   │                             │  - dry_run: true/false            │      │
│   │  Channel: MAILMERGE         │  - Channel: SMTP/M365/GMAIL       │      │
│   │                             │                                   │      │
│   └─────────────────────────────┴───────────────────────────────────┘      │
│                                    ▼                                        │
│   OUTPUTS:                                                                  │
│   ┌──────────────────────┐    ┌──────────────────────┐                     │
│   │   outreach_events    │    │   contact_details    │                     │
│   │  status = SENT       │    │ last_outreach_at =   │                     │
│   │  channel = X         │    │    NOW()             │                     │
│   └──────────────────────┘    └──────────────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Outreach Event Statuses**:
| Status | Description |
|--------|-------------|
| SENT | Email successfully sent/exported |
| SKIPPED | Failed eligibility check (with reason) |
| BOUNCED | Email bounced after sending |
| REPLIED | Reply detected from recipient |

**Counters Tracked**: sent, skipped, errors, eligible, exported

---

## 7. Provider Adapter System

The system uses the **Adapter Pattern** to abstract external service integrations:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ADAPTER ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ABSTRACT BASE CLASSES                          │   │
│  │                                                                     │   │
│  │  JobSourceAdapter          ContactDiscoveryAdapter                  │   │
│  │  ├─ fetch_jobs()           ├─ search_contacts()                     │   │
│  │  └─ normalize()            ├─ normalize()                           │   │
│  │                            └─ test_connection()                     │   │
│  │                                                                     │   │
│  │  EmailValidationAdapter    EmailSendAdapter                         │   │
│  │  ├─ validate_email()       ├─ send_email()                          │   │
│  │  ├─ validate_bulk()        ├─ send_bulk()                           │   │
│  │  └─ test_connection()      └─ test_connection()                     │   │
│  │                                                                     │   │
│  │  AIAdapter                                                          │   │
│  │  ├─ generate_email()       (personalized email content)             │   │
│  │  ├─ generate_subject_variations()  (A/B testing)                    │   │
│  │  ├─ analyze_response()     (sentiment/intent analysis)              │   │
│  │  └─ test_connection()                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CONCRETE IMPLEMENTATIONS                         │   │
│  │                                                                     │   │
│  │  Job Sources:              Contact Discovery:                       │   │
│  │  ├─ JSearchAdapter         ├─ ApolloAdapter                         │   │
│  │  ├─ IndeedAdapter          ├─ SeamlessAdapter                       │   │
│  │  └─ MockJobAdapter         └─ MockContactAdapter                    │   │
│  │                                                                     │   │
│  │  Email Validation:         Email Sending:                           │   │
│  │  ├─ NeverBounceAdapter     ├─ SMTPAdapter                           │   │
│  │  ├─ ZeroBounceAdapter      ├─ M365Adapter                           │   │
│  │  └─ MockValidationAdapter  └─ MockEmailAdapter                      │   │
│  │                                                                     │   │
│  │  AI/LLM:                                                            │   │
│  │  ├─ GroqAdapter            (Free, fast - default)                   │   │
│  │  ├─ OpenAIAdapter          (GPT models)                             │   │
│  │  ├─ AnthropicAdapter       (Claude models)                          │   │
│  │  └─ GeminiAdapter          (Google AI)                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Adapter Configuration

Adapters are configured via environment variables:

```bash
# Job Sources
JOB_SOURCE_PROVIDER=jsearch  # or: indeed, mock
JSEARCH_API_KEY=your_rapidapi_key
INDEED_PUBLISHER_ID=your_publisher_id

# AI/LLM Providers (Groq is default - free and fast)
AI_PROVIDER=groq  # or: openai, anthropic, gemini
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key
AI_MODEL=llama-3.1-70b-versatile  # Model varies by provider

# Contact Discovery
CONTACT_PROVIDER=apollo  # or: seamless, mock
APOLLO_API_KEY=your_api_key
SEAMLESS_API_KEY=your_api_key

# Email Validation
EMAIL_VALIDATION_PROVIDER=neverbounce  # or: zerobounce, mock
NEVERBOUNCE_API_KEY=your_api_key
ZEROBOUNCE_API_KEY=your_api_key

# Email Sending
EMAIL_SEND_MODE=smtp  # or: mock
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=password
```

### Standard Data Formats

**Job Data (from JobSourceAdapter)**:
```json
{
    "client_name": "Acme Corp",
    "job_title": "HR Manager",
    "state": "CA",
    "posting_date": "2024-01-15",
    "job_link": "https://linkedin.com/jobs/123",
    "salary_min": 80000,
    "salary_max": 120000,
    "source": "linkedin"
}
```

**Contact Data (from ContactDiscoveryAdapter)**:
```json
{
    "first_name": "Jane",
    "last_name": "Smith",
    "title": "HR Manager",
    "email": "jane.smith@acme.com",
    "phone": "+1-555-123-4567",
    "location_state": "CA",
    "priority_level": "P1_JOB_POSTER",
    "source": "apollo"
}
```

**Validation Result (from EmailValidationAdapter)**:
```json
{
    "email": "jane.smith@acme.com",
    "status": "valid",
    "sub_status": "deliverable",
    "raw_response": { /* provider-specific data */ }
}
```

---

## 8. API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/login` | User login | Public |
| POST | `/register` | User registration | Admin |
| GET | `/me` | Get current user | Authenticated |
| POST | `/logout` | User logout | Authenticated |

### Leads (`/api/v1/leads`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/` | List leads with filtering | Viewer+ |
| GET | `/{lead_id}` | Get single lead | Viewer+ |
| POST | `/` | Create lead | Operator+ |
| PUT | `/{lead_id}` | Update lead | Operator+ |
| DELETE | `/{lead_id}` | Delete lead | Admin |
| GET | `/stats/summary` | Lead statistics | Viewer+ |

**Query Parameters**:
- `status`: Filter by lead status
- `source`: Filter by source
- `state`: Filter by US state
- `client_name`: Filter by company
- `date_from`, `date_to`: Date range
- `search`: Full-text search
- `page`, `limit`: Pagination

### Clients (`/api/v1/clients`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/` | List clients | Viewer+ |
| GET | `/{client_id}` | Get single client | Viewer+ |
| POST | `/` | Create client | Operator+ |
| PUT | `/{client_id}` | Update client | Operator+ |
| DELETE | `/{client_id}` | Delete client | Admin |
| POST | `/{client_id}/refresh-category` | Recalculate category | Operator+ |
| GET | `/stats/summary` | Client statistics | Viewer+ |

### Contacts (`/api/v1/contacts`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/` | List contacts | Viewer+ |
| GET | `/{contact_id}` | Get single contact | Viewer+ |
| POST | `/` | Create contact | Operator+ |
| PUT | `/{contact_id}` | Update contact | Operator+ |
| DELETE | `/{contact_id}` | Delete contact | Admin |
| GET | `/stats/summary` | Contact statistics | Viewer+ |

### Validation (`/api/v1/validation`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/results` | List validation results | Viewer+ |
| GET | `/results/{email}` | Get result for email | Viewer+ |
| POST | `/validate-bulk` | Start bulk validation | Operator+ |
| POST | `/validate-pending-contacts` | Validate all pending | Operator+ |
| GET | `/stats/summary` | Validation statistics | Viewer+ |

### Outreach (`/api/v1/outreach`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/events` | List outreach events | Viewer+ |
| GET | `/events/{event_id}` | Get single event | Viewer+ |
| POST | `/events` | Create event manually | Operator+ |
| POST | `/run-mailmerge` | Start mail merge export | Operator+ |
| POST | `/send-emails` | Start email sending | Admin |
| GET | `/stats/summary` | Outreach statistics | Viewer+ |

### Pipelines (`/api/v1/pipelines`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/runs` | List pipeline runs | Viewer+ |
| GET | `/runs/{run_id}` | Get run details | Viewer+ |
| POST | `/lead-sourcing/run` | Trigger lead sourcing | Operator+ |
| POST | `/lead-sourcing/upload` | Upload leads from file | Operator+ |
| POST | `/contact-enrichment/run` | Trigger enrichment | Operator+ |
| POST | `/email-validation/run` | Trigger validation | Operator+ |
| POST | `/outreach/run` | Trigger outreach | Admin |

### Dashboard (`/api/v1/dashboard`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/kpis` | Get all KPI metrics | Viewer+ |
| GET | `/leads-sourced` | Recent leads | Viewer+ |
| GET | `/contacts-identified` | Recent contacts | Viewer+ |
| GET | `/outreach-sent` | Recent outreach | Viewer+ |
| GET | `/client-categories` | Category breakdown | Viewer+ |
| GET | `/trends` | Trend data | Viewer+ |

### Settings (`/api/v1/settings`)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/` | List all settings | Viewer+ |
| GET | `/{key}` | Get setting by key | Viewer+ |
| PUT | `/{key}` | Update setting | Admin |
| POST | `/initialize` | Initialize defaults | Admin |

---

## 9. Business Rules & Compliance

### Email Deliverability Rules

| Rule | Default Value | Purpose |
|------|---------------|---------|
| Bounce Rate Target | < 2% | Maintain sender reputation |
| Only Send to Valid | Enforced | Prevent bounces |
| Cooldown Period | 10 days | Prevent spam complaints |

### Volume Controls

| Rule | Default Value | Purpose |
|------|---------------|---------|
| Daily Send Limit | 30 emails | ISP rate limiting |
| Max per Company/Job | 4 contacts | Targeted outreach |
| Per-Run Limit | Configurable | Batch control |

### Suppression List

The suppression list prevents outreach to specific emails:

```python
# Suppression reasons
REASONS = [
    'unsubscribed',    # User requested removal
    'bounced',         # Previous bounce
    'complained',      # Spam complaint
    'manual',          # Admin added
    'invalid'          # Known invalid
]

# Check logic
def is_suppressed(email: str) -> bool:
    suppression = db.query(SuppressionList).filter_by(email=email).first()
    if not suppression:
        return False
    if suppression.expires_at and suppression.expires_at < datetime.now():
        return False  # Expired
    return True
```

### Compliance Checklist

Before each outreach:

```
┌─────────────────────────────────────────────────────────────────┐
│                    OUTREACH ELIGIBILITY CHECK                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  □ Email not in suppression list                                │
│    └─ Check: suppression_list WHERE email = ?                   │
│                                                                 │
│  □ Email validation status is 'valid'                           │
│    └─ Check: contact.validation_status = 'valid'                │
│                                                                 │
│  □ Cooldown period has passed                                   │
│    └─ Check: contact.last_outreach_at < (NOW - 10 days)         │
│                                                                 │
│  □ Company contact limit not exceeded                           │
│    └─ Check: COUNT(outreach_events for company/job) < 4         │
│                                                                 │
│  □ Daily send limit not exceeded                                │
│    └─ Check: COUNT(today's sends) < DAILY_SEND_LIMIT            │
│                                                                 │
│  All checks pass? → ELIGIBLE for outreach                       │
│  Any check fails? → SKIP with reason logged                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Module Interconnections

### Service Layer Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER INTERCONNECTIONS                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  lead_sourcing.py                                                           │
│    ├── READS FROM: External job board APIs (via JobSourceAdapter)           │
│    ├── WRITES TO: lead_details (INSERT/UPDATE)                              │
│    ├── WRITES TO: client_info (UPSERT)                                      │
│    └── WRITES TO: job_run (pipeline tracking)                               │
│                                                                             │
│                              ↓ (leads with status=NEW)                      │
│                                                                             │
│  contact_enrichment.py                                                      │
│    ├── READS FROM: lead_details (WHERE status=NEW, first_name IS NULL)      │
│    ├── USES: ContactDiscoveryAdapter (Apollo/Seamless)                      │
│    ├── WRITES TO: contact_details (INSERT)                                  │
│    ├── UPDATES: lead_details (status→ENRICHED, contact info populated)      │
│    └── WRITES TO: job_run (pipeline tracking)                               │
│                                                                             │
│                              ↓ (contacts with validation_status=NULL)       │
│                                                                             │
│  email_validation.py                                                        │
│    ├── READS FROM: contact_details (WHERE validation_status IS NULL)        │
│    ├── READS FROM: email_validation_results (check if already validated)    │
│    ├── USES: EmailValidationAdapter (NeverBounce/ZeroBounce)                │
│    ├── WRITES TO: email_validation_results (INSERT)                         │
│    ├── UPDATES: contact_details (validation_status)                         │
│    ├── UPDATES: lead_details (status→VALIDATED if valid contact exists)     │
│    └── WRITES TO: job_run (pipeline tracking)                               │
│                                                                             │
│                              ↓ (contacts with validation_status=valid)      │
│                                                                             │
│  outreach.py                                                                │
│    ├── READS FROM: contact_details (WHERE validation_status='valid')        │
│    ├── READS FROM: suppression_list (eligibility check)                     │
│    ├── READS FROM: outreach_events (cooldown & limit checks)                │
│    ├── USES: EmailSendAdapter (SMTP) OR exports CSV                         │
│    ├── WRITES TO: outreach_events (INSERT)                                  │
│    ├── UPDATES: contact_details (last_outreach_at)                          │
│    └── WRITES TO: job_run (pipeline tracking)                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Transformation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATA TRANSFORMATION FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  EXTERNAL DATA                    INTERNAL STORAGE                          │
│  ─────────────                    ────────────────                          │
│                                                                             │
│  Job Board API Response    →→→    lead_details record                       │
│  {                                {                                         │
│    "company": "Acme",               client_name: "Acme",                    │
│    "title": "HR Manager",           job_title: "HR Manager",                │
│    "location": "CA",                state: "CA",                            │
│    "url": "https://..."             job_link: "https://...",                │
│  }                                  lead_status: "NEW"                      │
│                                   }                                         │
│                                                                             │
│  Apollo API Response       →→→    contact_details record                    │
│  {                                {                                         │
│    "first_name": "Jane",            first_name: "Jane",                     │
│    "last_name": "Smith",            last_name: "Smith",                     │
│    "title": "HR Manager",           title: "HR Manager",                    │
│    "email": "jane@acme.com"         email: "jane@acme.com",                 │
│  }                                  priority_level: "P1_JOB_POSTER",        │
│                                     validation_status: NULL                 │
│                                   }                                         │
│                                                                             │
│  NeverBounce Response      →→→    email_validation_results record           │
│  {                                {                                         │
│    "result": "valid",               email: "jane@acme.com",                 │
│    "flags": ["has_mx"]              status: "valid",                        │
│  }                                  provider: "neverbounce",                │
│                                     raw_response_json: {...}                │
│                                   }                                         │
│                                   + UPDATE contact_details                  │
│                                     validation_status: "valid"              │
│                                                                             │
│  Email Send Result         →→→    outreach_events record                    │
│  {                                {                                         │
│    "success": true,                 contact_id: 123,                        │
│    "message_id": "abc123"           status: "SENT",                         │
│  }                                  channel: "SMTP",                        │
│                                     sent_at: "2024-01-15T10:00:00Z"         │
│                                   }                                         │
│                                   + UPDATE contact_details                  │
│                                     last_outreach_at: NOW()                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Status Progression Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STATUS PROGRESSION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LEAD STATUS PROGRESSION:                                                   │
│                                                                             │
│    ┌─────┐     ┌──────────┐     ┌───────────┐     ┌──────┐                 │
│    │ NEW │ ──► │ ENRICHED │ ──► │ VALIDATED │ ──► │ SENT │                 │
│    └─────┘     └──────────┘     └───────────┘     └──────┘                 │
│       │             │                 │               │                     │
│       │             │                 │               │                     │
│    Created      Contact           Valid email     Outreach                  │
│    from job     discovered        confirmed       completed                 │
│    source                                                                   │
│                                                                             │
│  ──────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  CONTACT VALIDATION STATUS:                                                 │
│                                                                             │
│    ┌──────┐     ┌───────────────┐     ┌─────────────────────┐              │
│    │ NULL │ ──► │ Validation    │ ──► │ valid / invalid /   │              │
│    └──────┘     │ Pipeline Runs │     │ catch_all / unknown │              │
│                 └───────────────┘     └─────────────────────┘              │
│                                                                             │
│  ──────────────────────────────────────────────────────────────────────     │
│                                                                             │
│  OUTREACH EVENT STATUS:                                                     │
│                                                                             │
│    ┌──────┐                                                                 │
│    │ SENT │ ──┬──► BOUNCED (bounce detected)                               │
│    └──────┘   │                                                             │
│               └──► REPLIED (reply detected)                                 │
│                                                                             │
│    ┌─────────┐                                                              │
│    │ SKIPPED │ (failed eligibility check - reason logged)                   │
│    └─────────┘                                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Frontend Pages

### Page Structure

```
frontend/src/app/
├── layout.tsx              # Root layout
├── page.tsx                # Landing/redirect
├── login/
│   └── page.tsx            # Login page
└── dashboard/
    ├── layout.tsx          # Dashboard layout with sidebar
    ├── page.tsx            # Main dashboard with KPIs
    ├── leads/
    │   └── page.tsx        # Lead management
    ├── clients/
    │   └── page.tsx        # Client management
    ├── contacts/
    │   └── page.tsx        # Contact management
    ├── validation/
    │   └── page.tsx        # Email validation
    ├── outreach/
    │   └── page.tsx        # Outreach management
    ├── pipelines/
    │   └── page.tsx        # Pipeline execution
    └── settings/
        └── page.tsx        # System settings
```

### Page Descriptions

| Page | Purpose | Key Features |
|------|---------|--------------|
| **Dashboard** | Overview of all KPIs | Stats cards, trend charts, recent activity |
| **Leads** | Manage job postings | List, filter, search, create, edit |
| **Clients** | Manage companies | List, category badges, status tracking |
| **Contacts** | Manage decision-makers | List, priority levels, validation status |
| **Validation** | Email validation | Stats, run pipeline, filter by status |
| **Outreach** | Email campaigns | Stats, mode selection, business rules |
| **Pipelines** | Pipeline control | Run all pipelines, view history |
| **Settings** | Configuration | View/edit system settings |

### Workflow Visualization

Each relevant page displays the current workflow position:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 1. Lead      │ ──► │ 2. Contact   │ ──► │ 3. Email     │ ──► │ 4. Outreach  │
│    Sourcing  │     │    Enrichment│     │    Validation│     │              │
│    [14 leads]│     │  [46 contacts]│     │  [38 valid]  │     │  [25 sent]   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
        ↑                                        ↑
   Leads Page                              Validation Page
                                          (highlighted)
```

---

## 12. Configuration & Settings

### Environment Variables

```bash
# Database
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/ra_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Authentication
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Provider Selection
CONTACT_PROVIDER=apollo          # apollo, seamless, mock
EMAIL_VALIDATION_PROVIDER=neverbounce  # neverbounce, zerobounce, mock
EMAIL_SEND_MODE=smtp             # smtp, mock

# API Keys
APOLLO_API_KEY=your_apollo_key
SEAMLESS_API_KEY=your_seamless_key
NEVERBOUNCE_API_KEY=your_neverbounce_key
ZEROBOUNCE_API_KEY=your_zerobounce_key

# SMTP Configuration
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=password
SMTP_FROM_EMAIL=noreply@example.com
SMTP_FROM_NAME=Exzelon Outreach

# Business Rules
DAILY_SEND_LIMIT=30
COOLDOWN_DAYS=10
MAX_CONTACTS_PER_COMPANY_JOB=4
BOUNCE_RATE_TARGET=2.0
```

### Database Settings Table

Settings stored in `settings` table for runtime configuration:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `daily_send_limit` | INTEGER | 30 | Max emails per day |
| `cooldown_days` | INTEGER | 10 | Days between sends to same contact |
| `max_contacts_per_company_job` | INTEGER | 4 | Max contacts per company/job |
| `bounce_rate_target` | FLOAT | 2.0 | Target bounce rate percentage |
| `contact_provider` | STRING | "mock" | Active contact provider |
| `validation_provider` | STRING | "mock" | Active validation provider |
| `email_send_mode` | STRING | "mock" | Email sending mode |

### RBAC Roles

| Role | Permissions |
|------|-------------|
| **ADMIN** | Full access - all operations |
| **OPERATOR** | Create, read, update - run pipelines |
| **VIEWER** | Read-only access to all data |

---

## Appendix A: Quick Reference

### API Base URL
```
http://localhost:8000/api/v1
```

### Frontend URL
```
http://localhost:3003
```

### Default Credentials
```
Admin: admin@exzelon.com / admin123
Operator: operator@exzelon.com / operator123
Viewer: viewer@exzelon.com / viewer123
```

### Docker Commands
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Restart specific service
docker compose restart web

# Stop all services
docker compose down

# Reset database
docker compose down -v
docker compose up -d
```

### Key File Locations
```
backend/
├── app/
│   ├── api/routes/          # API endpoints
│   ├── db/models/           # Database models
│   ├── services/pipelines/  # Pipeline services
│   └── providers/           # External adapters

frontend/
├── src/
│   ├── app/dashboard/       # Dashboard pages
│   └── lib/api.ts           # API client
```

---

*Document Version: 1.1*
*Last Updated: January 2026*
*System: Cold-Email Automation System for Exzelon Research Analysts*
