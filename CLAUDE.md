# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JobKit is an open source job hunting toolkit that helps users search for jobs, save them locally, and generate tailored resumes and cover letters using AI (LLMs).

## Commands

```bash
# Install in development mode
pip install -e ".[dev]"
playwright install chromium

# Run the web interface
jobkit web

# Run CLI commands
jobkit search "software engineer" --location "Remote"
jobkit list
jobkit generate JOB_ID

# Run tests
pytest
pytest tests/test_config.py -v  # single test file

# Linting and formatting
ruff check .
black .
```

## Architecture

### Core Modules

- `src/jobkit/cli.py` - Command-line interface entry point
- `src/jobkit/config.py` - Configuration management using dataclasses, stores in `~/.jobkit/`

### Scrapers (`src/jobkit/scrapers/`)

- `base.py` - Abstract `BaseScraper` class and `Job` dataclass
- `linkedin.py` - LinkedIn scraper using Playwright (browser automation)
- New scrapers should inherit from `BaseScraper` and implement `search()` and `get_job()` methods

### Generators (`src/jobkit/generators/`)

- `llm.py` - Unified `LLMClient` supporting Ollama, Anthropic, and OpenAI
- `resume.py` - `ResumeGenerator` creates tailored resumes
- `cover_letter.py` - `CoverLetterGenerator` creates cover letters

### Web UI (`src/jobkit/web/`)

- `app.py` - Flask application with routes for all features
- `templates/` - Jinja2 templates using Tailwind CSS

## Key Patterns

- **Provider abstraction**: LLMClient uses a unified interface for different LLM providers
- **Dataclasses for models**: Job, Config, SearchConfig, LLMConfig
- **Incremental processing**: Scrapers track existing jobs to avoid duplicates
- **Local-first**: All data stored in `~/.jobkit/` by default

## Adding a New Job Board Scraper

1. Create `src/jobkit/scrapers/newsite.py`
2. Inherit from `BaseScraper`
3. Implement `search(keywords, location, **filters) -> list[Job]`
4. Implement `get_job(job_id) -> Optional[Job]`
5. Export from `__init__.py`
