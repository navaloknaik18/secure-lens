
"""
SecureLens AI - Page Discovery Engine

Discovers pages on a local, authorized demo website.
Only follows HTTP/HTTPS links within the starting origin.
"""

from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag


MAX_PAGES_LIMIT = 20


def validate_local_url(url):
    """Allow local development targets only."""

    if not isinstance(url, str):
        raise ValueError("URL must be a string.")

    parsed = urlparse(url.strip())

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are supported.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed.")

    hostname = (parsed.hostname or "").lower()

    allowed_hosts = {
        "localhost",
        "127.0.0.1",
        "::1"
    }

    if hostname not in allowed_hosts:
        raise ValueError(
            "For this development version, use a local website "
            "such as http://127.0.0.1:5000."
        )

    return parsed


def discover_pages(start_url, max_pages=10):
    """
    Discover same-origin pages without submitting forms
    or interacting with page controls.
    """

    from playwright.sync_api import sync_playwright

    parsed_start = validate_local_url(start_url)

    if not isinstance(max_pages, int):
        raise ValueError("max_pages must be an integer.")

    max_pages = max(1, min(max_pages, MAX_PAGES_LIMIT))

    start_url = urldefrag(start_url.strip())[0]

    queue = deque([start_url])
    visited = set()
    discovered = []
    errors = []

    start_origin = (
        parsed_start.scheme,
        parsed_start.netloc
    )

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(headless=True)

        context = browser.new_context(
            ignore_https_errors=False
        )

        page = context.new_page()

        while queue and len(visited) < max_pages:

            current_url = queue.popleft()

            if current_url in visited:
                continue

            visited.add(current_url)

            try:
                response = page.goto(
                    current_url,
                    wait_until="domcontentloaded",
                    timeout=10000
                )

                if response is None:
                    errors.append({
                        "url": current_url,
                        "error": "No HTTP response was received."
                    })
                    continue

                if response.status >= 400:
                    errors.append({
                        "url": current_url,
                        "error": f"HTTP status {response.status}"
                    })
                    continue

                discovered.append({
                    "url": page.url,
                    "status": response.status,
                    "title": page.title()
                })

                links = page.locator("a[href]").evaluate_all(
                    """
                    elements => elements.map(
                        element => element.href
                    )
                    """
                )

                for link in links:

                    absolute_url = urldefrag(link)[0]
                    parsed_link = urlparse(absolute_url)

                    link_origin = (
                        parsed_link.scheme,
                        parsed_link.netloc
                    )

                    if link_origin != start_origin:
                        continue

                    if absolute_url not in visited:
                        if absolute_url not in queue:
                            queue.append(absolute_url)

            except Exception as error:

                errors.append({
                    "url": current_url,
                    "error": str(error)[:300]
                })

        context.close()
        browser.close()

    return {
        "success": True,
        "start_url": start_url,
        "pages_discovered": len(discovered),
        "pages": discovered,
        "errors": errors
    }
