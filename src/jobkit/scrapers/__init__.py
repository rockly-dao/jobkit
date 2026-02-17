"""Job scrapers for various platforms."""

from .linkedin import LinkedInScraper
from .base import BaseScraper, Job

__all__ = ["LinkedInScraper", "BaseScraper", "Job"]
