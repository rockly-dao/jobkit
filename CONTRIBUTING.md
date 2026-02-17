# Contributing to JobKit

First off, thank you for considering contributing to JobKit! It's people like you that make JobKit such a great tool for job seekers everywhere.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- Your operating system and Python version
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Any error messages or logs

### Suggesting Features

Feature suggestions are welcome! Please open an issue and describe:

- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

### Pull Requests

1. Fork the repo and create your branch from `main`
2. Install development dependencies: `pip install -e ".[dev]"`
3. Make your changes
4. Run tests: `pytest`
5. Run linting: `ruff check . && black --check .`
6. Submit your PR!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/jobkit.git
cd jobkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Run the web interface
jobkit web
```

## Project Structure

```
jobkit/
├── src/jobkit/
│   ├── cli.py           # Command-line interface
│   ├── config.py        # Configuration management
│   ├── scrapers/        # Job board scrapers
│   │   ├── base.py      # Base scraper class
│   │   └── linkedin.py  # LinkedIn scraper
│   ├── generators/      # Resume/cover letter generators
│   │   ├── llm.py       # LLM client (Ollama, Anthropic, OpenAI)
│   │   ├── resume.py    # Resume generator
│   │   └── cover_letter.py
│   └── web/             # Flask web interface
│       ├── app.py
│       └── templates/
└── tests/
```

## Areas We Need Help With

### High Priority
- **Additional job board scrapers**: Indeed, Glassdoor, ZipRecruiter
- **Better LinkedIn selectors**: LinkedIn changes their HTML frequently
- **PDF export**: Convert markdown resumes to professional PDFs
- **Tests**: We need more test coverage

### Medium Priority
- **Job matching algorithm**: Score jobs against user profile
- **Email integration**: Send applications directly
- **Browser extension**: Save jobs while browsing
- **Mobile-responsive UI**: Better experience on phones

### Low Priority / Nice to Have
- **Analytics dashboard**: Track application stats
- **AI interview prep**: Generate practice questions
- **Salary research**: Integrate salary data

## Code Style

- Use `black` for formatting
- Use `ruff` for linting
- Write docstrings for public functions
- Keep functions focused and small
- Add type hints where helpful

## Questions?

Feel free to open an issue for any questions about contributing!
