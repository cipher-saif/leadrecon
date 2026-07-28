"""
Central configuration for LeadRecon.

Edit ICP_WEIGHTS to match whatever product you're prospecting for.
Weights should sum to 100 (not enforced, but keeps scores on a 0-100 scale).
"""

import os

# ---------------------------------------------------------------------------
# ICP (Ideal Customer Profile) scoring weights
# ---------------------------------------------------------------------------
# Each key maps to a scoring function output (0-1) in scorer.py, multiplied
# by the weight below. Tune these to whatever you're actually selling.
ICP_WEIGHTS = {
    "company_size_match": 25,   # employee count falls in target range
    "industry_match": 20,       # industry/vertical matches ICP
    "tech_stack_signal": 25,    # detected stack indicates fit or opportunity
    "trigger_event": 15,        # recent funding / news / hiring signal
    "site_health_signal": 15,   # e.g. outdated stack, weak security headers -> opportunity
}

# Target company size range (employees) — adjust to your ICP
TARGET_EMPLOYEE_MIN = 20
TARGET_EMPLOYEE_MAX = 1000

# Target industries (lowercase, substring-matched against enrichment data)
TARGET_INDUSTRIES = [
    "software",
    "saas",
    "technology",
    "information technology",
    "financial services",
    "healthcare",
    "e-commerce",
]

# Tech signatures we treat as "opportunity" if found (e.g. competitor product,
# or an outdated/legacy tool your product could replace). Edit freely.
OPPORTUNITY_TECH_SIGNALS = [
    "wordpress",
    "wix",
    "squarespace",
    "shopify",
    "hubspot",
    "mailchimp",
    "salesforce",
]

# Score thresholds for bucketing
HOT_THRESHOLD = 70
WARM_THRESHOLD = 40
# below WARM_THRESHOLD -> Cold

# ---------------------------------------------------------------------------
# API keys (all optional — set as environment variables, never hardcode)
# ---------------------------------------------------------------------------
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")          # https://newsapi.org
CLEARBIT_KEY = os.environ.get("CLEARBIT_KEY", "")        # optional, logo/company API
REQUEST_TIMEOUT = 8   # seconds, per HTTP request
USER_AGENT = "LeadRecon/0.1 (educational lead-scoring tool)"
