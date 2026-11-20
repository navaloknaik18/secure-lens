
import io
import re
import zipfile

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file
)

from config import Config
from modules.website_scanner import assess_website
from modules.fix_builder import build_fix_package

from modules.functionality_tester import test_website_functionality
from modules.interaction_tester import run_interaction_tests


app = Flask(__name__)
app.config.from_object(Config)


# Temporary in-memory package storage for local development.
generated_packages = {}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "application": "SecureLens AI",
        "status": "running",
        "version": "1.1.0"
    }), 200


# ============================================================
# EXISTING WEBSITE ASSESSMENT API
# ============================================================

@app.route("/api/assess", methods=["POST"])
def assess():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Please provide valid JSON."
        }), 400

    website_url = data.get("url")

    if not isinstance(website_url, str) or not website_url.strip():
        return jsonify({
            "success": False,
            "error": "Website URL is required."
        }), 400

    if data.get("authorization_confirmed") is not True:
        return jsonify({
            "success": False,
            "error": "Assessment authorization is required."
        }), 403

    try:
        result = assess_website(website_url.strip())
        return jsonify(result), 200

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Unexpected assessment error")

        return jsonify({
            "success": False,
            "error": "An unexpected assessment error occurred."
        }), 500


# ============================================================
# FIXBUILDER: GENERATE FRAMEWORK-SPECIFIC FILES
# ============================================================

@app.route("/api/fixbuilder/generate", methods=["POST"])
def generate_fixes():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Please provide valid JSON."
        }), 400

    if data.get("authorization_confirmed") is not True:
        return jsonify({
            "success": False,
            "error": "Authorization confirmation is required."
        }), 403

    findings = data.get("findings")
    framework = data.get("framework")
    https_enabled = data.get("https_enabled", False)

    if not isinstance(findings, list) or len(findings) > 100:
        return jsonify({
            "success": False,
            "error": "Invalid findings list."
        }), 400

    if not isinstance(framework, str):
        return jsonify({
            "success": False,
            "error": "Please select a framework."
        }), 400

    if not isinstance(https_enabled, bool):
        return jsonify({
            "success": False,
            "error": "Invalid HTTPS status."
        }), 400

    try:
        result = build_fix_package(
            findings=findings,
            framework=framework,
            https_enabled=https_enabled
        )

        # Create a unique package identifier.
        import secrets
        package_id = secrets.token_urlsafe(24)

        generated_packages[package_id] = result

        # Limit memory use in this beginner prototype.
        if len(generated_packages) > 20:
            oldest_key = next(iter(generated_packages))
            del generated_packages[oldest_key]

        return jsonify({
            "success": True,
            "package_id": package_id,
            "framework": result["framework"],
            "missing_headers": result["missing_headers"],
            "files": result["files"],
            "download_endpoint": (
                f"/api/fixbuilder/download/{package_id}"
            )
        }), 200

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("FixBuilder generation failed")

        return jsonify({
            "success": False,
            "error": "Unable to generate the fix package."
        }), 500

# ============================================================
# FUNCTIONALITY TESTING API
# ============================================================

@app.route("/api/functionality", methods=["POST"])
def functionality_assessment():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Please provide valid JSON."
        }), 400

    if data.get("authorization_confirmed") is not True:
        return jsonify({
            "success": False,
            "error": "Authorization confirmation is required."
        }), 403

    website_url = data.get("url")

    if not isinstance(website_url, str) or not website_url.strip():
        return jsonify({
            "success": False,
            "error": "A local website URL is required."
        }), 400

    max_pages = data.get("max_pages", 10)

    if type(max_pages) is not int or not 1 <= max_pages <= 10:
        return jsonify({
            "success": False,
            "error": "max_pages must be an integer between 1 and 10."
        }), 400

    try:
        result = test_website_functionality(
            website_url.strip(),
            max_pages=max_pages
        )

        return jsonify(result), 200

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Functionality assessment failed")

        return jsonify({
            "success": False,
            "error": "Functionality assessment failed."
        }), 500


# ============================================================
# CONTROLLED INTERACTION TESTING API
# ============================================================

@app.route("/api/interaction-tests", methods=["POST"])
def interaction_assessment():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Please provide valid JSON."
        }), 400

    if data.get("authorization_confirmed") is not True:
        return jsonify({
            "success": False,
            "error": "Authorization confirmation is required."
        }), 403

    website_url = data.get("url")

    if not isinstance(website_url, str) or not website_url.strip():
        return jsonify({
            "success": False,
            "error": "A local test website URL is required."
        }), 400

    try:
        result = run_interaction_tests(website_url.strip())
        return jsonify(result), 200

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Interaction assessment failed")

        return jsonify({
            "success": False,
            "error": "Interaction assessment failed."
        }), 500


# ============================================================
# FIXBUILDER: DOWNLOAD GENERATED ZIP
# ============================================================

@app.route(
    "/api/fixbuilder/download/<package_id>",
    methods=["GET"]
)
def download_fixes(package_id):

    package = generated_packages.get(package_id)

    if package is None:
        return jsonify({
            "success": False,
            "error": "Package not found. Generate it again."
        }), 404

    memory_file = io.BytesIO()

    with zipfile.ZipFile(
        memory_file,
        mode="w",
        compression=zipfile.ZIP_DEFLATED
    ) as archive:

        for file in package["files"]:

            filename = file["filename"]

            # Only permit simple generated filenames.
            if not re.fullmatch(
                r"[A-Za-z0-9_.-]+",
                filename
            ):
                continue

            archive.writestr(
                filename,
                file["content"]
            )

    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name="SecureLens-FixBuilder.zip"
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({
        "success": False,
        "error": "The requested page was not found."
    }), 404


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "success": False,
        "error": "Request is too large."
    }), 413


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": "An internal server error occurred."
    }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
