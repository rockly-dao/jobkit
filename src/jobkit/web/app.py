"""Web UI for JobKit."""

import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
from ..config import get_config
from ..scrapers import Job
from ..generators import LLMClient, ResumeGenerator, CoverLetterGenerator


app = Flask(__name__,
    template_folder=Path(__file__).parent / "templates",
    static_folder=Path(__file__).parent / "static"
)


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
        profile_data = {
            "name": request.form.get("name", ""),
            "email": request.form.get("email", ""),
            "phone": request.form.get("phone", ""),
            "background": request.form.get("background", ""),
        }
        with open(config.profile_path, "w") as f:
            json.dump(profile_data, f, indent=2)
        return redirect(url_for("profile"))

    profile_data = get_profile()
    return render_template("profile.html", profile=profile_data)


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
        # Initialize LLM
        llm = LLMClient.from_config(config)
        resume_gen = ResumeGenerator(llm)
        cover_gen = CoverLetterGenerator(llm)

        # Create application folder
        folder_name = f"{job.company} - {job.title}"
        folder_name = "".join(c if c.isalnum() or c in " -_." else "_" for c in folder_name)[:60]
        app_folder = config.applications_dir / folder_name
        app_folder.mkdir(exist_ok=True)

        # Generate resume
        resume_content = resume_gen.generate(job, profile["background"])
        resume_gen.save(resume_content, app_folder / "resume.md")

        # Generate cover letter
        cover_content = cover_gen.generate(job, profile["background"])
        cover_gen.save(cover_content, app_folder / "cover_letter.md")

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


@app.route("/settings", methods=["GET", "POST"])
def settings():
    """View/edit settings."""
    config = get_config()

    if request.method == "POST":
        config.search.keywords = request.form.get("keywords", "")
        config.search.location = request.form.get("location", "")
        config.llm.provider = request.form.get("llm_provider", "ollama")
        config.llm.model = request.form.get("llm_model", "llama3")
        config.save()
        return redirect(url_for("settings"))

    return render_template("settings.html", config=config)


def run_server(host="127.0.0.1", port=5000, debug=False):
    """Run the web server."""
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server(debug=True)
