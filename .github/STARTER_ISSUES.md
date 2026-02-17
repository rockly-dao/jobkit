# Starter Issues for GitHub

Copy these to GitHub Issues after creating the repository.

---

## Issue 1: Add Indeed Job Scraper
**Labels:** `good first issue`, `enhancement`, `help wanted`

**Description:**
Add a scraper for Indeed.com jobs, similar to the LinkedIn scraper.

**Implementation:**
1. Create `src/jobkit/scrapers/indeed.py`
2. Inherit from `BaseScraper`
3. Implement `search()` and `get_job()` methods
4. Add to `__init__.py` exports

**Acceptance Criteria:**
- [ ] Can search for jobs by keyword and location
- [ ] Returns `Job` objects with all fields populated
- [ ] Handles pagination
- [ ] Has basic error handling

---

## Issue 2: PDF Export for Resumes
**Labels:** `good first issue`, `enhancement`, `help wanted`

**Description:**
Add the ability to export generated resumes as professionally formatted PDFs.

**Implementation:**
Consider using `reportlab` or `weasyprint`. The PDF should look professional and clean.

**Acceptance Criteria:**
- [ ] "Download PDF" button on application detail page
- [ ] PDF includes proper formatting (headers, bullets, etc.)
- [ ] Works on all platforms

---

## Issue 3: Add Glassdoor Scraper
**Labels:** `enhancement`, `help wanted`

**Description:**
Add a scraper for Glassdoor job postings.

**Notes:**
Glassdoor requires login. Consider if we want to handle auth or only support public listings.

---

## Issue 4: Job Matching Score
**Labels:** `enhancement`

**Description:**
Add a matching score that shows how well a job matches the user's profile.

**Implementation Ideas:**
- Extract keywords from job description
- Compare with user's background/skills
- Display percentage match on job cards

---

## Issue 5: Email Application Feature
**Labels:** `enhancement`

**Description:**
Allow users to email their generated resume and cover letter directly from the app.

**Implementation:**
- Add SMTP settings to configuration
- Add "Email Application" button
- Support Gmail, Outlook, generic SMTP

---

## Issue 6: Browser Extension for Saving Jobs
**Labels:** `enhancement`, `help wanted`

**Description:**
Create a browser extension that adds a "Save to JobKit" button on job posting pages.

**Notes:**
Could be a Chrome/Firefox extension that communicates with a local JobKit server.

---

## Issue 7: Mobile-Responsive UI
**Labels:** `good first issue`, `enhancement`

**Description:**
Improve the web UI for mobile devices.

**Implementation:**
- Review all templates for mobile breakpoints
- Fix any overflow/spacing issues
- Test on actual mobile devices

---

## Issue 8: Add Test Coverage
**Labels:** `good first issue`, `help wanted`

**Description:**
Increase test coverage for the project.

**Priority Areas:**
- [ ] LinkedIn scraper tests (with mocked responses)
- [ ] Web app route tests
- [ ] CLI command tests

---

## Issue 9: Dark Mode
**Labels:** `enhancement`

**Description:**
Add a dark mode option to the web interface.

**Implementation:**
- Add theme toggle in settings
- Use Tailwind's dark mode classes
- Persist preference in config

---

## Issue 10: ZipRecruiter Scraper
**Labels:** `enhancement`, `help wanted`

**Description:**
Add a scraper for ZipRecruiter job postings.
