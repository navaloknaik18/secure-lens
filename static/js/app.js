
// ============================================================
// SECURELENS AI
// Website Security Assessment Dashboard
// ============================================================


// DOM ELEMENTS
const backendStatus = document.getElementById("backend-status");
const statusIndicator = document.getElementById("status-indicator");
const assessButton = document.getElementById("assess-button");
const message = document.getElementById("assessment-message");


// RESULTS CONTAINER
const resultsContainer = document.createElement("section");

resultsContainer.id = "results-container";
resultsContainer.className = "assessment-card";
resultsContainer.hidden = true;

document.querySelector(".assessment-card").after(resultsContainer);


// UPDATE INTERFACE DESCRIPTION
const description = document.querySelector(".assessment-card > p");

if (description) {
    description.textContent =
        "Run a passive security configuration assessment on an authorized website.";
}


// ============================================================
// 1. BACKEND HEALTH CHECK
// ============================================================

async function checkBackend() {
    try {
        const response = await fetch("/api/health");
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error("Backend unavailable");
        }

        backendStatus.textContent = "Connected · " + data.status;
        statusIndicator.className = "status-indicator online";

    } catch (error) {
        backendStatus.textContent = "Backend connection failed";
        statusIndicator.className = "status-indicator offline";
    }
}


// ============================================================
// 2. SAFE HTML ELEMENT CREATOR
// ============================================================

function createElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    if (text !== undefined) {
        element.textContent = text;
    }

    return element;
}


// ============================================================
// 3. SECURITY SCORE CALCULATION
// ============================================================

function calculateSecurityScore(findings) {

    const weights = {
        High: 25,
        Medium: 10,
        Low: 5,
        Informational: 0
    };

    let deductions = 0;

    findings.forEach(finding => {
        deductions += weights[finding.severity] ?? 0;
    });

    return Math.max(0, 100 - deductions);
}


// ============================================================
// 4. SECURITY SCORE PANEL
// ============================================================

function displaySecurityScore(findings) {

    const score = calculateSecurityScore(findings);

    let rating = "Needs improvement";

    if (score >= 80) {
        rating = "Good configuration score";
    } else if (score >= 60) {
        rating = "Moderate configuration score";
    } else if (score < 40) {
        rating = "Poor configuration score";
    }

    const panel = createElement("div", "score-panel");

    panel.appendChild(
        createElement(
            "h2",
            "",
            "Security Configuration Score"
        )
    );

    panel.appendChild(
        createElement(
            "div",
            "score-number",
            score + "/100"
        )
    );

    panel.appendChild(
        createElement(
            "h3",
            "score-rating",
            rating
        )
    );

    const track = createElement("div", "score-track");
    const fill = createElement("div", "score-fill");

    fill.style.width = score + "%";

    track.appendChild(fill);
    panel.appendChild(track);

    panel.appendChild(
        createElement(
            "p",
            "score-note",
            "Educational estimate based on detected findings. " +
            "This is not a complete security audit or certification."
        )
    );

    return panel;
}


// ============================================================
// 5. SEVERITY ANALYTICS
// ============================================================

function displayAnalytics(findings) {

    const section = createElement("div", "analytics-section");

    section.appendChild(
        createElement(
            "h2",
            "",
            "Findings Analytics"
        )
    );

    const severities = [
        { name: "High", color: "high-bar" },
        { name: "Medium", color: "medium-bar" },
        { name: "Low", color: "low-bar" },
        { name: "Informational", color: "info-bar" }
    ];

    const maxCount = Math.max(
        1,
        ...severities.map(item =>
            findings.filter(
                finding => finding.severity === item.name
            ).length
        )
    );

    severities.forEach(item => {

        const count = findings.filter(
            finding => finding.severity === item.name
        ).length;

        const row = createElement("div", "chart-row");

        const label = createElement(
            "div",
            "chart-label",
            item.name + " (" + count + ")"
        );

        const track = createElement("div", "chart-track");

        const bar = createElement(
            "div",
            "chart-bar " + item.color
        );

        bar.style.width =
            (count / maxCount * 100) + "%";

        track.appendChild(bar);
        row.appendChild(label);
        row.appendChild(track);

        section.appendChild(row);
    });

    return section;
}


// ============================================================
// 6. DETAILED REPORT SUMMARY IN SIMPLE ENGLISH
// ============================================================

function displayPlainEnglishSummary(data) {

    const findings = data.findings || [];

    const section = createElement(
        "div",
        "plain-summary"
    );

    section.appendChild(
        createElement(
            "h2",
            "",
            "Detailed Report Summary"
        )
    );

    section.appendChild(
        createElement(
            "p",
            "",
            "This section explains your assessment results in simple English."
        )
    );


    // COUNT FINDINGS

    const counts = {
        High: 0,
        Medium: 0,
        Low: 0,
        Informational: 0
    };

    findings.forEach(finding => {

        if (
            Object.prototype.hasOwnProperty.call(
                counts,
                finding.severity
            )
        ) {
            counts[finding.severity]++;
        }

    });


    // 1. OVERALL RESULT

    section.appendChild(
        createElement(
            "h3",
            "",
            "1. Overall Result"
        )
    );

    let overallText;

    if (findings.length === 0) {

        overallText =
            "The assessment did not report any issues in the checks performed. " +
            "However, this does not guarantee that the website is completely secure.";

    } else {

        overallText =
            "The assessment reported " +
            findings.length +
            " findings. Some security configuration settings may need improvement. " +
            "These findings are not necessarily confirmed vulnerabilities.";
    }

    section.appendChild(
        createElement(
            "p",
            "",
            overallText
        )
    );


    // 2. RISK LEVEL EXPLANATION

    section.appendChild(
        createElement(
            "h3",
            "",
            "2. Understanding the Risk Levels"
        )
    );

    const explanations = [
        [
            "High",
            "Important issue. Review and address it as a priority."
        ],
        [
            "Medium",
            "An issue that should be reviewed and improved."
        ],
        [
            "Low",
            "A smaller configuration improvement to consider."
        ],
        [
            "Informational",
            "Additional information about the website configuration."
        ]
    ];

    explanations.forEach(([severity, explanation]) => {

        section.appendChild(
            createElement(
                "p",
                "summary-detail",
                severity +
                " (" +
                counts[severity] +
                "): " +
                explanation
            )
        );

    });


    // 3. WEBSITE CONNECTION

    section.appendChild(
        createElement(
            "h3",
            "",
            "3. Website Connection"
        )
    );

    const httpsText = data.https_enabled

        ? "The final website address uses HTTPS. HTTPS helps protect information while it travels between the browser and website. This does not guarantee that every part of the website is secure."

        : "The final website address uses HTTP rather than HTTPS. The website owner should review HTTPS configuration and enable it with a valid certificate.";

    section.appendChild(
        createElement(
            "p",
            "",
            httpsText
        )
    );


    // 4. PRIORITIZED RECOMMENDATIONS

    section.appendChild(
        createElement(
            "h3",
            "",
            "4. Recommended Actions"
        )
    );

    const priorityOrder = {
        High: 1,
        Medium: 2,
        Low: 3,
        Informational: 4
    };

    const prioritizedFindings = [...findings].sort(
        (a, b) =>
            (priorityOrder[a.severity] || 5) -
            (priorityOrder[b.severity] || 5)
    );

    if (prioritizedFindings.length === 0) {

        section.appendChild(
            createElement(
                "p",
                "",
                "Continue regular security reviews and consider additional security checks."
            )
        );

    } else {

        const actionList = document.createElement("ol");

        prioritizedFindings.forEach(finding => {

            const item = document.createElement("li");

            item.textContent =
                finding.title +
                ": " +
                finding.recommendation;

            actionList.appendChild(item);

        });

        section.appendChild(actionList);
    }


    // 5. FINAL CONCLUSION

    section.appendChild(
        createElement(
            "h3",
            "",
            "5. Final Conclusion"
        )
    );

    section.appendChild(
        createElement(
            "p",
            "",
            "This assessment reviewed the website's homepage HTTP response " +
            "and selected security headers. It did not perform a complete " +
            "security audit, test application code, or verify every possible " +
            "security weakness. The website owner should review the findings, " +
            "make appropriate improvements, and arrange further authorized testing."
        )
    );


    // SUMMARY FOOTER

    section.appendChild(
        createElement(
            "p",
            "summary-footer",
            "Generated automatically by SecureLens AI."
        )
    );

    return section;
}


// ============================================================
// 7. DISPLAY COMPLETE ASSESSMENT RESULTS
// ============================================================

function displayResults(data) {

    resultsContainer.replaceChildren();
    resultsContainer.hidden = false;

    const findings = data.findings || [];


    // ASSESSMENT HEADER

    resultsContainer.appendChild(
        createElement(
            "h2",
            "",
            "Assessment Results"
        )
    );

    resultsContainer.appendChild(
        createElement(
            "p",
            "",
            "Target: " + data.target
        )
    );

    resultsContainer.appendChild(
        createElement(
            "p",
            "",
            "HTTP Status: " + data.status_code
        )
    );

    resultsContainer.appendChild(
        createElement(
            "p",
            "",
            "HTTPS Enabled: " +
            (data.https_enabled ? "Yes" : "No")
        )
    );


    // SECURITY SCORE

    resultsContainer.appendChild(
        displaySecurityScore(findings)
    );


    // ANALYTICS

    resultsContainer.appendChild(
        displayAnalytics(findings)
    );


    // FINDINGS HEADING

    resultsContainer.appendChild(
        createElement(
            "h2",
            "",
            "Detailed Findings (" + findings.length + ")"
        )
    );


    // SEVERITY SUMMARY

    const summary = createElement(
        "div",
        "severity-summary"
    );

    ["High", "Medium", "Low", "Informational"].forEach(severity => {

        const count = findings.filter(
            item => item.severity === severity
        ).length;

        summary.appendChild(
            createElement(
                "p",
                "severity-count",
                severity + ": " + count
            )
        );

    });

    resultsContainer.appendChild(summary);


    // HANDLE EMPTY FINDINGS

    if (findings.length === 0) {

        resultsContainer.appendChild(
            createElement(
                "p",
                "",
                "No findings were reported."
            )
        );
    }


    // INDIVIDUAL FINDING CARDS

    findings.forEach((finding, index) => {

        const card = createElement(
            "div",
            "finding-card"
        );

        card.appendChild(
            createElement(
                "h3",
                "",
                (index + 1) + ". " + finding.title
            )
        );

        card.appendChild(
            createElement(
                "p",
                "finding-severity",
                "Severity: " + finding.severity
            )
        );

        card.appendChild(
            createElement(
                "p",
                "",
                finding.description
            )
        );

        card.appendChild(
            createElement(
                "p",
                "",
                "Evidence: " + finding.evidence
            )
        );

        card.appendChild(
            createElement(
                "p",
                "recommendation",
                "Recommendation: " + finding.recommendation
            )
        );

        resultsContainer.appendChild(card);

    });


    // DETAILED SUMMARY AT THE VERY END

    resultsContainer.appendChild(
        displayPlainEnglishSummary(data)
    );


    // SCROLL TO RESULTS

    resultsContainer.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


// ============================================================
// 8. SUBMIT WEBSITE ASSESSMENT
// ============================================================

assessButton.addEventListener("click", async () => {

    const websiteUrl = document
        .getElementById("website-url")
        .value.trim();

    const authorization = document
        .getElementById("authorization")
        .checked;

    message.textContent = "";

    resultsContainer.hidden = true;
    resultsContainer.replaceChildren();


    // VALIDATE URL INPUT

    if (!websiteUrl) {

        message.textContent =
            "Please enter a website URL.";

        return;
    }


    // VALIDATE AUTHORIZATION

    if (!authorization) {

        message.textContent =
            "Please confirm assessment authorization.";

        return;
    }


    // LOADING STATE

    assessButton.disabled = true;
    assessButton.textContent = "Assessing...";


    try {

        const response = await fetch("/api/assess", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                url: websiteUrl,

                authorization_confirmed: true

            })

        });


        const data = await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.error || "Assessment failed."
            );

        }


        // SUCCESS MESSAGE

        message.textContent =
            "Assessment completed successfully.";


        // DISPLAY RESULTS

        displayResults(data);


    } catch (error) {

        message.textContent =
            error.message;

    } finally {

        assessButton.disabled = false;

        assessButton.textContent =
            "Submit Assessment";

    }

});


// ============================================================
// 9. INITIALIZE APPLICATION
// ============================================================

checkBackend();
