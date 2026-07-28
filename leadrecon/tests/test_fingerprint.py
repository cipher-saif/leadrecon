"""
Basic unit tests for fingerprint.py — uses mocked responses, no live network
calls, so this suite runs offline and in CI.
"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from leadrecon.fingerprint import fingerprint_site


def _mock_response(html="", headers=None, status_code=200):
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.status_code = status_code
    mock_resp.headers = headers or {}
    return mock_resp


@patch("leadrecon.fingerprint.requests.get")
@patch("leadrecon.fingerprint._check_ssl_expiry", return_value=120)
def test_detects_wordpress(mock_ssl, mock_get):
    mock_get.return_value = _mock_response(
        html='<html><head><meta name="generator" content="WordPress 6.4"></head></html>',
        headers={"Server": "nginx"},
    )
    result = fingerprint_site("example.com")
    assert result.reachable is True
    assert "WordPress" in result.detected_tech


@patch("leadrecon.fingerprint.requests.get")
@patch("leadrecon.fingerprint._check_ssl_expiry", return_value=90)
def test_detects_missing_security_headers(mock_ssl, mock_get):
    mock_get.return_value = _mock_response(html="<html></html>", headers={})
    result = fingerprint_site("example.com")
    assert "strict-transport-security" in result.missing_security_headers


@patch("leadrecon.fingerprint.requests.get", side_effect=Exception("connection error"))
def test_handles_unreachable_site(mock_get):
    result = fingerprint_site("this-domain-does-not-exist-xyz123.com")
    assert result.reachable is False


if __name__ == "__main__":
    test_detects_wordpress()
    test_detects_missing_security_headers()
    test_handles_unreachable_site()
    print("All tests passed.")
