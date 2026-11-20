
"""
SecureLens AI - FixBuilder

Generates reviewable security configuration examples
for supported web frameworks.
"""

from datetime import datetime, timezone


SUPPORTED_FRAMEWORKS = {
    "flask",
    "django",
    "express",
    "php",
    "static"
}

HEADER_CONFIG = {
    "Strict-Transport-Security": (
        "Strict-Transport-Security",
        "max-age=300"
    ),
    "Content-Security-Policy": (
        "Content-Security-Policy-Report-Only",
        "default-src 'self'; object-src 'none'; "
        "base-uri 'self'; frame-ancestors 'self'"
    ),
    "X-Content-Type-Options": (
        "X-Content-Type-Options",
        "nosniff"
    ),
    "X-Frame-Options": (
        "X-Frame-Options",
        "SAMEORIGIN"
    ),
    "Referrer-Policy": (
        "Referrer-Policy",
        "strict-origin-when-cross-origin"
    ),
    "Permissions-Policy": (
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()"
    )
}


def identify_missing_headers(findings):
    """Extract recognized missing security headers."""

    missing = set()

    for finding in findings:
        if not isinstance(finding, dict):
            continue

        title = str(finding.get("title", ""))

        for header in HEADER_CONFIG:
            if title == f"Missing {header} header":
                missing.add(header)

    return sorted(missing)


def generate_header_lines(missing_headers):
    """Generate header configuration lines."""

    lines = []

    for header in missing_headers:
        name, value = HEADER_CONFIG[header]

        lines.append(
            f'    response.headers["{name}"] = "{value}"'
        )

    return lines


def generate_flask(missing_headers):
    lines = [
        '"""Review before adding to your Flask application."""',
        "",
        "from flask import Flask",
        "",
        "app = Flask(__name__)",
        "",
        "@app.after_request",
        "def add_security_headers(response):"
    ]

    header_lines = generate_header_lines(missing_headers)

    if header_lines:
        lines.extend(header_lines)
    else:
        lines.append("    pass")

    lines.extend([
        "    return response",
        ""
    ])

    return "\n".join(lines)


def generate_django(missing_headers):
    lines = [
        '"""Example Django security middleware."""',
        "",
        "class SecurityHeadersMiddleware:",
        "    def __init__(self, get_response):",
        "        self.get_response = get_response",
        "",
        "    def __call__(self, request):",
        "        response = self.get_response(request)"
    ]

    for header in missing_headers:
        name, value = HEADER_CONFIG[header]

        lines.append(
            f'        response["{name}"] = "{value}"'
        )

    lines.extend([
        "        return response",
        ""
    ])

    return "\n".join(lines)


def generate_express(missing_headers):
    lines = [
        "// Review before adding to your Express application.",
        "",
        "function securityHeaders(req, res, next) {"
    ]

    for header in missing_headers:
        name, value = HEADER_CONFIG[header]

        lines.append(
            f'    res.setHeader("{name}", "{value}");'
        )

    lines.extend([
        "    next();",
        "}",
        "",
        "module.exports = securityHeaders;",
        ""
    ])

    return "\n".join(lines)


def generate_php(missing_headers):
    lines = [
        "<?php",
        "// Review before adding to your PHP application.",
        ""
    ]

    for header in missing_headers:
        name, value = HEADER_CONFIG[header]

        lines.append(
            f"header('{name}: {value}');"
        )

    lines.append("")

    return "\n".join(lines)


def generate_nginx(missing_headers):
    lines = [
        "# Review and merge into the correct Nginx server block.",
        "# Do not create duplicate conflicting directives.",
        ""
    ]

    for header in missing_headers:
        name, value = HEADER_CONFIG[header]

        lines.append(
            f'add_header {name} "{value}" always;'
        )

    lines.append("")

    return "\n".join(lines)


def generate_apache(missing_headers):
    lines = [
        "# Review and merge into your Apache virtual host",
        "# or an appropriate .htaccess file.",
        "",
        "<IfModule mod_headers.c>"
    ]

    for header in missing_headers:
        name, value = HEADER_CONFIG[header]

        lines.append(
            f'    Header always set {name} "{value}"'
        )

    lines.extend([
        "</IfModule>",
        ""
    ])

    return "\n".join(lines)


def generate_cookie_guidance(findings):
    titles = {
        str(item.get("title", ""))
        for item in findings
        if isinstance(item, dict)
    }

    lines = [
        "COOKIE SECURITY REVIEW",
        "======================",
        ""
    ]

    if "Cookie missing Secure attribute" in titles:
        lines.extend([
            "Finding: Cookie missing Secure attribute",
            "Recommended action:",
            "- Enable Secure for cookies sent over HTTPS.",
            "- Verify that the application uses HTTPS.",
            ""
        ])

    if "Cookie missing HttpOnly attribute" in titles:
        lines.extend([
            "Finding: Cookie missing HttpOnly attribute",
            "Recommended action:",
            "- Enable HttpOnly for session cookies",
            "  that do not require JavaScript access.",
            ""
        ])

    if len(lines) == 4:
        lines.append("No cookie attribute findings were supplied.")

    return "\n".join(lines)


def generate_readme(framework, missing_headers):
    lines = [
        "SECURELENS AI - GENERATED FIX PACKAGE",
        "=====================================",
        "",
        f"Framework: {framework}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "IMPORTANT:",
        "- These are configuration examples, not automatic fixes.",
        "- Review all generated code before using it.",
        "- Back up your original project first.",
        "- Test changes in a development environment.",
        "- Deploy only after successful testing.",
        "",
        "GENERATED HEADER CONFIGURATIONS",
        "--------------------------------",
    ]

    if missing_headers:
        lines.extend(f"- {header}" for header in missing_headers)
    else:
        lines.append("- No recognized missing headers.")

    lines.extend([
        "",
        "CONTENT SECURITY POLICY:",
        "The generated CSP uses Report-Only mode as a starting point.",
        "Review browser reports and customize the policy before",
        "enforcing it. A generic policy may break website features.",
        "",
        "HSTS:",
        "The generated max-age is deliberately short for initial testing.",
        "Increase it only after confirming HTTPS works correctly.",
        "Do not enable preload without understanding its consequences.",
        "",
        "COOKIE SETTINGS:",
        "See cookie-review.txt for any detected cookie recommendations.",
        "",
        "VERIFICATION:",
        "Reassess your authorized website after applying changes.",
        "A generated file does not prove that a security issue is fixed.",
        ""
    ])

    return "\n".join(lines)


def build_fix_package(findings, framework, https_enabled=False):
    """
    Return a list of generated files.

    Supported frameworks:
    flask, django, express, php, static
    """

    if not isinstance(findings, list):
        raise ValueError("Findings must be a list.")

    framework = str(framework).strip().lower()

    if framework not in SUPPORTED_FRAMEWORKS:
        raise ValueError("Unsupported framework selected.")

    missing_headers = identify_missing_headers(findings)

    # HSTS should only be generated for HTTPS websites.
    if not https_enabled:
        missing_headers = [
            header for header in missing_headers
            if header != "Strict-Transport-Security"
        ]

    if framework == "flask":
        filename = "security_headers.py"
        content = generate_flask(missing_headers)

    elif framework == "django":
        filename = "security_headers_middleware.py"
        content = generate_django(missing_headers)

    elif framework == "express":
        filename = "security-headers.js"
        content = generate_express(missing_headers)

    elif framework == "php":
        filename = "security-headers.php"
        content = generate_php(missing_headers)

    else:
        filename = "nginx-security-headers.conf"
        content = generate_nginx(missing_headers)

    files = [
        {
            "filename": filename,
            "content": content
        },
        {
            "filename": "README.txt",
            "content": generate_readme(
                framework,
                missing_headers
            )
        },
        {
            "filename": "cookie-review.txt",
            "content": generate_cookie_guidance(findings)
        }
    ]

    if framework == "static":
        files.append({
            "filename": "apache-security-headers.conf",
            "content": generate_apache(missing_headers)
        })

    return {
        "success": True,
        "framework": framework,
        "missing_headers": missing_headers,
        "files": files
    }
