"""
fingerprint.py — passive tech-stack detection for a company's public website.

Only ever makes normal, low-volume GET requests to pages a browser would
request anyway (homepage HTML + headers). No scanning, no brute-forcing,
no auth bypass — this is the same class of technique BuiltWith/Wappalyzer
use, applied at a small scale for lead research.
"""

import re
import socket
import ssl
import datetime
from dataclasses import dataclass, field

import requests

from .config import REQUEST_TIMEOUT, USER_AGENT

# Signature patterns: name -> list of regexes checked against page HTML/headers
SIGNATURES = {
    "WordPress": [r"wp-content", r"wp-includes", r'name="generator" content="WordPress'],
    "Shopify": [r"cdn\.shopify\.com", r"Shopify\.theme"],
    "Wix": [r"static\.wixstatic\.com", r"wix-code"],
    "Squarespace": [r"squarespace\.com", r"static1\.squarespace\.com"],
    "Webflow": [r"webflow\.com", r"data-wf-page"],
    "HubSpot": [r"js\.hs-scripts\.com", r"hsforms\.net", r"hs-analytics"],
    "Salesforce": [r"force\.com", r"salesforce\.com/sfdc"],
    "Marketo": [r"munchkin\.js", r"marketo\.net"],
    "Google Analytics": [r"google-analytics\.com/analytics\.js", r"gtag\('config'", r"googletagmanager\.com"],
    "Intercom": [r"widget\.intercom\.io"],
    "Drift": [r"js\.driftt\.com"],
    "Cloudflare": [r"cloudflare"],  # also checked via headers
    "React": [r"__NEXT_DATA__", r"react-dom", r"data-reactroot"],
    "Next.js": [r"__NEXT_DATA__", r"/_next/static"],
}

HEADER_SIGNATURES = {
    "server": {
        "cloudflare": "Cloudflare",
        "nginx": "Nginx",
        "apache": "Apache",
        "microsoft-iis": "IIS",
    },
    "x-powered-by": {
        "express": "Express/Node.js",
        "php": "PHP",
        "asp.net": "ASP.NET",
    },
}

SECURITY_HEADERS_TO_CHECK = [
    "strict-transport-security",
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
]


@dataclass
class FingerprintResult:
    domain: str
    reachable: bool = False
    status_code: int | None = None
    detected_tech: list = field(default_factory=list)
    missing_security_headers: list = field(default_factory=list)
    ssl_days_to_expiry: int | None = None
    error: str | None = None


def _normalize_domain(domain: str) -> str:
    domain = domain.strip()
    if not domain.startswith(("http://", "https://")):
        domain = "https://" + domain
    return domain


def _check_ssl_expiry(hostname: str) -> int | None:
    """Return days until the SSL cert expires, or None if unavailable."""
    try:
        hostname = hostname.replace("https://", "").replace("http://", "").split("/")[0]
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=REQUEST_TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
        expiry = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        return (expiry - datetime.datetime.utcnow()).days
    except Exception:
        return None


def fingerprint_site(domain: str) -> FingerprintResult:
    """
    Fetch a site's homepage and detect tech stack + basic security posture.
    Read-only, single GET request — safe for any public website.
    """
    url = _normalize_domain(domain)
    result = FingerprintResult(domain=domain)

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        result.reachable = True
        result.status_code = resp.status_code
        html = resp.text or ""
        headers = {k.lower(): v.lower() for k, v in resp.headers.items()}

        detected = set()

        # Pattern-based detection over HTML
        for tech, patterns in SIGNATURES.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    detected.add(tech)
                    break

        # Header-based detection
        for header_name, mapping in HEADER_SIGNATURES.items():
            header_val = headers.get(header_name, "")
            for needle, tech in mapping.items():
                if needle in header_val:
                    detected.add(tech)

        result.detected_tech = sorted(detected)

        # Security header gap check (informational — useful "opportunity" signal
        # for a security-adjacent seller, and shows off your background)
        missing = [h for h in SECURITY_HEADERS_TO_CHECK if h not in headers]
        result.missing_security_headers = missing

        result.ssl_days_to_expiry = _check_ssl_expiry(url)

    except (requests.RequestException, Exception) as exc:
        result.error = str(exc)

    return result
