#!/usr/bin/env python3
"""Test the LinkedIn scraper directly."""

from pathlib import Path
from src.jobkit.scrapers.linkedin import LinkedInScraper

print("Creating scraper...")
scraper = LinkedInScraper(headless=False, data_dir=Path.home() / ".jobkit")

print("Starting search...")
try:
    jobs = scraper.search("software engineer", "Remote", max_jobs=5)
    print(f"Found {len(jobs)} jobs:")
    for job in jobs:
        print(f"  - {job.title} at {job.company}")

    print("\nSearch completed successfully!")
    print("Press Enter to close the browser...")
    input()

except Exception as e:
    print(f"\n{'='*50}")
    print(f"ERROR: {e}")
    print(f"{'='*50}")
    import traceback
    traceback.print_exc()
    print("\nBrowser left open for debugging. Press Enter to close...")
    input()

finally:
    print("Stopping scraper...")
    scraper.stop()
    print("Done!")
