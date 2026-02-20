# Practical Usage Guide - Cold-Email Automation System

This guide explains how each module works practically and how to configure them for real-world use.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Module 1: Lead Sourcing](#2-module-1-lead-sourcing)
3. [Module 2: Contact Enrichment](#3-module-2-contact-enrichment)
4. [Module 3: Email Validation](#4-module-3-email-validation)
5. [Module 4: Outreach](#5-module-4-outreach)
6. [AI/LLM Configuration](#6-aillm-configuration)
7. [Configuration via Admin Panel](#7-configuration-via-admin-panel)
8. [End-to-End Workflow Example](#8-end-to-end-workflow-example)

---

## 1. Quick Start

### Access the Application

1. **Frontend**: http://localhost:3003
2. **Login Credentials**:
   - Admin: `admin@exzelon.com` / `admin123`
   - Operator: `operator@exzelon.com` / `operator123`

### Configure Providers (First Time Setup)

1. Navigate to **Settings** page
2. Configure **Contact Discovery Provider** (Apollo or Seamless)
3. Configure **Email Validation Provider** (NeverBounce or ZeroBounce)
4. Configure **Outreach Mode** (Mail Merge or SMTP)
5. Save configuration and test connections

---

## 2. Module 1: Lead Sourcing

### What It Does
Fetches job postings from external sources and stores them as leads in the database.

### Current Implementation Status

| Source | Status | Notes |
|--------|--------|-------|
| Mock Data | **Working** | Generates realistic sample jobs |
| JSearch API | **Working** | Aggregates LinkedIn, Indeed, Glassdoor, ZipRecruiter via RapidAPI |
| Indeed Jobs | **Working** | Requires Indeed Publisher API |
| File Upload | **Working** | Import from XLSX |

### Supported Job Source Providers

#### JSearch API (Recommended)
JSearch is a RapidAPI service that aggregates job postings from multiple sources:
- LinkedIn
- Indeed
- Glassdoor
- ZipRecruiter
- And many more

**Pricing**: Free tier includes 500 requests/month

**How to Get API Key**:
1. Sign up at https://rapidapi.com/
2. Subscribe to JSearch API: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
3. Get your RapidAPI key from the dashboard
4. Configure in Settings → Job Sources → JSearch API Key

#### Indeed Publisher API
Direct access to Indeed job postings.

**How to Get Publisher ID**:
1. Apply for Indeed Publisher Program: https://www.indeed.com/publisher
2. Once approved, get your Publisher ID
3. Configure in Settings → Job Sources → Indeed Publisher ID

### How to Use

#### Option 1: Generate Mock Data (Development/Testing)
1. Go to **Pipelines** page
2. Click **Run Pipeline** under Lead Sourcing
3. System generates 10-25 sample job postings
4. View results on **Leads** page

#### Option 2: Import from Excel File
1. Prepare an XLSX file with columns:
   - `client_name` (Company name)
   - `job_title` (Position)
   - `state` (2-letter US state code)
   - `posting_date` (YYYY-MM-DD)
   - `job_link` (URL - optional)
   - `salary_min`, `salary_max` (optional)
2. Upload via API: `POST /api/v1/pipelines/lead-sourcing/upload`

### Data Flow
```
External Sources / File Upload
        ↓
    Normalization
        ↓
    Deduplication (by job_link or company+title+state+date)
        ↓
    lead_details table (status = NEW)
        ↓
    client_info table (upsert company record)
```

### Business Rules Applied
- **Target Industries**: Healthcare, Manufacturing, Logistics, Retail, BFSI, Education, Engineering, Automotive, Construction
- **Excluded Keywords**: software, developer, engineer, IT, tech (filters out IT jobs)
- **Minimum Salary**: $40,000 (configurable)

---

## 3. Module 2: Contact Enrichment

### What It Does
Finds decision-maker contacts at companies using contact discovery APIs.

### Supported Providers

| Provider | Status | API Key Required | Pricing |
|----------|--------|------------------|---------|
| Mock | **Working** | No | Free (test data) |
| Apollo.io | **Working** | Yes | Pay per credit |
| Seamless.ai | **Working** | Yes | Subscription |

### How to Configure

#### Step 1: Get API Key
- **Apollo.io**: Sign up at https://apollo.io and get API key from Settings
- **Seamless.ai**: Sign up at https://seamless.ai and get API key

#### Step 2: Configure in Admin Panel
1. Go to **Settings** → **Provider Configuration**
2. Select **Contact Discovery Provider**: `Apollo.io` or `Seamless.ai`
3. Enter the **API Key**
4. Click **Test** to verify connection
5. Click **Save Provider Configuration**

### How to Use
1. Ensure you have leads with status = NEW
2. Go to **Pipelines** page
3. Click **Run Pipeline** under Contact Enrichment
4. System searches for contacts at each company
5. View results on **Contacts** page

### Data Flow
```
lead_details (status = NEW, first_name IS NULL)
        ↓
    For each lead:
        ↓
    Apollo/Seamless API search
        ↓
    Priority Level Assignment (P1-P5)
        ↓
    contact_details table (new contacts)
        ↓
    lead_details updated (status = ENRICHED)
```

### Priority Levels
| Level | Title Keywords | Description |
|-------|---------------|-------------|
| P1 | Hiring Manager, Talent Acquisition | Direct decision makers |
| P2 | Recruiter, HR Coordinator | Talent team |
| P3 | HR Manager, HR Director, HRBP | HR leadership |
| P4 | Operations, Plant Manager | Operations leaders |
| P5 | Other titles | Functional managers |

### Business Rules
- **Max 4 contacts** per company per job posting
- Duplicate emails are skipped
- Contacts are linked to the original lead

---

## 4. Module 3: Email Validation

### What It Does
Validates email addresses to ensure deliverability before outreach.

### Supported Providers

| Provider | Status | API Key Required | Cost |
|----------|--------|------------------|------|
| Mock | **Working** | No | Free (simulated) |
| NeverBounce | **Working** | Yes | ~$0.003-0.008/email |
| ZeroBounce | **Working** | Yes | ~$0.007-0.01/email |

### How to Configure

#### Step 1: Get API Key
- **NeverBounce**: https://app.neverbounce.com → API Keys
- **ZeroBounce**: https://www.zerobounce.net → API → API Keys

#### Step 2: Configure in Admin Panel
1. Go to **Settings** → **Provider Configuration**
2. Select **Email Validation Provider**: `NeverBounce` or `ZeroBounce`
3. Enter the **API Key**
4. Click **Test** to verify connection
5. Click **Save Provider Configuration**

### How to Use
1. Go to **Validation** page
2. Click **Run Validation Pipeline**
3. System validates all contacts with `validation_status = NULL`
4. View results with status badges (valid/invalid/catch-all/unknown)

### Data Flow
```
contact_details (validation_status IS NULL)
        ↓
    Deduplicate emails
        ↓
    Provider API validation
        ↓
    email_validation_results table
        ↓
    contact_details.validation_status updated
        ↓
    lead_details (status = VALIDATED if valid contact exists)
```

### Validation Statuses

| Status | Meaning | Outreach Action |
|--------|---------|-----------------|
| **valid** | Email exists and accepts mail | Safe to send |
| **invalid** | Email doesn't exist | Do NOT send |
| **catch_all** | Domain accepts all emails | Risky - configurable |
| **unknown** | Could not verify | Manual review |

### Catch-All Policy (Configurable)
- **Exclude** (Recommended): Don't send to catch-all emails
- **Include**: Send to catch-all emails (higher bounce risk)
- **Flag**: Mark for manual review

---

## 5. Module 4: Outreach

### What It Does
Sends personalized emails to validated contacts or exports them for external mail merge.

### Supported Modes

| Mode | Status | Description |
|------|--------|-------------|
| Mail Merge Export | **Working** | Exports CSV for external tools |
| SMTP Direct Send | **Working** | Sends via configured SMTP server |
| Mock | **Working** | Simulates sending (development) |

### How to Configure SMTP

#### Step 1: Get SMTP Credentials
- **Gmail**: Enable 2FA, create App Password
- **Office 365**: Use your email and password (or App Password)
- **Custom SMTP**: Get credentials from your email provider

#### Step 2: Configure in Admin Panel
1. Go to **Settings** → **Provider Configuration**
2. Select **Send Mode**: `SMTP (Direct Send)`
3. Enter SMTP details:
   - **Host**: smtp.gmail.com (for Gmail)
   - **Port**: 587
   - **Username**: your@email.com
   - **Password**: Your app password
   - **From Email**: your@email.com
   - **From Name**: Your Name
4. Click **Test SMTP Connection**
5. Click **Save Provider Configuration**

### How to Use

#### Mail Merge Mode (Recommended for beginners)
1. Go to **Outreach** page
2. Select **Outreach Mode**: `Mailmerge Export (CSV)`
3. Click **Export for Mailmerge**
4. Download the CSV file from `data/exports/`
5. Import into your mail merge tool (Word, GMass, etc.)

#### SMTP Direct Send Mode
1. Go to **Outreach** page
2. Select **Outreach Mode**: `Programmatic Send`
3. **Enable Dry Run** first to test without sending
4. Click **Run Outreach**
5. Review results
6. Disable Dry Run and run again to send actual emails

### Data Flow
```
contact_details (validation_status = 'valid')
        ↓
    Eligibility Checks:
    ├─ Not in suppression_list?
    ├─ Email validated?
    ├─ Cooldown passed (10 days)?
    └─ Company contact limit OK?
        ↓
    Build email list
        ↓
    Send via SMTP / Export to CSV
        ↓
    outreach_events table (status = SENT)
        ↓
    contact_details.last_outreach_at updated
```

### Business Rules
| Rule | Default Value | Purpose |
|------|---------------|---------|
| Daily Send Limit | 30 | Prevent ISP rate limiting |
| Cooldown Period | 10 days | Prevent spam complaints |
| Max per Company/Job | 4 contacts | Targeted outreach |
| Bounce Rate Target | < 2% | Maintain sender reputation |

---

## 6. AI/LLM Configuration

### What It Does
AI/LLM providers are used for generating personalized email content, subject line variations, and analyzing email responses.

### Supported Providers

| Provider | Status | API Key Required | Pricing | Best For |
|----------|--------|------------------|---------|----------|
| **Groq** (Default) | **Working** | Yes | Free tier (14,400 req/day) | Fast, free inference |
| OpenAI | **Working** | Yes | Pay per token | High quality |
| Anthropic | **Working** | Yes | Pay per token | Best reasoning |
| Gemini | **Working** | Yes | Free tier available | Google integration |

### Provider Details

#### Groq (Recommended Default)
Groq offers extremely fast inference with a generous free tier.

**Features**:
- 14,400 free requests per day
- Extremely fast response times (fastest LLM inference)
- Models: Llama 3.1, Mixtral, Gemma

**Available Models**:
| Model | Description |
|-------|-------------|
| `llama-3.1-70b-versatile` | Best quality (default) |
| `llama-3.1-8b-instant` | Fastest responses |
| `mixtral-8x7b-32768` | Good balance of speed/quality |
| `gemma2-9b-it` | Compact and fast |

**How to Get API Key**:
1. Sign up at https://console.groq.com/
2. Navigate to API Keys
3. Create new API key
4. Configure in Settings → AI/LLM → Groq API Key

#### OpenAI
Industry-standard GPT models with excellent quality.

**Available Models**:
| Model | Description |
|-------|-------------|
| `gpt-4o` | Best quality, multimodal |
| `gpt-4o-mini` | Fast and affordable (recommended) |
| `gpt-4-turbo` | High quality |
| `gpt-3.5-turbo` | Fast and economical |

**How to Get API Key**:
1. Sign up at https://platform.openai.com/
2. Navigate to API Keys
3. Create new API key
4. Configure in Settings → AI/LLM → OpenAI API Key

#### Anthropic Claude
Advanced reasoning and helpful AI models.

**Available Models**:
| Model | Description |
|-------|-------------|
| `claude-3-5-sonnet-20241022` | Best balance (recommended) |
| `claude-3-5-haiku-20241022` | Fast and affordable |
| `claude-3-opus-20240229` | Most capable |

**How to Get API Key**:
1. Sign up at https://console.anthropic.com/
2. Navigate to API Keys
3. Create new API key
4. Configure in Settings → AI/LLM → Anthropic API Key

#### Google Gemini
Google's multimodal AI models.

**Available Models**:
| Model | Description |
|-------|-------------|
| `gemini-1.5-pro` | Most capable |
| `gemini-1.5-flash` | Fast and efficient (recommended) |
| `gemini-1.0-pro` | Stable |

**How to Get API Key**:
1. Go to https://aistudio.google.com/
2. Create API key
3. Configure in Settings → AI/LLM → Gemini API Key

### AI Features

#### 1. Email Content Generation
Generates personalized cold email content based on:
- Contact name and title
- Company name
- Job posting details
- Custom templates

#### 2. Subject Line Variations
Creates A/B test variations of subject lines for better open rates.

#### 3. Response Analysis
Analyzes email responses to determine:
- **Sentiment**: positive, negative, neutral
- **Intent**: interested, not_interested, question, out_of_office, bounce
- **Suggested Action**: follow_up, archive, respond, escalate

### How to Configure

1. Go to **Settings** → **AI/LLM** tab
2. Select your preferred **AI Provider** (Groq recommended)
3. Enter the **API Key** for your chosen provider
4. Select the **Model** to use
5. Click **Test Connection** to verify
6. Click **Save Configuration**

---

## 7. Configuration via Admin Panel

### Settings Page Layout

The Settings page has **7 tabs** for comprehensive configuration:

#### Tab 1: Job Sources
Configure job sourcing providers:
- **Provider Selection**: Mock, JSearch API, Indeed
- **JSearch API Key**: For RapidAPI access to LinkedIn, Indeed, Glassdoor
- **Indeed Publisher ID**: For direct Indeed API access
- **Target States**: US states to search for jobs
- **Target Job Titles**: Job titles to search for

#### Tab 2: AI/LLM
Configure AI providers for email content generation:
- **Provider Selection**: Groq (default), OpenAI, Anthropic, Gemini
- **API Keys**: Enter key for selected provider
- **Model Selection**: Choose specific model variant
- **Test Connection**: Verify API key works

#### Tab 3: Contact Discovery
Configure contact enrichment providers:
- **Provider Selection**: Mock, Apollo.io, Seamless.ai
- **API Key**: Enter provider API key
- **Test Connection**: Verify connectivity

#### Tab 4: Email Validation
Configure email validation providers:
- **Provider Selection**: Mock, NeverBounce, ZeroBounce
- **API Key**: Enter provider API key
- **Test Connection**: Verify connectivity

#### Tab 5: Outreach
Configure email sending:
- **Mode Selection**: Mail Merge Export, SMTP Direct Send, Mock
- **SMTP Configuration**: Host, port, username, password
- **From Email/Name**: Sender details
- **Test SMTP Connection**: Verify SMTP settings

#### Tab 6: Business Rules
Configure outreach limits and policies:
- **Daily Send Limit**: Max emails per day (default: 30)
- **Cooldown Period**: Days between emails to same contact (default: 10)
- **Max Contacts per Company/Job**: Limit contacts per job (default: 4)
- **Minimum Salary Threshold**: Filter low-salary jobs (default: $40,000)
- **Catch-All Policy**: How to handle catch-all emails
- **Unsubscribe Footer**: Include unsubscribe link (required for compliance)

#### Tab 7: All Settings
View all settings as key-value pairs (advanced view).

---

## 8. End-to-End Workflow Example

### Scenario: Find and Contact HR Managers at Healthcare Companies

#### Step 1: Configure Providers
1. Go to Settings
2. Set Contact Provider: **Apollo.io** + API Key
3. Set Validation Provider: **NeverBounce** + API Key
4. Set Outreach Mode: **Mail Merge Export**
5. Save and test connections

#### Step 2: Source Leads
1. Go to Pipelines → Run Lead Sourcing
2. Or upload a list of healthcare companies with job postings
3. Check Leads page - should see new leads with status "NEW"

#### Step 3: Enrich Contacts
1. Go to Pipelines → Run Contact Enrichment
2. Wait for completion
3. Check Contacts page - should see HR contacts with priority levels
4. Leads should now show status "ENRICHED"

#### Step 4: Validate Emails
1. Go to Validation page
2. Click "Run Validation Pipeline"
3. Wait for completion
4. Check validation status - contacts marked as valid/invalid
5. Review stats: aim for >95% valid rate

#### Step 5: Execute Outreach
1. Go to Outreach page
2. Review stats (valid emails available)
3. Select "Mailmerge Export (CSV)"
4. Click "Export for Mailmerge"
5. Download CSV from data/exports/
6. Import into your mail merge tool
7. Send personalized emails

#### Step 6: Track Results
1. Check Outreach page for sent count
2. Monitor bounce rate (target: <2%)
3. Track replies manually or via webhook
4. Add bounced emails to suppression list

---

## Common Questions

### Q: Why use Mock mode?
Mock mode lets you test the entire workflow without using real API credits. Use it for:
- Initial setup and testing
- Training new users
- Development and debugging

### Q: How do I switch from Mock to Real providers?
1. Get API keys from the provider websites
2. Go to Settings → Provider Configuration
3. Select the real provider and enter API key
4. Test connection
5. Save configuration

### Q: Why is Mail Merge recommended over SMTP?
- **Better deliverability**: External tools have better reputation management
- **More control**: Review emails before sending
- **Compliance**: Easier to comply with CAN-SPAM
- **Tracking**: Mail merge tools often include tracking

### Q: What happens if validation fails?
- Invalid emails are marked and excluded from outreach
- Catch-all emails follow your configured policy
- Unknown results can be manually reviewed

### Q: How do I handle bounces?
1. Mark bounced emails in outreach_events (status = BOUNCED)
2. System automatically adds them to suppression list
3. They won't be contacted again

---

## API Keys Required for Production

### Job Sources

| Provider | Get Key From | Approximate Cost |
|----------|-------------|------------------|
| JSearch (RapidAPI) | https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch | Free: 500 req/month, then pay per request |
| Indeed Publisher | https://www.indeed.com/publisher | Free (requires approval) |

### AI/LLM Providers

| Provider | Get Key From | Approximate Cost |
|----------|-------------|------------------|
| Groq | https://console.groq.com/ | Free: 14,400 req/day |
| OpenAI | https://platform.openai.com/ | Pay per token (~$0.01-0.03/1K tokens) |
| Anthropic | https://console.anthropic.com/ | Pay per token (~$0.01-0.03/1K tokens) |
| Gemini | https://aistudio.google.com/ | Free tier available |

### Contact Discovery

| Provider | Get Key From | Approximate Cost |
|----------|-------------|------------------|
| Apollo.io | https://apollo.io/settings | Pay per credit ($0.03-0.06/contact) |
| Seamless.ai | https://seamless.ai | Subscription ($99-499/month) |

### Email Validation

| Provider | Get Key From | Approximate Cost |
|----------|-------------|------------------|
| NeverBounce | https://app.neverbounce.com | Pay per validation ($0.003-0.008) |
| ZeroBounce | https://zerobounce.net | Pay per validation ($0.007-0.01) |

---

*Document Version: 1.1*
*Last Updated: January 2026*
