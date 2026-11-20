
import unittest

from modules.static_analyzer import analyze_html
from modules.page_discovery import validate_local_url


class TestFunctionalityEngine(unittest.TestCase):

    def test_missing_link_destination(self):

        html = """
        <html>
            <body>
                <a>Broken link</a>
            </body>
        </html>
        """

        result = analyze_html(html)

        titles = [
            item["title"]
            for item in result["findings"]
        ]

        self.assertIn(
            "Link has no destination",
            titles
        )

    def test_missing_image_source(self):

        html = """
        <html>
            <body>
                <img alt="Example image">
            </body>
        </html>
        """

        result = analyze_html(html)

        titles = [
            item["title"]
            for item in result["findings"]
        ]

        self.assertIn(
            "Image has no source",
            titles
        )

    def test_missing_button_name(self):

        html = """
        <html>
            <body>
                <button></button>
            </body>
        </html>
        """

        result = analyze_html(html)

        titles = [
            item["title"]
            for item in result["findings"]
        ]

        self.assertIn(
            "Button may lack an accessible name",
            titles
        )

    def test_local_url_allowed(self):

        result = validate_local_url(
            "http://127.0.0.1:5000"
        )

        self.assertEqual(
            result.hostname,
            "127.0.0.1"
        )

    def test_external_url_rejected(self):

        with self.assertRaises(ValueError):
            validate_local_url(
                "https://example.com"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
