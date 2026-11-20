
"""
SecureLens AI - Browser Functionality Tester

Uses Playwright to inspect a local website.
It does not click controls or submit forms automatically.
"""

from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from modules.page_discovery import (
    discover_pages,
    validate_local_url
)

from modules.static_analyzer import analyze_html


def add_finding(
    findings,
    title,
    severity,
    confidence,
    evidence,
    recommendation
):

    findings.append({
        "title": title,
        "category": "Functionality",
        "severity": severity,
        "confidence": confidence,
        "evidence": evidence,
        "recommendation": recommendation
    })


def inspect_page(url):

    validate_local_url(url)

    findings = []

    browser_errors = []
    failed_requests = []

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            viewport={
                "width": 1366,
                "height": 768
            }
        )

        page.on(
            "pageerror",
            lambda error: browser_errors.append(str(error)[:300])
        )

        page.on(
            "requestfailed",
            lambda request: failed_requests.append({
                "url": request.url[:500],
                "error": str(request.failure)[:200]
            })
        )

        try:

            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=15000
            )

            if response is None:

                add_finding(
                    findings,
                    "Page did not return an HTTP response",
                    "Medium",
                    "High",
                    f"No HTTP response received for {url}",
                    "Check the local server and page availability."
                )

                return {
                    "url": url,
                    "findings": findings,
                    "browser_errors": browser_errors,
                    "failed_requests": failed_requests
                }

            if response.status >= 400:

                add_finding(
                    findings,
                    "Page returned an HTTP error",
                    "Medium",
                    "High",
                    f"HTTP status: {response.status}",
                    "Review the page route and server response."
                )

            # Inspect page structure without interacting with controls.
            page_data = page.locator("body").evaluate(
                """
                body => {

                    const elements = [...body.querySelectorAll(
                        'button, input, select, textarea, a, img, form'
                    )];

                    const buttons = [...body.querySelectorAll('button')];

                    const links = [...body.querySelectorAll('a')];

                    const images = [...body.querySelectorAll('img')];

                    const controls = [...body.querySelectorAll(
                        'input:not([type="hidden"]), select, textarea'
                    )];

                    const forms = [...body.querySelectorAll('form')];

                    return {

                        title: document.title,

                        buttons: buttons.map(button => ({
                            text: button.innerText.trim(),
                            ariaLabel: button.getAttribute('aria-label'),
                            disabled: button.disabled,
                            visible: !!(
                                button.getClientRects().length
                            )
                        })),

                        links: links.map(link => ({
                            text: link.innerText.trim(),
                            href: link.getAttribute('href')
                        })),

                        images: images.map(image => ({
                            src: image.currentSrc || image.src,
                            loaded: image.complete && image.naturalWidth > 0,
                            alt: image.getAttribute('alt')
                        })),

                        controls: controls.map(control => ({
                            tag: control.tagName.toLowerCase(),
                            type: control.type || '',
                            id: control.id,
                            name: control.name,
                            accessibleName:
                                control.labels &&
                                [...control.labels].some(
                                    label => label.innerText.trim()
                                ) ||
                                !!control.getAttribute('aria-label') ||
                                !!control.getAttribute('aria-labelledby')
                        })),

                        forms: forms.length,

                        navigation: document.querySelectorAll(
                            'nav, [role="navigation"]'
                        ).length,

                        viewportWidth: window.innerWidth,

                        documentWidth:
                            document.documentElement.scrollWidth
                    };
                }
                """
            )

            # Check buttons.
            for button in page_data["buttons"]:

                if not button["visible"]:
                    continue

                if (
                    not button["text"]
                    and not button["ariaLabel"]
                ):

                    add_finding(
                        findings,
                        "Visible button has no accessible name",
                        "Low",
                        "High",
                        "A visible button has no text or aria-label.",
                        "Provide meaningful button text or an "
                        "accessible label."
                    )

            # Check links.
            for link in page_data["links"]:

                if not link["href"]:

                    add_finding(
                        findings,
                        "Link has no destination",
                        "Low",
                        "High",
                        f"Link text: {link['text'] or 'No text'}",
                        "Provide a valid destination or use a button."
                    )

            # Check images.
            for image in page_data["images"]:

                if not image["loaded"]:

                    add_finding(
                        findings,
                        "Image failed to load",
                        "Low",
                        "High",
                        f"Image source: {image['src']}",
                        "Check the image path, file availability "
                        "and server response."
                    )

            # Check form controls.
            for control in page_data["controls"]:

                if not control["accessibleName"]:

                    add_finding(
                        findings,
                        "Form control may lack an accessible name",
                        "Low",
                        "High",
                        (
                            f"Element: {control['tag']}, "
                            f"id: {control['id']}, "
                            f"name: {control['name']}"
                        ),
                        "Associate the control with a visible label "
                        "or accessible name."
                    )

            # Check horizontal overflow at the current viewport.
            if (
                page_data["documentWidth"]
                > page_data["viewportWidth"] + 2
            ):

                add_finding(
                    findings,
                    "Horizontal page overflow detected",
                    "Low",
                    "High",
                    (
                        f"Document width: "
                        f"{page_data['documentWidth']}, "
                        f"viewport width: {page_data['viewportWidth']}"
                    ),
                    "Review CSS widths, margins and responsive layouts."
                )

            # Check JavaScript runtime errors.
            for error in browser_errors:

                add_finding(
                    findings,
                    "JavaScript runtime error",
                    "Medium",
                    "High",
                    error,
                    "Review the JavaScript stack trace and correct "
                    "the underlying error."
                )

            # Failed requests are evidence for manual review.
            for failed in failed_requests:

                add_finding(
                    findings,
                    "Browser resource request failed",
                    "Low",
                    "Medium",
                    (
                        f"URL: {failed['url']}; "
                        f"Error: {failed['error']}"
                    ),
                    "Check whether the resource path and server "
                    "response are correct."
                )

            # Run static analysis on the rendered page HTML.
            static_result = analyze_html(page.content())

            for finding in static_result["findings"]:
                findings.append(finding)

            return {
                "url": page.url,
                "http_status": response.status,
                "page_title": page_data["title"],
                "element_summary": {
                    "buttons": len(page_data["buttons"]),
                    "links": len(page_data["links"]),
                    "images": len(page_data["images"]),
                    "form_controls": len(page_data["controls"]),
                    "forms": page_data["forms"],
                    "navigation_regions": page_data["navigation"]
                },
                "findings": findings,
                "browser_errors": browser_errors,
                "failed_requests": failed_requests
            }

        finally:
            browser.close()


def test_website_functionality(
    start_url,
    max_pages=10
):
    """
    Discover and inspect pages on a local website.

    Browser interactions are read-only in this version.
    """

    validate_local_url(start_url)

    discovery = discover_pages(
        start_url,
        max_pages=max_pages
    )

    page_results = []

    for discovered_page in discovery["pages"]:

        result = inspect_page(
            discovered_page["url"]
        )

        page_results.append(result)

    all_findings = []

    for page_result in page_results:

        for finding in page_result["findings"]:

            finding_copy = dict(finding)
            finding_copy["page_url"] = page_result["url"]

            all_findings.append(finding_copy)

    return {
        "success": True,
        "scan_type": "Static analysis + browser inspection",
        "start_url": start_url,
        "pages_discovered": discovery["pages_discovered"],
        "pages_tested": len(page_results),
        "discovery_errors": discovery["errors"],
        "page_results": page_results,
        "findings": all_findings,
        "total_findings": len(all_findings)
    }
