# LeadRecon

**Tech-stack recon and ICP lead-scoring engine — reconnaissance techniques from security engineering, applied to sales qualification.**

## Problem

Sales and BD teams spend hours manually researching leads before outreach: checking company size, industry fit, what tools a company already uses, and whether anything recent (funding, a launch) makes them a hot prospect right now. Most of that research follows a predictable pattern — which means it can be automated.

LeadRecon takes a raw list of company domains and:
1. **Fingerprints their public tech stack** (CMS, analytics, marketing tools, security posture) using the same passive-recon techniques used in security reconnaissance — a single GET request and pattern matching, nothing invasive.
2. **Enriches** each lead with firmographic data (company size, industry) and optional "trigger events" (funding, hiring, launches) via NewsAPI.
3. **Scores** every lead 0–100 against a configurable, BANT-weighted Ideal Customer Profile.
4. **Outputs** a ranked CSV and a clean HTML report — Hot / Warm / Cold tiers, with a plain-English explanation of *why* each lead scored the way it did.

## Why this exists

I'm a cybersecurity student moving into SaaS/tech sales. Rather than just take a sales course, I wanted to prove I could build the actual tooling behind lead generation and qualification — using the passive reconnaissance and fingerprinting skills from my security background, repointed at a sales use case instead of a penetration test.

## Sample output

Run against 6 real public domains (`data/input_leads.csv`):

| Company | Score | Tier | Why |
|---|---|---|---|
| Notion | 74 | 🔥 Hot | Company size in target range |
| Basecamp | 74 | 🔥 Hot | Company size in target range |
| Wikipedia | 60 | Warm | Company size in target range, industry mismatch |
| Stripe | 54 | Warm | Company size outside target range |
| Shopify | 54 | Warm | Company size outside target range |
| HubSpot | 54 | Warm | Company size outside target range |

Full report: `data/output_scored.html` / `data/output_scored.csv`

## Architecture

```
Input CSV (company, domain, size, industry)
        │
        ▼
 fingerprint.py  ──▶  passive tech-stack + security-header detection
        │
        ▼
  enrich.py      ──▶  firmographic data + optional NewsAPI trigger events
        │
        ▼
  scorer.py      ──▶  weighted BANT-style ICP score (0-100) + tier
        │
        ▼
  report.py      ──▶  ranked CSV + HTML report
```

## Setup

```bash
git clone https://github.com/cipher-saif/leadrecon.git
cd leadrecon
pip install -r requirements.txt
```

Optional — enable trigger-event enrichment:
```bash
export NEWSAPI_KEY="your-free-newsapi-key"
```

## Usage

```bash
python main.py --input data/input_leads.csv --output data/output_scored
```

Input CSV format:
```csv
company_name,domain,employee_count,industry
Acme Inc,acme.com,150,software
```

`employee_count` and `industry` are optional — leave them blank and the scorer falls back to a neutral score for that criterion rather than penalizing the lead.

## Configuring your own ICP

Edit `leadrecon/config.py`:

```python
ICP_WEIGHTS = {
    "company_size_match": 25,
    "industry_match": 20,
    "tech_stack_signal": 25,
    "trigger_event": 15,
    "site_health_signal": 15,
}
TARGET_EMPLOYEE_MIN = 20
TARGET_EMPLOYEE_MAX = 1000
TARGET_INDUSTRIES = ["software", "saas", ...]
```

Tune these to whatever you're actually selling — the weights and target ranges are the whole "business logic" of the tool.

## Testing

Unit tests mock all network calls, so the suite runs offline:
```bash
python tests/test_fingerprint.py
```

## What I'd add next (production version)

- Swap the free-tier firmographic fallback for a real API (Clearbit, Crunchbase Pro)
- HubSpot/Zoho CRM API integration to push Hot leads directly into a pipeline
- Slack webhook alert when a lead crosses the Hot threshold
- Async requests (`aiohttp`) to scan larger lead lists faster

## Tech used

Python, `requests`, regex-based fingerprinting, dataclasses, optional NewsAPI integration, CSV/HTML report generation.

## Ethical note

This tool only ever makes a single, ordinary GET request to a site's public homepage — the same request any browser makes when you visit the page. No scanning, no authentication bypass, no non-public data. It's built for legitimate sales research on companies you intend to contact, not surveillance.
