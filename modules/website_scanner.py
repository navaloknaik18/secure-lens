
import ipaddress
import socket
from urllib.parse import urlparse, urljoin

import requests


SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "severity": "High",
        "recommendation": (
            "Configure HTTP Strict Transport Security (HSTS) "
            "for HTTPS websites."
        )
    },
    "Content-Security-Policy": {
        "severity": "Medium",
        "recommendation": (
            "Create a suitable Content Security Policy "
            "to help restrict unwanted content sources."
        )
    },
    "X-Content-Type-Options": {
        "severity": "Low",
        "recommendation": (
            "Set X-Content-Type-Options to nosniff."
        )
    },
    "X-Frame-Options": {
        "severity": "Medium",
        "recommendation": (
            "Configure X-Frame-Options or an appropriate "
            "frame-ancestors directive in Content Security Policy."
        )
    },
    "Referrer-Policy": {
        "severity": "Low",
        "recommendation": (
            "Set an appropriate Referrer-Policy "
            "to control referrer information."
        )
    },
    "Permissions-Policy": {
        "severity": "Low",
        "recommendation": (
            "Configure Permissions-Policy to limit "
            "unnecessary browser features."
        )
    }
}

MAX_REDIRECTS = 3
REQUEST_TIMEOUT = (5, 10)

USER_AGENT = "SecureLensAI/1.0 PassiveSecurityAssessment"


def validate_target(url):
    """Validate a public HTTP/HTTPS target."""

    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError("Invalid or excessively long URL.")

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are supported.")

    if not parsed.hostname:
        raise ValueError("URL hostname is missing.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed.")

    try:
        port = parsed.port
    except ValueError:
        raise ValueError("Invalid URL port.")

    if port is not None and port not in (80, 443):
        raise ValueError("Only standard HTTP/HTTPS ports are allowed.")

    hostname = parsed.hostname

    if hostname.lower() == "localhost":
        raise ValueError("Localhost targets are not allowed.")

    try:
        addresses = {
            ipaddress.ip_address(hostname)
        }
    except ValueError:
        try:
            records = socket.getaddrinfo(
                hostname,
                None,
                type=socket.SOCK_STREAM
            )
            addresses = {
                ipaddress.ip_address(record[4][0])
                for record in records
            }
        except socket.gaierror:
            raise ValueError("Unable to resolve the target hostname.")

    if not addresses:
        raise ValueError("No valid target addresses found.")

    for address in addresses:
        if not address.is_global:
            raise ValueError(
                "Private, local, or non-public network targets are blocked."
            )

    return parsed


def add_finding(findings, title, severity, description,
                evidence, recommendation):

    findings.append({
        "title": title,
        "severity": severity,
        "description": description,
        "evidence": evidence,
        "recommendation": recommendation
    })


def analyze_headers(response):
    """Inspect response headers and produce findings."""

    findings = []
    headers = response.headers

    is_https = response.url.lower().startswith("https://")

    if not is_https:
        add_finding(
            findings,
            "HTTPS not enabled",
            "High",
            "The final website address uses HTTP instead of HTTPS.",
            "Final URL uses HTTP.",
            "Configure HTTPS with a valid TLS certificate and redirect HTTP to HTTPS."
        )

    for header, details in SECURITY_HEADERS.items():

        # HSTS is meaningful only over HTTPS.
        if header == "Strict-Transport-Security" and not is_https:
            continue

        value = headers.get(header)

        if not value:
            add_finding(
                findings,
                f"Missing {header} header",
                details["severity"],
                f"The response does not include {header}.",
                f"{header} was not present in the response.",
                details["recommendation"]
            )

    # Review cookies without storing their values.
    cookie_headers = response.raw.headers.getlist("Set-Cookie")

    for cookie_header in cookie_headers:
        lower_cookie = cookie_header.lower()

        if is_https and "secure" not in lower_cookie:
            add_finding(
                findings,
                "Cookie missing Secure attribute",
                "Medium",
                "A response cookie appears to lack the Secure attribute.",
                "A Set-Cookie header was observed without Secure.",
                "Set the Secure attribute on cookies sent over HTTPS."
            )
            break

    for cookie_header in cookie_headers:
        lower_cookie = cookie_header.lower()

        if "httponly" not in lower_cookie:
            add_finding(
                findings,
                "Cookie missing HttpOnly attribute",
                "Low",
                "A response cookie appears to lack HttpOnly.",
                "A Set-Cookie header was observed without HttpOnly.",
                "Set HttpOnly for cookies that do not need JavaScript access."
            )
            break

    server_header = headers.get("Server")

    if server_header:
        add_finding(
            findings,
            "Server information exposed",
            "Informational",
            "The response reveals a server identification header.",
            f"Server header present: {server_header[:120]}",
            "Consider reducing unnecessary server version disclosure."
        )

    powered_by = headers.get("X-Powered-By")

    if powered_by:
        add_finding(
            findings,
            "Technology information exposed",
            "Informational",
            "The response contains an X-Powered-By header.",
            "X-Powered-By header is present.",
            "Consider removing unnecessary technology disclosure headers."
        )

    return findings


def assess_website(url):
    """
    Perform a limited passive assessment.

    Makes only ordinary GET requests for the homepage.
    Does not crawl, submit forms, or exploit vulnerabilities.
    """

    findings = []
    current_url = url
    response = None

    session = requests.Session()
    session.trust_env = False
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html"
    })

    try:
        for redirect_count in range(MAX_REDIRECTS + 1):

            validate_target(current_url)

            response = session.get(
                current_url,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
                stream=True,
                verify=True
            )

            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")

                response.close()
                response = None

                if not location:
                    raise ValueError("Redirect has no destination.")

                if redirect_count == MAX_REDIRECTS:
                    raise ValueError("Maximum redirect limit reached.")

                current_url = urljoin(current_url, location)
                continue

            break

        if response is None:
            raise ValueError("No response received.")

        findings = analyze_headers(response)

        return {
            "success": True,
            "target": url,
            "final_url": response.url,
            "status_code": response.status_code,
            "https_enabled": response.url.startswith("https://"),
            "findings_count": len(findings),
            "findings": findings
        }

    except requests.exceptions.SSLError:
        raise ValueError("TLS certificate verification failed.")

    except requests.exceptions.Timeout:
        raise ValueError("The website request timed out.")

    except requests.exceptions.RequestException:
        raise ValueError("Unable to complete the website request.")

    finally:
        if response is not None:
            response.close()

        session.close()
