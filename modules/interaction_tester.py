
"""
SecureLens AI - Controlled Interaction Tester

Only tests elements explicitly marked as safe test controls.
Designed for local demo applications.
"""

from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from modules.page_discovery import validate_local_url


def run_interaction_tests(url):

    validate_local_url(url)

    results = []

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(headless=True)

        context = browser.new_context()

        page = context.new_page()

        try:

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=10000
            )

            # Only explicitly marked safe-click controls are tested.
            buttons = page.locator(
                '[data-securelens-test="safe-click"]'
            )

            for index in range(buttons.count()):

                button = buttons.nth(index)

                result_selector = button.get_attribute(
                    "data-securelens-result"
                )

                expected_text = button.get_attribute(
                    "data-securelens-expected"
                )

                if not result_selector or expected_text is None:

                    results.append({
                        "element": f"Safe test button {index + 1}",
                        "status": "Needs review",
                        "evidence": "Missing expected-result configuration."
                    })

                    continue

                try:

                    if not button.is_visible() or not button.is_enabled():

                        results.append({
                            "element": f"Safe test button {index + 1}",
                            "status": "Failed",
                            "evidence": "Button is hidden or disabled."
                        })

                        continue

                    button.click(timeout=3000)

                    result_element = page.locator(result_selector)

                    actual_text = result_element.inner_text(
                        timeout=3000
                    ).strip()

                    if expected_text in actual_text:

                        results.append({
                            "element": f"Safe test button {index + 1}",
                            "status": "Passed",
                            "expected": expected_text,
                            "actual": actual_text
                        })

                    else:

                        results.append({
                            "element": f"Safe test button {index + 1}",
                            "status": "Failed",
                            "expected": expected_text,
                            "actual": actual_text
                        })

                except Exception as error:

                    results.append({
                        "element": f"Safe test button {index + 1}",
                        "status": "Failed",
                        "evidence": str(error)[:300]
                    })

            # Only explicitly marked demo forms are submitted.
            forms = page.locator(
                'form[data-securelens-test="safe-submit"]'
            )

            for index in range(forms.count()):

                form = forms.nth(index)

                result_selector = form.get_attribute(
                    "data-securelens-result"
                )

                expected_text = form.get_attribute(
                    "data-securelens-expected"
                )

                if not result_selector or expected_text is None:

                    results.append({
                        "element": f"Safe test form {index + 1}",
                        "status": "Needs review",
                        "evidence": "Missing expected-result configuration."
                    })

                    continue

                try:

                    # Fill only fields explicitly marked for test use.
                    test_fields = form.locator(
                        "[data-securelens-test-value]"
                    )

                    for field_index in range(test_fields.count()):

                        field = test_fields.nth(field_index)

                        test_value = field.get_attribute(
                            "data-securelens-test-value"
                        )

                        if test_value is not None:
                            field.fill(test_value)

                    submit_button = form.locator(
                        '[data-securelens-submit]'
                    )

                    if submit_button.count() != 1:

                        results.append({
                            "element": f"Safe test form {index + 1}",
                            "status": "Needs review",
                            "evidence": (
                                "Expected exactly one marked submit button."
                            )
                        })

                        continue

                    submit_button.click(timeout=3000)

                    actual_text = page.locator(
                        result_selector
                    ).inner_text(timeout=3000).strip()

                    if expected_text in actual_text:

                        results.append({
                            "element": f"Safe test form {index + 1}",
                            "status": "Passed",
                            "expected": expected_text,
                            "actual": actual_text
                        })

                    else:

                        results.append({
                            "element": f"Safe test form {index + 1}",
                            "status": "Failed",
                            "expected": expected_text,
                            "actual": actual_text
                        })

                except Exception as error:

                    results.append({
                        "element": f"Safe test form {index + 1}",
                        "status": "Failed",
                        "evidence": str(error)[:300]
                    })

        finally:

            context.close()
            browser.close()

    passed = sum(
        item["status"] == "Passed"
        for item in results
    )

    failed = sum(
        item["status"] == "Failed"
        for item in results
    )

    return {
        "success": True,
        "tested_controls": len(results),
        "passed": passed,
        "failed": failed,
        "results": results
    }
