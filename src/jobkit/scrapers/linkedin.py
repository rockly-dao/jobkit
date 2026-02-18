"""LinkedIn job scraper."""

import json
import re
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright, Browser, Page

from .base import BaseScraper, Job


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job listings."""

    BASE_URL = "https://www.linkedin.com"
    JOBS_URL = "https://www.linkedin.com/jobs/search/"

    def __init__(self, headless: bool = False, data_dir: Path = None):
        super().__init__()
        self.headless = headless
        self.data_dir = Path(data_dir) if data_dir else Path.home() / ".jobkit"
        self.cookies_file = self.data_dir / "linkedin_cookies.json"
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self._logged_in = False

    def start(self):
        """Start the browser."""
        print("Starting Playwright...")
        self.playwright = sync_playwright().start()
        print("Playwright started, launching Chrome...")
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        print("Chrome launched, creating context...")
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        # Load saved cookies if available
        if self.cookies_file.exists():
            try:
                cookies = json.loads(self.cookies_file.read_text())
                self.context.add_cookies(cookies)
                print("Loaded saved LinkedIn cookies")
            except Exception as e:
                print(f"Could not load cookies: {e}")

        self.page = self.context.new_page()
        print("Browser ready!")

    def save_cookies(self):
        """Save cookies for future sessions."""
        try:
            cookies = self.context.cookies()
            self.cookies_file.parent.mkdir(parents=True, exist_ok=True)
            self.cookies_file.write_text(json.dumps(cookies))
            print("Saved LinkedIn cookies for future sessions")
        except Exception as e:
            print(f"Could not save cookies: {e}")

    def is_logged_in(self) -> bool:
        """Check if currently logged in to LinkedIn."""
        try:
            # Go to LinkedIn feed to check login status
            self.page.goto(f"{self.BASE_URL}/feed/", wait_until="domcontentloaded", timeout=10000)
            time.sleep(2)

            current_url = self.page.url

            # If redirected to login, not logged in
            if "login" in current_url or "authwall" in current_url or "checkpoint" in current_url:
                return False

            # If on feed or has nav elements, logged in
            if "feed" in current_url:
                return True

            # Check for logged-in nav elements
            nav = self.page.query_selector('nav[aria-label="Primary"]') or \
                  self.page.query_selector('.global-nav') or \
                  self.page.query_selector('[data-alias="nav-feed"]')
            return nav is not None

        except Exception as e:
            print(f"Error checking login status: {e}")
            return False

    def stop(self):
        """Stop the browser."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self, wait_for_user: bool = True, timeout: int = 300) -> bool:
        """Navigate to LinkedIn login page and wait for user to log in."""
        if self._logged_in:
            return True

        # First check if already logged in
        if self.is_logged_in():
            print("Already logged in to LinkedIn!")
            self._logged_in = True
            self.save_cookies()
            return True

        # Need to log in
        self.page.goto(f"{self.BASE_URL}/login", wait_until="domcontentloaded")

        if wait_for_user:
            print("\n" + "=" * 50)
            print("Please log in to LinkedIn in the browser window.")
            print(f"Waiting up to {timeout // 60} minutes for login...")
            print("=" * 50 + "\n")

            # Wait for login by checking URL change
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    current_url = self.page.url
                    # Check various success URLs
                    if any(x in current_url for x in ["/feed", "/jobs", "/mynetwork", "/messaging"]):
                        self._logged_in = True
                        print("Login successful!")
                        self.save_cookies()
                        return True
                    # Still on login page
                    if "login" not in current_url and "checkpoint" not in current_url and "authwall" not in current_url:
                        # Might be logged in, verify
                        if self.is_logged_in():
                            self._logged_in = True
                            print("Login successful!")
                            self.save_cookies()
                            return True
                except:
                    pass
                time.sleep(3)

            print("Login timeout - please try again")
            return False

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
            panel_found = False
            for sel in [".jobs-unified-top-card", ".job-details-jobs-unified-top-card", ".jobs-details", ".jobs-search__job-details"]:
                try:
                    self.page.wait_for_selector(sel, timeout=3000)
                    panel_found = True
                    break
                except:
                    continue

            if not panel_found:
                print("  No job details panel found")

            # Get job ID from URL first
            job_id = ""
            current_url = self.page.url
            url_match = re.search(r"/jobs/view/(\d+)", current_url)
            if url_match:
                job_id = url_match.group(1)
            else:
                # Try getting from currentJobId in URL params
                url_match = re.search(r"currentJobId=(\d+)", current_url)
                if url_match:
                    job_id = url_match.group(1)

            # Extract fields with multiple selector attempts
            title_el = self._find_element([
                ".jobs-unified-top-card__job-title",
                ".job-details-jobs-unified-top-card__job-title",
                ".jobs-unified-top-card h1",
                ".jobs-unified-top-card h2",
                "h1.t-24",
                ".job-details h1",
                ".jobs-details-top-card__job-title"
            ])
            company_el = self._find_element([
                ".jobs-unified-top-card__company-name",
                ".job-details-jobs-unified-top-card__company-name",
                ".jobs-unified-top-card__primary-description a",
                ".topcard__org-name-link",
                ".jobs-details-top-card__company-url"
            ])
            location_el = self._find_element([
                ".jobs-unified-top-card__bullet",
                ".job-details-jobs-unified-top-card__bullet",
                ".jobs-unified-top-card__workplace-type",
                ".topcard__flavor--bullet",
                ".jobs-details-top-card__bullet"
            ])
            description_el = self._find_element([
                ".jobs-description__content",
                ".jobs-description-content__text",
                ".jobs-box__html-content",
                ".jobs-description"
            ])

            title = title_el.inner_text().strip() if title_el else "Unknown"
            company = company_el.inner_text().strip() if company_el else "Unknown"
            location = location_el.inner_text().strip() if location_el else "Unknown"
            description = description_el.inner_text().strip() if description_el else ""

            return Job(
                id=job_id,
                title=title,
                company=company,
                location=location,
                description=description[:5000],  # Limit description length
                url=current_url,
                source="linkedin",
            )

        except Exception as e:
            print(f"Error extracting job details: {e}")
            import traceback
            traceback.print_exc()
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
        print("search() called")

        # Auto-start browser if not running
        if not self.page:
            print("Browser not started, starting now...")
            self.start()
        else:
            print("Browser already running")

        # Build search URL first
        url = self._build_search_url(keywords, location, remote_options, experience_level, date_posted)
        print(f"Search URL: {url}")

        # Navigate directly to the jobs search page
        print("Navigating to LinkedIn Jobs...")
        self.page.goto(url, wait_until="domcontentloaded")
        time.sleep(3)

        # Check if we need to log in (redirected to login page)
        current_url = self.page.url
        login_pages = ["login", "authwall", "checkpoint", "uas/login", "signin"]

        if any(x in current_url for x in login_pages):
            print("\n" + "=" * 50)
            print("LOGIN REQUIRED")
            print("Please log in to LinkedIn in the browser window.")
            print("Take your time - waiting up to 5 minutes...")
            print("=" * 50 + "\n")

            # Wait for user to fully log in (5 minutes)
            start_time = time.time()
            timeout = 300
            logged_in = False

            while time.time() - start_time < timeout:
                time.sleep(3)  # Check every 3 seconds

                try:
                    current_url = self.page.url

                    # Still on a login-related page - keep waiting
                    if any(x in current_url for x in login_pages):
                        continue

                    # Check if we're on a real LinkedIn page (feed, jobs, etc.)
                    success_indicators = ["/feed", "/jobs", "/mynetwork", "/messaging", "/notifications"]
                    if any(x in current_url for x in success_indicators):
                        # Verify by checking for nav element
                        time.sleep(2)  # Wait for page to fully load
                        nav = self.page.query_selector('.global-nav__content') or \
                              self.page.query_selector('[data-test-global-nav]') or \
                              self.page.query_selector('.scaffold-layout')

                        if nav:
                            print("Login successful!")
                            logged_in = True
                            break

                except Exception as e:
                    # Page might be loading, continue waiting
                    continue

            if not logged_in:
                raise Exception("Login timeout - please try again and complete the full login process")

            self._logged_in = True
            print("Saving cookies...")
            try:
                self.save_cookies()
            except Exception as e:
                print(f"Warning: Could not save cookies: {e}")

            # Now navigate to the jobs search
            print(f"Navigating to job search with your keywords...")
            time.sleep(3)
            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                print(f"On jobs page: {self.page.url}")
            except Exception as e:
                print(f"Error navigating to jobs: {e}")
                raise
            time.sleep(3)
        else:
            # Already logged in
            self._logged_in = True
            print("Already logged in to LinkedIn")

        print("Proceeding with job search...")
        print(f"Current URL: {self.page.url}")

        print("Page loaded. Scrolling to load more jobs...")

        # Scroll to trigger lazy loading
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        time.sleep(2)

        print("Looking for job cards...")

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
        processed = 0

        for i in range(min(len(job_cards), max_jobs)):
            try:
                # Re-query job cards each time (they can become detached)
                current_cards = []
                for selector in selectors:
                    current_cards = self.page.query_selector_all(selector)
                    if current_cards:
                        break

                if i >= len(current_cards):
                    print(f"[{i+1}] No more cards available")
                    break

                card = current_cards[i]

                # Try to click the card
                try:
                    card.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    card.click()
                except Exception:
                    # Fallback: use JavaScript click
                    try:
                        self.page.evaluate(f"document.querySelectorAll('{selectors[0]}')[{i}]?.click()")
                    except:
                        print(f"[{i+1}] Could not click card, skipping")
                        continue

                time.sleep(1.5)

                job = self._extract_job_details()
                if job:
                    print(f"[{i+1}] Extracted: id={job.id}, title={job.title}, company={job.company}")
                    if job.id:
                        # All jobs are new since we don't pre-load existing
                        jobs.append(job)
                        self.existing_job_ids.add(job.id)
                        print(f"[{i+1}] SAVED: {job.title} at {job.company}")
                        processed += 1
                    else:
                        print(f"[{i+1}] No job ID found, skipping")
                else:
                    print(f"[{i+1}] Could not extract job details")

            except Exception as e:
                print(f"[{i+1}] Error: {e}")
                continue

        print(f"Processed {processed} jobs, found {len(jobs)} new ones")
        return jobs

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a single job by ID."""
        # Auto-start browser if not running
        if not self.page:
            self.start()

        url = f"https://www.linkedin.com/jobs/view/{job_id}"
        print(f"Fetching: {url}")

        self.page.goto(url)
        time.sleep(3)

        return self._extract_job_details()
