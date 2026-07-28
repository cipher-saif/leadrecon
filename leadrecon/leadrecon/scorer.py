"""
scorer.py — BANT-weighted ICP scoring.

Combines fingerprint.FingerprintResult + enrich.EnrichmentResult into a
single 0-100 lead score, plus a human-readable "why this score" explanation
per lead (this is the piece an interviewer will ask you to walk through).
"""

from dataclasses import dataclass, field

from .config import (
    ICP_WEIGHTS,
    TARGET_EMPLOYEE_MIN,
    TARGET_EMPLOYEE_MAX,
    TARGET_INDUSTRIES,
    OPPORTUNITY_TECH_SIGNALS,
    HOT_THRESHOLD,
    WARM_THRESHOLD,
)


@dataclass
class ScoredLead:
    company_name: str
    domain: str
    score: int
    tier: str
    reasons: list = field(default_factory=list)
    detected_tech: list = field(default_factory=list)
    employee_count: int | None = None
    industry: str | None = None
    trigger_events: list = field(default_factory=list)
    error: str | None = None


def _score_company_size(employee_count) -> tuple[float, str]:
    if employee_count is None:
        return 0.5, "Company size unknown — neutral score"
    if TARGET_EMPLOYEE_MIN <= employee_count <= TARGET_EMPLOYEE_MAX:
        return 1.0, f"Company size ({employee_count}) is in target range"
    return 0.2, f"Company size ({employee_count}) is outside target range"


def _score_industry(industry) -> tuple[float, str]:
    if not industry:
        return 0.5, "Industry unknown — neutral score"
    match = any(target in industry for target in TARGET_INDUSTRIES)
    if match:
        return 1.0, f"Industry '{industry}' matches ICP"
    return 0.3, f"Industry '{industry}' does not match target verticals"


def _score_tech_stack(detected_tech) -> tuple[float, str]:
    if not detected_tech:
        return 0.4, "No tech signals detected"
    overlap = [t for t in detected_tech if t.lower() in OPPORTUNITY_TECH_SIGNALS]
    if overlap:
        return 1.0, f"Detected opportunity-signal tech: {', '.join(overlap)}"
    return 0.5, f"Detected tech ({', '.join(detected_tech)}) — no direct opportunity signal"


def _score_trigger_event(trigger_events) -> tuple[float, str]:
    if trigger_events:
        top = trigger_events[0].get("title", "recent news")
        return 1.0, f"Recent trigger event found: {top}"
    return 0.3, "No recent trigger event found"


def _score_site_health(missing_security_headers, ssl_days_to_expiry) -> tuple[float, str]:
    issues = []
    if missing_security_headers:
        issues.append(f"missing {len(missing_security_headers)} security header(s)")
    if ssl_days_to_expiry is not None and ssl_days_to_expiry < 30:
        issues.append(f"SSL cert expiring in {ssl_days_to_expiry} days")
    if issues:
        return 1.0, "Site health opportunity: " + "; ".join(issues)
    return 0.4, "No notable site health issues detected"


def score_lead(company_name, domain, fingerprint_result, enrichment_result) -> ScoredLead:
    """Combine fingerprint + enrichment data into a single weighted score."""
    if fingerprint_result.error and not fingerprint_result.reachable:
        return ScoredLead(
            company_name=company_name,
            domain=domain,
            score=0,
            tier="Unreachable",
            reasons=[f"Site unreachable: {fingerprint_result.error}"],
            error=fingerprint_result.error,
        )

    size_score, size_reason = _score_company_size(enrichment_result.employee_count)
    industry_score, industry_reason = _score_industry(enrichment_result.industry)
    tech_score, tech_reason = _score_tech_stack(fingerprint_result.detected_tech)
    trigger_score, trigger_reason = _score_trigger_event(enrichment_result.trigger_events)
    health_score, health_reason = _score_site_health(
        fingerprint_result.missing_security_headers,
        fingerprint_result.ssl_days_to_expiry,
    )

    weighted_total = (
        size_score * ICP_WEIGHTS["company_size_match"]
        + industry_score * ICP_WEIGHTS["industry_match"]
        + tech_score * ICP_WEIGHTS["tech_stack_signal"]
        + trigger_score * ICP_WEIGHTS["trigger_event"]
        + health_score * ICP_WEIGHTS["site_health_signal"]
    )
    final_score = round(weighted_total)

    if final_score >= HOT_THRESHOLD:
        tier = "Hot"
    elif final_score >= WARM_THRESHOLD:
        tier = "Warm"
    else:
        tier = "Cold"

    return ScoredLead(
        company_name=company_name,
        domain=domain,
        score=final_score,
        tier=tier,
        reasons=[size_reason, industry_reason, tech_reason, trigger_reason, health_reason],
        detected_tech=fingerprint_result.detected_tech,
        employee_count=enrichment_result.employee_count,
        industry=enrichment_result.industry,
        trigger_events=enrichment_result.trigger_events,
    )
