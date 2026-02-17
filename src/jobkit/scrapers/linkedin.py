"""LinkedIn job scraper."""

import re
import time
from typing import Optional
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright, Browser, Page

from .base import BaseScraper, Job


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job listings."""

    BASE_URL = "https://www.linkedin.com"
    JOBS_URL = "https://www.linkedin.com/jobs/search/"

    def __init__(self, headless: bool = False):
        super().__init__()
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self._logged_in = False

    def start(self):
        """Start the browser."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        self.page = self.context.new_page()

    def stop(self):
        """Stop the browser."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self, wait_for_user: bool = True) -> bool:
        """Navigate to LinkedIn login page."""
        if self._logged_in:
            return True

        self.page.goto(f"{self.BASE_URL}/login")

        if wait_for_user:
            print("\n" + "=" * 50)
            print("Please log in to LinkedIn in the browser window.")
            print("Press Enter here once you're logged in...")
            print("=" * 50 + "\n")
            input()

        # Verify login
        self.page.goto(self.BASE_URL)
        time.sleep(2)

        if "feed" in self.page.url or self.page.query_selector('[data-alias="nav-feed"]'):
            self._logged_in = True
            return True

        return False

    def _build_search_url(
        self,
        keywords: str,
        location: str,
        remote_options: list[str] = None,
        experience_level: list[str] = None,
        date_posted: str = None,
    ) -> str:
        """Build LinkedIn job search URL with filters."""
        params = [f"keywords={quote_plus(keywords)}"]

        if location:
            params.append(f"location={quote_plus(location)}")

        # Remote filter
        remote_map = {"on-site": "1", "remote": "2", "hybrid": "3"}
        if remote_options:
            codes = [remote_map[r] for r in remote_options if r in remote_map]
            if codes:
                params.append(f"f_WT={','.join(codes)}")

        # Experience level
        exp_map = {
            "internship": "1", "entry": "2", "associate": "3",
            "mid-senior": "4", "director": "5", "executive": "6",
        }
        if experience_level:
            codes = [exp_map[e] for e in experience_level if e in exp_map]
            if codes:
                params.append(f"f_E={','.join(codes)}")

        # Date posted
        date_map = {"day": "r86400", "week": "r604800", "month": "r2592000"}
        if date_posted and date_posted in date_map:
            params.append(f"f_TPR={date_map[date_posted]}")

        return f"{self.JOBS_URL}?{'&'.join(params)}"

    def _find_element(self, selectors: list[str]):
        """Try multiple selectors and return first match."""
        for selector in selectors:
            el = self.page.query_selector(selector)
            if el:
                return el
        return None

    def _extract_job_details(self) -> Optional[Job]:
        """Extract job details from current page."""
        try:
            # Wait for job details panel
            for sel in [".jobs-unified-top-card", ".job-details-jobs-unified-top-card", ".jobs-details"]:
                try:
                    self.page.wait_for_selector(sel, timeout=3000)
                    break
                except:
                    continue

            # Extract fields with multiple selector attempts
            title_el = self._find_element([
                ".jobs-unified-top-card__job-title",
                ".job-details-jobs-unified-top-card__job-title",
                "h1.t-24", "h2.jobs-unified-top-card__job-title"
            ])
            company_el = self._find_element([
                ".jobs-unified-top-card__company-name",
                ".job-details-jobs-unified-top-card__company-name",
                ".topcard__org-name-link"
            ])
            location_el = self._find_element([
                ".jobs-unified-top-card__bullet",
                ".job-details-jobs-unified-top-card__bullet",
                ".topcard__flavor--bullet"
            ])
            description_el = self._find_element([
                ".jobs-description__content",
                ".jobs-description-content__text",
                ".jobs-box__html-content"
            ])

            # Get job ID from URL
            job_id = ""
            url_match = re.search(r"/jobs/view/(\d+)", self.page.url)
            if url_match:
                job_id = url_match.group(1)

            return Job(
                id=job_id,
                title=title_el.inner_text().strip() if title_el else "Unknown",
                company=company_el.inner_text().strip() if company_el else "Unknown",
                location=location_el.inner_text().strip() if location_el else "Unknown",
                description=description_el.inner_text().strip() if description_el else "",
                url=self.page.url,
                source="linkedin",
            )

        except Exception as e:
            print(f"Error extracting job details: {e}")
            return None

    def search(
        self,
        keywords: str,
        location: str,
        remote_options: list[str] = None,
        experience_level: list[str] = None,
        date_posted: str = None,
        max_jobs: int = 50,
        **kwargs,
    ) -> list[Job]:
        """Search for jobs on LinkedIn."""
        url = self._build_search_url(keywords, location, remote_options, experience_level, date_posted)
        print(f"Searching: {url}")

        self.page.goto(url)
        time.sleep(5)

        # Scroll to trigger lazy loading
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        time.sleep(2)

        # Find job cards
        selectors = [
            "li.jobs-search-results__list-item",
            "[data-occludable-job-id]",
            ".job-card-container",
            ".jobs-search-result-item",
            "div.job-card-list__entity-lockup",
            "ul.jobs-search__results-list > li",
        ]

        job_cards = []
        for selector in selectors:
            job_cards = self.page.query_selector_all(selector)
            if job_cards:
                break

        print(f"Found {len(job_cards)} job cards")

        jobs = []
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                card.click()
                time.sleep(1.5)

                job = self._extract_job_details()
                if job:
                    if self.is_new_job(job.id):
                        jobs.append(job)
                        self.existing_job_ids.add(job.id)
                        print(f"[{i+1}] NEW: {job.title} at {job.company}")
                    else:
                        print(f"[{i+1}] SKIP: {job.title} at {job.company} (already saved)")

            except Exception as e:
                print(f"Error processing job {i+1}: {e}")

        return jobs

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a single job by ID."""
        url = f"https://www.linkedin.com/jobs/view/{job_id}"
        print(f"Fetching: {url}")

        self.page.goto(url)
        time.sleep(3)

        return self._extract_job_details()
