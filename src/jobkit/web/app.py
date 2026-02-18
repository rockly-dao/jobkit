"""Web UI for JobKit."""

import json
import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from ..config import get_config
from ..scrapers import Job
from ..generators import LLMClient, ResumeGenerator, CoverLetterGenerator

# Required for multiprocessing on macOS
if sys.platform == 'darwin':
    import multiprocessing
    try:
        multiprocessing.set_start_method('spawn')
    except RuntimeError:
        pass  # Already set


app = Flask(__name__,
    template_folder=Path(__file__).parent / "templates",
    static_folder=Path(__file__).parent / "static"
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "jobkit-dev-key-change-in-production")


def get_saved_jobs() -> list[dict]:
    """Get all saved jobs."""
    config = get_config()
    jobs = []
    for json_file in config.jobs_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                job_data = json.load(f)
                job_data["_file"] = json_file.name
                jobs.append(job_data)
        except:
            continue
    return sorted(jobs, key=lambda x: x.get("scraped_at", ""), reverse=True)


def get_applications() -> list[dict]:
    """Get all generated applications."""
    config = get_config()
    applications = []
    for folder in config.applications_dir.iterdir():
        if folder.is_dir():
            app_data = {
                "name": folder.name,
                "has_resume": (folder / "resume.md").exists(),
                "has_cover_letter": (folder / "cover_letter.md").exists(),
            }
            applications.append(app_data)
    return applications


def get_profile() -> dict:
    """Get user profile."""
    config = get_config()
    if config.profile_path.exists():
        with open(config.profile_path) as f:
            return json.load(f)
    return {"background": "", "name": "", "email": "", "phone": ""}


@app.route("/")
def index():
    """Dashboard home."""
    jobs = get_saved_jobs()
    applications = get_applications()
    profile = get_profile()
    return render_template("index.html",
        jobs=jobs,
        applications=applications,
        profile=profile,
        job_count=len(jobs),
        app_count=len(applications),
    )


@app.route("/jobs")
def jobs_list():
    """List all saved jobs."""
    jobs = get_saved_jobs()
    return render_template("jobs.html", jobs=jobs)


@app.route("/jobs/<job_id>")
def job_detail(job_id):
    """View job details."""
    config = get_config()
    for json_file in config.jobs_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                job_data = json.load(f)
                if job_data.get("id") == job_id:
                    return render_template("job_detail.html", job=job_data)
        except:
            continue
    return "Job not found", 404


@app.route("/profile", methods=["GET", "POST"])
def profile():
    """View/edit profile."""
    config = get_config()

    if request.method == "POST":
        # Get existing profile to preserve background
        current_profile = get_profile()

        # Update only contact info
        profile_data = {
            "name": request.form.get("name", ""),
            "email": request.form.get("email", ""),
            "phone": request.form.get("phone", ""),
            "background": current_profile.get("background", ""),  # Preserve background
        }
        with open(config.profile_path, "w") as f:
            json.dump(profile_data, f, indent=2)
        flash("Contact info saved!", "success")
        return redirect(url_for("profile"))

    profile_data = get_profile()
    return render_template("profile.html", profile=profile_data)


@app.route("/profile/clear", methods=["POST"])
def clear_profile():
    """Clear the current profile."""
    config = get_config()

    empty_profile = {
        "name": "",
        "email": "",
        "phone": "",
        "background": "",
    }

    with open(config.profile_path, "w") as f:
        json.dump(empty_profile, f, indent=2)

    flash("Profile cleared!", "success")
    return redirect(url_for("profile"))


def _run_linkedin_import_process(import_id, linkedin_url, data_dir, profile_path):
    """Run LinkedIn import in a separate process."""
    import sys

    status_file = Path(data_dir) / f".import_{import_id}.json"

    def write_status(status, profile=None, error=""):
        status_file.write_text(json.dumps({
            "status": status,
            "profile": profile or {},
            "error": error
        }))

    write_status("running")
    print(f"\n[{import_id}] LinkedIn import started!", flush=True)

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from jobkit.importers.linkedin_profile import LinkedInProfileImporter

        importer = LinkedInProfileImporter(data_dir)
        profile_data = importer.import_profile(linkedin_url)
        background_text = importer.format_as_text(profile_data)

        # Load current profile and update with smart merging
        profile_path = Path(profile_path)
        current_profile = {}
        if profile_path.exists():
            current_profile = json.loads(profile_path.read_text())

        # Smart merge: keep best value for each field (non-empty wins)
        if profile_data.get("name") and not current_profile.get("name"):
            current_profile["name"] = profile_data.get("name")

        # Only update background if LinkedIn gave us substantial data
        has_substantial_data = (
            profile_data.get("about") or
            profile_data.get("experience") or
            profile_data.get("education")
        )

        if has_substantial_data:
            # Merge backgrounds with clear section headers
            existing_bg = current_profile.get("background", "").strip()
            linkedin_bg = background_text.strip()

            if existing_bg:
                # Check if LinkedIn data is already in background
                if linkedin_bg[:100] not in existing_bg:
                    current_profile["background"] = f"=== FROM LINKEDIN ===\n{linkedin_bg}\n\n=== FROM RESUME ===\n{existing_bg}"
            else:
                current_profile["background"] = linkedin_bg
        else:
            print(f"[{import_id}] LinkedIn didn't extract much data, keeping existing background", flush=True)

        # Save updated profile
        profile_path.write_text(json.dumps(current_profile, indent=2))

        write_status("complete", profile_data)
        print(f"[{import_id}] Import complete!", flush=True)

    except Exception as e:
        import traceback
        print(f"[{import_id}] ERROR: {str(e)}", flush=True)
        traceback.print_exc()
        write_status("error", error=str(e))


@app.route("/profile/import-linkedin", methods=["POST"])
def import_linkedin():
    """Start LinkedIn profile import (async)."""
    config = get_config()
    linkedin_url = request.form.get("linkedin_url", "").strip()

    if not linkedin_url:
        flash("Please enter a LinkedIn profile URL", "error")
        return redirect(url_for("profile"))

    # Generate import ID
    import_id = str(uuid.uuid4())[:8]

    # Create initial status file
    status_file = config.data_dir / f".import_{import_id}.json"
    status_file.write_text(json.dumps({"status": "starting", "profile": {}, "error": ""}))

    # Start import in a separate process
    process = multiprocessing.Process(
        target=_run_linkedin_import_process,
        args=(import_id, linkedin_url, str(config.data_dir), str(config.profile_path))
    )
    process.start()

    # Redirect to a status page
    flash("LinkedIn import started. Please log in if the browser opens, then wait...", "info")
    return redirect(url_for("import_status", import_id=import_id))


@app.route("/profile/import-status/<import_id>")
def import_status(import_id):
    """Check status of LinkedIn import."""
    config = get_config()
    status_file = config.data_dir / f".import_{import_id}.json"

    if not status_file.exists():
        flash("Import not found", "error")
        return redirect(url_for("profile"))

    try:
        status = json.loads(status_file.read_text())

        if status["status"] == "complete":
            # Clean up and redirect
            try:
                status_file.unlink()
            except:
                pass
            flash("Successfully imported profile from LinkedIn!", "success")
            return redirect(url_for("profile"))

        elif status["status"] == "error":
            try:
                status_file.unlink()
            except:
                pass
            flash(f"Error importing: {status.get('error', 'Unknown error')}", "error")
            return redirect(url_for("profile"))

        else:
            # Still running - show waiting page
            return render_template("import_status.html", import_id=import_id)

    except Exception as e:
        flash(f"Error checking import status: {str(e)}", "error")
        return redirect(url_for("profile"))


@app.route("/profile/import-github", methods=["POST"])
def import_github():
    """Import profile from GitHub."""
    config = get_config()
    github_url = request.form.get("github_url", "").strip()

    if not github_url:
        flash("Please enter a GitHub username or URL", "error")
        return redirect(url_for("profile"))

    try:
        from ..importers.github_profile import GitHubProfileImporter

        importer = GitHubProfileImporter()
        profile_data = importer.import_profile(github_url)
        github_text = importer.format_as_text(profile_data)

        # Smart merge with existing profile
        current_profile = get_profile()

        # Update name only if not set
        if profile_data.get("name") and not current_profile.get("name"):
            current_profile["name"] = profile_data.get("name")

        # Merge background
        existing_bg = current_profile.get("background", "").strip()
        if existing_bg:
            if "=== FROM GITHUB ===" not in existing_bg:
                current_profile["background"] = f"{existing_bg}\n\n=== FROM GITHUB ===\n{github_text}"
        else:
            current_profile["background"] = github_text

        with open(config.profile_path, "w") as f:
            json.dump(current_profile, f, indent=2)

        flash(f"Successfully imported GitHub profile (@{profile_data.get('username', '')})!", "success")
        return redirect(url_for("profile"))

    except Exception as e:
        flash(f"Error importing from GitHub: {str(e)}", "error")
        return redirect(url_for("profile"))


@app.route("/profile/upload", methods=["POST"])
def upload_resume():
    """Upload and parse resume file."""
    config = get_config()

    if "resume_file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("profile"))

    file = request.files["resume_file"]
    if file.filename == "":
        flash("No file selected", "error")
        return redirect(url_for("profile"))

    replace_existing = request.form.get("replace_existing") == "1"

    try:
        from ..importers.file_parser import FileParser

        file_bytes = file.read()
        parsed = FileParser.parse(file_bytes=file_bytes, filename=file.filename)

        # Smart merge: always keep best info from all sources
        current_profile = get_profile()

        # Update contact info - new values win if they exist
        if parsed.get("name"):
            current_profile["name"] = parsed["name"]
        if parsed.get("email"):
            current_profile["email"] = parsed["email"]
        if parsed.get("phone"):
            current_profile["phone"] = parsed["phone"]

        # Handle background based on replace_existing flag
        new_text = parsed.get("text", "").strip()
        existing_bg = current_profile.get("background", "").strip()

        if replace_existing or not existing_bg:
            # Replace or first upload
            current_profile["background"] = new_text
        else:
            # Merge: check if this content is already there
            if new_text[:100] not in existing_bg:
                current_profile["background"] = f"=== FROM RESUME ===\n{new_text}\n\n{existing_bg}"

        with open(config.profile_path, "w") as f:
            json.dump(current_profile, f, indent=2)

        flash(f"Successfully imported from {file.filename}!", "success")
        return redirect(url_for("profile"))

    except ImportError as e:
        flash(str(e), "error")
        return redirect(url_for("profile"))
    except Exception as e:
        flash(f"Error parsing file: {str(e)}", "error")
        return redirect(url_for("profile"))


@app.route("/generate/<job_id>", methods=["POST"])
def generate_application(job_id):
    """Generate resume and cover letter for a job."""
    config = get_config()
    profile = get_profile()

    if not profile.get("background"):
        return jsonify({"error": "Please set up your profile first"}), 400

    # Find the job
    job_data = None
    for json_file in config.jobs_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
                if data.get("id") == job_id:
                    job_data = data
                    break
        except:
            continue

    if not job_data:
        return jsonify({"error": "Job not found"}), 404

    job = Job(**{k: v for k, v in job_data.items() if k in Job.__dataclass_fields__})

    try:
        # Check LLM configuration
        provider = config.llm.provider
        print(f"Initializing LLM: provider={provider}, model={config.llm.model}")

        if provider in ["anthropic", "openai"] and not config.llm.api_key:
            return jsonify({
                "error": f"API key required for {provider}. Please add your API key in Settings."
            }), 400

        if provider == "ollama":
            # Check if Ollama is running
            import requests
            try:
                resp = requests.get("http://localhost:11434/api/version", timeout=2)
                if resp.status_code != 200:
                    raise Exception("Ollama not responding")
            except Exception:
                return jsonify({
                    "error": "Ollama is not running. Please start Ollama with 'ollama serve' or switch to a cloud provider in Settings."
                }), 400

        llm = LLMClient.from_config(config)
        resume_gen = ResumeGenerator(llm)
        cover_gen = CoverLetterGenerator(llm)

        # Create application folder
        folder_name = f"{job.company} - {job.title}"
        folder_name = "".join(c if c.isalnum() or c in " -_." else "_" for c in folder_name)[:60]
        app_folder = config.applications_dir / folder_name
        app_folder.mkdir(exist_ok=True)

        # Generate resume
        print(f"Generating resume for {job.title} at {job.company}...")
        resume_content = resume_gen.generate(job, profile["background"])
        resume_gen.save(resume_content, app_folder / "resume.md")
        print("Resume generated!")

        # Generate cover letter
        print("Generating cover letter...")
        cover_content = cover_gen.generate(job, profile["background"])
        cover_gen.save(cover_content, app_folder / "cover_letter.md")
        print("Cover letter generated!")

        # Save job details
        with open(app_folder / "job.json", "w") as f:
            json.dump(job_data, f, indent=2)

        return jsonify({
            "success": True,
            "folder": folder_name,
            "resume": resume_content,
            "cover_letter": cover_content,
        })

    except Exception as e:
        import traceback
        print(f"Error generating application: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/applications/<name>")
def application_detail(name):
    """View application details."""
    config = get_config()
    app_folder = config.applications_dir / name

    if not app_folder.exists():
        return "Application not found", 404

    resume = ""
    cover_letter = ""

    if (app_folder / "resume.md").exists():
        resume = (app_folder / "resume.md").read_text()

    if (app_folder / "cover_letter.md").exists():
        cover_letter = (app_folder / "cover_letter.md").read_text()

    return render_template("application_detail.html",
        name=name,
        resume=resume,
        cover_letter=cover_letter,
    )


@app.route("/applications/<name>/download/<doc_type>")
def download_pdf(name, doc_type):
    """Download resume or cover letter as PDF."""
    from flask import Response, send_file
    from io import BytesIO

    config = get_config()
    app_folder = config.applications_dir / name

    if not app_folder.exists():
        return "Application not found", 404

    if doc_type not in ["resume", "cover_letter"]:
        return "Invalid document type", 400

    md_file = app_folder / f"{doc_type}.md"
    if not md_file.exists():
        return f"{doc_type} not found", 404

    try:
        from ..exporters.pdf import export_to_pdf

        markdown_content = md_file.read_text()

        # Create a nice filename with company/job name
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in name)[:50]
        pdf_filename = f"{safe_name}_{doc_type}.pdf"

        # Save to Downloads folder (visible to users)
        downloads_folder = Path.home() / "Downloads"
        pdf_path = downloads_folder / pdf_filename
        export_to_pdf(markdown_content, output_path=pdf_path)

        # Also keep a copy in the application folder
        app_pdf_path = app_folder / f"{doc_type}.pdf"
        export_to_pdf(markdown_content, output_path=app_pdf_path)

        # Send the file from Downloads
        return send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=pdf_filename
        )

    except ImportError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error generating PDF: {str(e)}"}), 500


@app.route("/settings", methods=["GET", "POST"])
def settings():
    """View/edit settings."""
    config = get_config()

    if request.method == "POST":
        config.search.keywords = request.form.get("keywords", "")
        config.search.location = request.form.get("location", "")
        config.llm.provider = request.form.get("llm_provider", "ollama")
        config.llm.model = request.form.get("llm_model", "llama3")
        api_key = request.form.get("api_key", "").strip()
        if api_key:  # Only update if provided (don't clear existing)
            config.llm.api_key = api_key
        config.save()
        flash("Settings saved!", "success")
        return redirect(url_for("settings"))

    return render_template("settings.html", config=config)


# ============ Job Search Routes ============

import multiprocessing
import uuid

# Storage for search state (using files for multiprocessing compatibility)
_search_results = {}


@app.route("/search")
def search_page():
    """Job search page."""
    config = get_config()
    return render_template("search.html",
        keywords=config.search.keywords,
        location=config.search.location
    )


def _get_search_status_file(search_id, data_dir):
    """Get path to search status file."""
    return Path(data_dir) / f".search_{search_id}.json"


def _run_search_process(search_id, keywords, location, data_dir, jobs_dir):
    """Run the search in a separate process."""
    import sys

    status_file = _get_search_status_file(search_id, data_dir)

    def write_status(status, jobs=None, error=""):
        status_file.write_text(json.dumps({
            "status": status,
            "jobs": jobs or [],
            "error": error
        }))

    write_status("running")
    print(f"\n[{search_id}] Search process started!", flush=True)

    scraper = None
    try:
        # Import here since we're in a new process
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from jobkit.scrapers.linkedin import LinkedInScraper

        print(f"[{search_id}] Starting LinkedIn search: {keywords} in {location}", flush=True)

        scraper = LinkedInScraper(headless=False, data_dir=data_dir)

        print(f"[{search_id}] Calling scraper.search()...", flush=True)
        jobs = scraper.search(keywords, location, max_jobs=25)
        print(f"[{search_id}] Search complete! Found {len(jobs)} jobs", flush=True)

        # Get list of already saved job IDs
        saved_ids = set()
        jobs_path = Path(jobs_dir)
        if jobs_path.exists():
            for json_file in jobs_path.glob("*.json"):
                try:
                    job_data = json.loads(json_file.read_text())
                    saved_ids.add(job_data.get("id"))
                except:
                    continue

        # Store results
        results = []
        for job in jobs:
            job_dict = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description,
                "url": job.url,
                "source": job.source,
                "saved": job.id in saved_ids
            }
            results.append(job_dict)

        write_status("complete", results)
        print(f"[{search_id}] Done! {len(results)} results saved", flush=True)

    except Exception as e:
        import traceback
        print(f"[{search_id}] ERROR: {str(e)}", flush=True)
        traceback.print_exc()
        write_status("error", error=str(e))

    finally:
        print(f"[{search_id}] Closing browser...", flush=True)
        if scraper:
            try:
                scraper.stop()
            except:
                pass


@app.route("/search/run", methods=["POST"])
def search_run():
    """Start a job search on LinkedIn (async)."""
    global _search_results
    config = get_config()

    data = request.get_json()
    keywords = data.get("keywords", "")
    location = data.get("location", "Remote")

    if not keywords:
        return jsonify({"error": "Keywords are required"}), 400

    # Generate search ID
    search_id = str(uuid.uuid4())[:8]

    # Create initial status file
    status_file = _get_search_status_file(search_id, config.data_dir)
    status_file.write_text(json.dumps({"status": "starting", "jobs": [], "error": ""}))

    # Start search in a separate process
    process = multiprocessing.Process(
        target=_run_search_process,
        args=(search_id, keywords, location, str(config.data_dir), str(config.jobs_dir))
    )
    process.start()

    return jsonify({"search_id": search_id, "status": "running"})


@app.route("/search/status/<search_id>")
def search_status(search_id):
    """Check status of a running search."""
    global _search_results
    config = get_config()

    status_file = _get_search_status_file(search_id, config.data_dir)

    if not status_file.exists():
        return jsonify({"error": "Search not found"}), 404

    try:
        status = json.loads(status_file.read_text())

        # If complete, store results and clean up
        if status["status"] == "complete":
            for job in status.get("jobs", []):
                _search_results[job["id"]] = job
            # Clean up status file
            try:
                status_file.unlink()
            except:
                pass

        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/save/<job_id>", methods=["POST"])
def search_save(job_id):
    """Save a job from search results."""
    global _search_results
    config = get_config()

    # Get job from search results
    job_data = _search_results.get(job_id)
    if not job_data:
        return jsonify({"error": "Job not found in search results"}), 404

    try:
        from datetime import datetime

        # Add timestamp
        job_data["scraped_at"] = datetime.now().isoformat()

        # Save to file
        job_file = config.jobs_dir / f"{job_id}.json"
        job_file.write_text(json.dumps(job_data, indent=2))

        return jsonify({"success": True, "id": job_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run_server(host="127.0.0.1", port=5000, debug=False):
    """Run the web server."""
    # Enable threading for background search tasks
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    run_server(debug=True)
