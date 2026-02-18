"""LinkedIn profile importer using Playwright."""

import json
import time
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, Page


class LinkedInProfileImporter:
    """Import profile data from LinkedIn."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.cookies_file = self.data_dir / "linkedin_cookies.json"

    def import_profile(self, profile_url: str) -> dict:
        """
        Import profile from LinkedIn URL.
        Returns dict with name, headline, about, experience, education, skills.
        """
        playwright = None
        browser = None

        try:
            print("Starting Playwright...", flush=True)
            playwright = sync_playwright().start()

            print("Launching browser...", flush=True)
            browser = playwright.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )

            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # Load cookies if available
            if self.cookies_file.exists():
                try:
                    cookies = json.loads(self.cookies_file.read_text())
                    context.add_cookies(cookies)
                    print("Loaded saved cookies", flush=True)
                except Exception as e:
                    print(f"Could not load cookies: {e}", flush=True)

            page = context.new_page()
            page.set_default_timeout(120000)  # 2 minute default timeout

            # Navigate to profile
            print(f"Navigating to {profile_url}...", flush=True)
            page.goto(profile_url, wait_until="domcontentloaded", timeout=120000)
            time.sleep(3)

            # Check if logged in
            current_url = page.url
            login_indicators = ["login", "authwall", "checkpoint", "uas/login", "signin"]

            if any(x in current_url for x in login_indicators):
                print("\n" + "=" * 50, flush=True)
                print("LOGIN REQUIRED", flush=True)
                print("Please log in to LinkedIn in the browser window.", flush=True)
                print("Take your time - waiting up to 5 minutes...", flush=True)
                print("=" * 50 + "\n", flush=True)

                # Wait for login (up to 5 minutes)
                start_time = time.time()
                timeout = 300  # 5 minutes
                logged_in = False

                while time.time() - start_time < timeout:
                    time.sleep(3)
                    try:
                        current_url = page.url

                        # Still on login page
                        if any(x in current_url for x in login_indicators):
                            continue

                        # Check for successful login indicators
                        success_indicators = ["/feed", "/in/", "/mynetwork", "/messaging", "/jobs"]
                        if any(x in current_url for x in success_indicators):
                            print("Login successful!", flush=True)
                            logged_in = True
                            break

                    except Exception as e:
                        print(f"Waiting... ({e})", flush=True)
                        continue

                if not logged_in:
                    raise Exception("Login timeout - please try again")

                # Save cookies for next time
                try:
                    cookies = context.cookies()
                    self.cookies_file.write_text(json.dumps(cookies))
                    print("Saved cookies for future sessions", flush=True)
                except Exception as e:
                    print(f"Could not save cookies: {e}", flush=True)

                # Navigate to profile
                print(f"Navigating to profile: {profile_url}", flush=True)
                time.sleep(2)
                page.goto(profile_url, wait_until="domcontentloaded", timeout=120000)
                time.sleep(3)

            print("Extracting profile data...", flush=True)
            profile = self._extract_profile(page)
            print(f"Extracted: {profile.get('name', 'Unknown')}", flush=True)

            return profile

        finally:
            print("Closing browser...", flush=True)
            if browser:
                try:
                    browser.close()
                except:
                    pass
            if playwright:
                try:
                    playwright.stop()
                except:
                    pass

    def _extract_profile(self, page: Page) -> dict:
        """Extract profile information from the page."""
        profile = {
            "name": "",
            "headline": "",
            "about": "",
            "experience": [],
            "education": [],
            "skills": [],
        }

        # Wait for page to load
        time.sleep(2)

        # Name
        try:
            name_el = page.query_selector("h1")
            if name_el:
                profile["name"] = name_el.inner_text().strip()
                print(f"  Found name: {profile['name']}", flush=True)
        except Exception as e:
            print(f"  Could not get name: {e}", flush=True)

        # Headline
        try:
            headline_el = page.query_selector(".text-body-medium")
            if headline_el:
                profile["headline"] = headline_el.inner_text().strip()
                print(f"  Found headline: {profile['headline'][:50]}...", flush=True)
        except Exception as e:
            print(f"  Could not get headline: {e}", flush=True)

        # About section
        try:
            about_section = page.query_selector("#about")
            if about_section:
                about_container = about_section.query_selector("xpath=following-sibling::div[1]")
                if about_container:
                    # Click "see more" if present
                    try:
                        see_more = about_container.query_selector("button:has-text('see more')")
                        if see_more:
                            see_more.click()
                            time.sleep(0.5)
                    except:
                        pass

                    about_text = about_container.query_selector(".inline-show-more-text span[aria-hidden='true']")
                    if about_text:
                        profile["about"] = about_text.inner_text().strip()
                        print(f"  Found about section", flush=True)
        except Exception as e:
            print(f"  Could not get about: {e}", flush=True)

        # Experience section
        try:
            exp_section = page.query_selector("#experience")
            if exp_section:
                exp_container = exp_section.query_selector("xpath=following-sibling::div[1]")
                if exp_container:
                    exp_items = exp_container.query_selector_all("li.artdeco-list__item")
                    for item in exp_items[:10]:
                        try:
                            title = item.query_selector(".t-bold span[aria-hidden='true']")
                            company = item.query_selector(".t-normal span[aria-hidden='true']")
                            duration = item.query_selector(".t-black--light span[aria-hidden='true']")

                            exp_entry = {
                                "title": title.inner_text().strip() if title else "",
                                "company": company.inner_text().strip() if company else "",
                                "duration": duration.inner_text().strip() if duration else "",
                            }
                            if exp_entry["title"]:
                                profile["experience"].append(exp_entry)
                        except:
                            continue
                    print(f"  Found {len(profile['experience'])} experience entries", flush=True)
        except Exception as e:
            print(f"  Could not get experience: {e}", flush=True)

        # Education section
        try:
            edu_section = page.query_selector("#education")
            if edu_section:
                edu_container = edu_section.query_selector("xpath=following-sibling::div[1]")
                if edu_container:
                    edu_items = edu_container.query_selector_all("li.artdeco-list__item")
                    for item in edu_items[:5]:
                        try:
                            school = item.query_selector(".t-bold span[aria-hidden='true']")
                            degree = item.query_selector(".t-normal span[aria-hidden='true']")

                            edu_entry = {
                                "school": school.inner_text().strip() if school else "",
                                "degree": degree.inner_text().strip() if degree else "",
                            }
                            if edu_entry["school"]:
                                profile["education"].append(edu_entry)
                        except:
                            continue
                    print(f"  Found {len(profile['education'])} education entries", flush=True)
        except Exception as e:
            print(f"  Could not get education: {e}", flush=True)

        return profile

    def format_as_text(self, profile: dict) -> str:
        """Convert profile dict to readable text format."""
        lines = []

        if profile.get("name"):
            lines.append(profile["name"].upper())
        if profile.get("headline"):
            lines.append(profile["headline"])

        lines.append("")

        if profile.get("about"):
            lines.append("SUMMARY")
            lines.append(profile["about"])
            lines.append("")

        if profile.get("experience"):
            lines.append("EXPERIENCE")
            for exp in profile["experience"]:
                lines.append(f"{exp['title']} at {exp['company']}")
                if exp.get("duration"):
                    lines.append(f"  {exp['duration']}")
            lines.append("")

        if profile.get("education"):
            lines.append("EDUCATION")
            for edu in profile["education"]:
                if edu.get("degree"):
                    lines.append(f"{edu['degree']} - {edu['school']}")
                else:
                    lines.append(edu["school"])
            lines.append("")

        return "\n".join(lines)
