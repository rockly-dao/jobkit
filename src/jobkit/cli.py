"""
JobKit CLI - Command line interface for job hunting automation.
"""

import argparse
import sys
from pathlib import Path

from .config import load_config, save_config
from .scrapers.linkedin import LinkedInScraper


def main():
    parser = argparse.ArgumentParser(
        prog="jobkit",
        description="Open source job hunting toolkit - search, save, and generate applications"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for jobs")
    search_parser.add_argument("keywords", help="Job search keywords")
    search_parser.add_argument("--location", "-l", default="Remote", help="Location filter")
    search_parser.add_argument("--limit", "-n", type=int, default=25, help="Max jobs to fetch")

    # Job command - fetch single job
    job_parser = subparsers.add_parser("job", help="Fetch a single job by ID or URL")
    job_parser.add_argument("job_id", help="LinkedIn job ID or URL")

    # List command
    list_parser = subparsers.add_parser("list", help="List saved jobs")
    list_parser.add_argument("--new", action="store_true", help="Show only new jobs")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate resume and cover letter")
    gen_parser.add_argument("job_id", help="Job ID to generate application for")

    # Web command
    web_parser = subparsers.add_parser("web", help="Start web interface")
    web_parser.add_argument("--port", "-p", type=int, default=5000, help="Port to run on")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")

    # Config command
    config_parser = subparsers.add_parser("config", help="Show or edit configuration")
    config_parser.add_argument("--show", action="store_true", help="Show current config")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    config = load_config()

    if args.command == "search":
        cmd_search(config, args)
    elif args.command == "job":
        cmd_job(config, args)
    elif args.command == "list":
        cmd_list(config, args)
    elif args.command == "generate":
        cmd_generate(config, args)
    elif args.command == "web":
        cmd_web(config, args)
    elif args.command == "config":
        cmd_config(config, args)


def cmd_search(config, args):
    """Search for jobs on LinkedIn."""
    print(f"Searching for '{args.keywords}' in {args.location}...")

    scraper = LinkedInScraper(config.data_dir)
    jobs = scraper.search(args.keywords, args.location, limit=args.limit)

    print(f"\nFound {len(jobs)} jobs:")
    for job in jobs:
        print(f"  - {job.title} at {job.company} ({job.location})")

    print(f"\nJobs saved to: {config.data_dir / 'jobs'}")


def cmd_job(config, args):
    """Fetch a single job by ID or URL."""
    job_id = args.job_id

    # Extract ID from URL if needed
    if "linkedin.com" in job_id:
        import re
        match = re.search(r'/jobs/view/(\d+)', job_id)
        if match:
            job_id = match.group(1)

    print(f"Fetching job {job_id}...")

    scraper = LinkedInScraper(config.data_dir)
    job = scraper.get_job(job_id)

    if job:
        print(f"\nSaved: {job.title} at {job.company}")
        print(f"Location: {job.location}")
        print(f"File: {config.data_dir / 'jobs' / f'{job.id}.json'}")
    else:
        print("Failed to fetch job")


def cmd_list(config, args):
    """List saved jobs."""
    import json

    jobs_dir = config.data_dir / "jobs"
    if not jobs_dir.exists():
        print("No jobs saved yet. Run 'jobkit search' first.")
        return

    applications_dir = config.data_dir / "applications"
    applied_ids = set()
    if applications_dir.exists():
        for app_dir in applications_dir.iterdir():
            if app_dir.is_dir():
                meta_file = app_dir / "meta.json"
                if meta_file.exists():
                    meta = json.loads(meta_file.read_text())
                    applied_ids.add(meta.get("job_id"))

    jobs = []
    for job_file in jobs_dir.glob("*.json"):
        job = json.loads(job_file.read_text())
        job["_applied"] = job.get("id") in applied_ids
        jobs.append(job)

    # Sort by date
    jobs.sort(key=lambda x: x.get("scraped_at", ""), reverse=True)

    if args.new:
        jobs = [j for j in jobs if not j["_applied"]]

    print(f"\n{'NEW' if args.new else 'All'} Jobs ({len(jobs)}):\n")

    for i, job in enumerate(jobs, 1):
        status = "" if job["_applied"] else " [NEW]"
        print(f"{i}. {job['title']}")
        print(f"   {job['company']} - {job['location']}{status}")
        print()


def cmd_generate(config, args):
    """Generate resume and cover letter for a job."""
    import json

    # Find the job
    jobs_dir = config.data_dir / "jobs"
    job_file = jobs_dir / f"{args.job_id}.json"

    if not job_file.exists():
        # Try partial match
        matches = list(jobs_dir.glob(f"*{args.job_id}*.json"))
        if matches:
            job_file = matches[0]
        else:
            print(f"Job not found: {args.job_id}")
            return

    job = json.loads(job_file.read_text())

    # Check for profile
    profile_file = config.data_dir / "profile.json"
    if not profile_file.exists():
        print("Profile not found. Run 'jobkit web' to set up your profile first.")
        return

    profile = json.loads(profile_file.read_text())

    print(f"Generating application for: {job['title']} at {job['company']}")

    from .generators.llm import LLMClient
    from .generators.resume import ResumeGenerator
    from .generators.cover_letter import CoverLetterGenerator

    llm = LLMClient(
        provider=config.llm.provider,
        model=config.llm.model,
        api_key=config.llm.api_key
    )

    # Generate resume
    print("Generating tailored resume...")
    resume_gen = ResumeGenerator(llm)
    resume = resume_gen.generate(profile, job)

    # Generate cover letter
    print("Generating cover letter...")
    cover_gen = CoverLetterGenerator(llm)
    cover_letter = cover_gen.generate(profile, job)

    # Save outputs
    app_name = f"{job['company']} - {job['title']}".replace("/", "-")
    app_dir = config.data_dir / "applications" / app_name
    app_dir.mkdir(parents=True, exist_ok=True)

    (app_dir / "resume.md").write_text(resume)
    (app_dir / "cover_letter.md").write_text(cover_letter)

    # Save metadata
    meta = {"job_id": job["id"], "generated_at": str(Path().stat().st_mtime)}
    (app_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    print(f"\nApplication saved to: {app_dir}")
    print("  - resume.md")
    print("  - cover_letter.md")


def cmd_web(config, args):
    """Start the web interface."""
    from .web.app import create_app

    app = create_app(config)
    print(f"\nStarting JobKit web interface at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop\n")
    app.run(host=args.host, port=args.port, debug=True)


def cmd_config(config, args):
    """Show or edit configuration."""
    print(f"Data directory: {config.data_dir}")
    print(f"\nSearch defaults:")
    print(f"  Keywords: {config.search.keywords}")
    print(f"  Location: {config.search.location}")
    print(f"\nLLM settings:")
    print(f"  Provider: {config.llm.provider}")
    print(f"  Model: {config.llm.model}")
    print(f"\nEdit settings via: jobkit web")


if __name__ == "__main__":
    main()
