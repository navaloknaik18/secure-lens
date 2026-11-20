
import sys
from pathlib import Path

# Add the main project folder to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.website_scanner import analyze_headers


class FakeHeaders(dict):
    def getlist(self, name):
        return []


class FakeResponse:
    url = "https://test.example"
    headers = FakeHeaders({
        "Server": "ExampleServer"
    })

    class Raw:
        headers = FakeHeaders()

    raw = Raw()


def test_missing_security_headers():
    response = FakeResponse()
    findings = analyze_headers(response)

    print("\nSECURELENS AI TEST RESULTS")

    for finding in findings:
        print(finding["severity"], "-", finding["title"])

    assert any(
        item["title"] == "Missing Content-Security-Policy header"
        for item in findings
    )

    assert any(
        item["title"] == "Missing Strict-Transport-Security header"
        for item in findings
    )

    print("\nAll tests passed!")


if __name__ == "__main__":
    test_missing_security_headers()
