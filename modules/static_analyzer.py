
"""
SecureLens AI - Static Functionality Analyzer

Inspects HTML without executing JavaScript.
"""

from html.parser import HTMLParser
from urllib.parse import urlparse


class WebsiteHTMLAnalyzer(HTMLParser):

    def __init__(self):
        super().__init__()

        self.findings = []

        self.buttons = 0
        self.links = 0
        self.forms = 0
        self.images = 0
        self.inputs = 0

        self.labels = set()
        self.input_ids = set()
        self.current_label_for = None
        self.label_text = []

    def add_finding(
        self,
        title,
        severity,
        confidence,
        evidence,
        recommendation
    ):

        self.findings.append({
            "title": title,
            "category": "Functionality",
            "severity": severity,
            "confidence": confidence,
            "evidence": evidence,
            "recommendation": recommendation
        })

    def handle_starttag(self, tag, attrs):

        attributes = dict(attrs)

        if tag == "label":
            self.current_label_for = attributes.get("for")
            self.label_text = []

        if tag == "button":

            self.buttons += 1

            button_text = attributes.get("aria-label", "").strip()

            if not button_text and attributes.get("title"):
                button_text = attributes["title"].strip()

            if not button_text:
                self.add_finding(
                    "Button may lack an accessible name",
                    "Low",
                    "Medium",
                    "A button has no aria-label or title attribute. "
                    "Visible text may still provide its name.",
                    "Provide meaningful visible text or an accessible label."
                )

            if attributes.get("type") not in (
                "button",
                "submit",
                "reset"
            ):
                self.add_finding(
                    "Button has no explicit type",
                    "Low",
                    "High",
                    "A button does not specify its type attribute.",
                    "Set type='button' or type='submit' as appropriate."
                )

        if tag == "a":

            self.links += 1

            href = attributes.get("href", "").strip()

            if not href:

                self.add_finding(
                    "Link has no destination",
                    "Low",
                    "High",
                    "An anchor element has no href attribute.",
                    "Add a valid destination or use a button "
                    "for an action."
                )

            elif href == "#":

                self.add_finding(
                    "Placeholder link detected",
                    "Low",
                    "High",
                    "A link uses href='#'.",
                    "Provide a real destination or implement "
                    "the intended interaction."
                )

            elif href.lower().startswith("javascript:"):

                self.add_finding(
                    "JavaScript URL used in link",
                    "Medium",
                    "High",
                    "An anchor uses a javascript: URL.",
                    "Use a button with an event handler instead."
                )

        if tag == "form":

            self.forms += 1

            method = attributes.get("method", "").lower()

            if method not in ("get", "post", "dialog"):
                self.add_finding(
                    "Form has no explicit method",
                    "Informational",
                    "High",
                    "The form does not specify a method.",
                    "Set the intended form submission method."
                )

        if tag == "img":

            self.images += 1

            if "src" not in attributes:

                self.add_finding(
                    "Image has no source",
                    "Low",
                    "High",
                    "An image element has no src attribute.",
                    "Provide a valid image source."
                )

            if "alt" not in attributes:

                self.add_finding(
                    "Image has no alt attribute",
                    "Low",
                    "High",
                    "An image element has no alt attribute.",
                    "Add appropriate alternative text, or alt='' "
                    "if the image is decorative."
                )

        if tag in ("input", "select", "textarea"):

            self.inputs += 1

            element_id = attributes.get("id")

            if element_id:
                self.input_ids.add(element_id)

            if tag == "input" and attributes.get("type") == "hidden":
                return

            aria_label = attributes.get("aria-label", "").strip()
            aria_labelledby = attributes.get(
                "aria-labelledby",
                ""
            ).strip()

            if not aria_label and not aria_labelledby:
                self.add_finding(
                    "Form control may lack an accessible name",
                    "Low",
                    "Medium",
                    f"A {tag} element has no aria-label or "
                    "aria-labelledby attribute. A wrapping label "
                    "may still provide its accessible name.",
                    "Associate the control with a meaningful label."
                )

    def handle_data(self, data):

        if self.current_label_for is not None:
            self.label_text.append(data)

    def handle_endtag(self, tag):

        if tag == "label":

            label_text = "".join(self.label_text).strip()

            if self.current_label_for and label_text:
                self.labels.add(self.current_label_for)

            self.current_label_for = None
            self.label_text = []

    def finish(self):

        for element_id in self.input_ids:

            if element_id not in self.labels:
                # This is only a heuristic. Browser accessibility
                # inspection is needed to confirm the actual name.
                pass

        return {
            "summary": {
                "buttons": self.buttons,
                "links": self.links,
                "forms": self.forms,
                "images": self.images,
                "form_controls": self.inputs
            },
            "findings": self.findings
        }


def analyze_html(html_content):

    if not isinstance(html_content, str):
        raise ValueError("HTML content must be text.")

    if len(html_content) > 2_000_000:
        raise ValueError("HTML content exceeds the size limit.")

    analyzer = WebsiteHTMLAnalyzer()

    analyzer.feed(html_content)

    return analyzer.finish()
