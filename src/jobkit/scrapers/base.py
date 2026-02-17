"""Base scraper class and Job model."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json
from pathlib import Path


@dataclass
class Job:
    """Job listing data model."""
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str  # linkedin, indeed, etc.
    salary: Optional[str] = None
    posted_date: Optional[str] = None
    scraped_at: str = ""

    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, directory: Path) -> Path:
        """Save job to JSON file."""
        filename = f"{self.company} - {self.title}.json"
        # Sanitize filename
        filename = "".join(c if c.isalnum() or c in " -_." else "_" for c in filename)[:100]
        filepath = directory / filename

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        return filepath

    @classmethod
    def load(cls, filepath: Path) -> "Job":
        """Load job from JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        return cls(**data)


class BaseScraper(ABC):
    """Base class for job scrapers."""

    def __init__(self):
        self.existing_job_ids: set[str] = set()

    def load_existing_jobs(self, directory: Path):
        """Load IDs of already scraped jobs."""
        for json_file in directory.glob("*.json"):
            try:
                job = Job.load(json_file)
                if job.id:
                    self.existing_job_ids.add(job.id)
            except (json.JSONDecodeError, TypeError):
                continue

    def is_new_job(self, job_id: str) -> bool:
        """Check if job is new (not already scraped)."""
        return job_id not in self.existing_job_ids

    @abstractmethod
    def search(self, keywords: str, location: str, **filters) -> list[Job]:
        """Search for jobs. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a single job by ID. Must be implemented by subclasses."""
        pass
