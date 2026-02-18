# JobKit

**Open source AI-powered job hunting toolkit**

Search jobs, build your profile from multiple sources, and generate tailored resumes and cover letters with AI.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Job Search** - Search and save jobs from LinkedIn
- **Multi-Source Profile** - Import from resume (PDF/DOCX), LinkedIn, and GitHub
- **AI-Powered Generation** - Create tailored resumes and cover letters
- **PDF Export** - Download professional PDFs ready to submit
- **Multiple LLM Support** - Ollama (free/local), Anthropic Claude, or OpenAI GPT
- **100% Local** - Your data stays on your machine

## Quick Start

### Install

```bash
pip install jobkit
playwright install chromium
```

### Run

```bash
jobkit web --port 8080
```

Open http://localhost:8080 in your browser.

## Usage

### 1. Set Up Your Profile

Import your background from multiple sources:
- **Upload Resume** - PDF, DOCX, or TXT
- **LinkedIn** - Import experience and education
- **GitHub** - Import projects and languages

All sources are merged intelligently.

### 2. Search for Jobs

- Enter keywords and location
- Browser opens for LinkedIn login (cookies saved for future sessions)
- Save interesting jobs with one click

### 3. Generate Applications

Click "Generate Application" on any saved job to create:
- Tailored resume matching the job requirements
- Compelling cover letter
- Download as professional PDFs

## LLM Setup

### Ollama (Free, Local) - Recommended

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
ollama serve
```

### Cloud Providers

Set your API key in Settings:
- **Anthropic**: claude-sonnet-4-20250514
- **OpenAI**: gpt-4

## CLI Commands

```bash
jobkit search "software engineer" --location "Remote"
jobkit list
jobkit generate JOB_ID
jobkit config
```

## Development

```bash
git clone https://github.com/rocky-dao/jobkit.git
cd jobkit
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

## Tech Stack

- **Backend**: Python, Flask
- **Scraping**: Playwright
- **AI**: Ollama, Anthropic, OpenAI
- **PDF**: fpdf2
- **Frontend**: Tailwind CSS

## Contributing

Contributions welcome! Areas of interest:
- New job board scrapers (Indeed, Glassdoor)
- Profile importers (Twitter, personal websites)
- UI improvements

## License

MIT License - free for personal and commercial use.

---

**Built with AI, for job seekers**
