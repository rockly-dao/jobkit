---
layout: default
title: JobKit - AI-Powered Job Hunting Toolkit
---

# JobKit

**Open source AI-powered job hunting toolkit**

JobKit helps you search for jobs, build a comprehensive profile from multiple sources, and generate tailored resumes and cover letters using AI.

---

## Features

### Job Search
- **LinkedIn Integration** - Search and save jobs directly from LinkedIn
- **Smart Filtering** - Filter by keywords, location, remote options
- **Job Management** - Save, organize, and track jobs you're interested in

### Profile Builder
- **Multi-Source Import** - Build your profile from:
  - Resume upload (PDF, DOCX, TXT)
  - LinkedIn profile
  - GitHub profile (repos, languages, contributions)
- **Smart Merging** - Combines information from all sources intelligently

### AI-Powered Applications
- **Tailored Resumes** - Generate resumes customized for each job
- **Cover Letters** - Create compelling cover letters that match job requirements
- **PDF Export** - Download professional PDFs ready to submit
- **Multiple LLM Support** - Works with Ollama (free/local), Anthropic Claude, or OpenAI GPT

---

## Quick Start

### Installation

```bash
# Install from PyPI
pip install jobkit

# Install Playwright for LinkedIn integration
playwright install chromium
```

### Running JobKit

```bash
# Start the web interface
jobkit web --port 8080
```

Then open [http://localhost:8080](http://localhost:8080) in your browser.

---

## Screenshots

### Dashboard
Manage your saved jobs and generated applications from one place.

### Profile Builder
Import your background from multiple sources - resume, LinkedIn, GitHub.

### Application Generator
Generate tailored resumes and cover letters with one click.

---

## LLM Setup

JobKit supports multiple AI providers:

### Ollama (Free, Local)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3

# Start Ollama (keep running)
ollama serve
```

### Cloud Providers
For Anthropic Claude or OpenAI GPT:
1. Go to Settings in JobKit
2. Select your provider
3. Enter your API key

---

## Tech Stack

- **Backend**: Python, Flask
- **Job Scraping**: Playwright (browser automation)
- **AI/LLM**: Ollama, Anthropic, OpenAI
- **PDF Generation**: fpdf2
- **Frontend**: Jinja2 templates, Tailwind CSS

---

## Contributing

JobKit is open source! Contributions welcome.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## Links

- [GitHub Repository](https://github.com/rocky-dao/jobkit)
- [Report Issues](https://github.com/rocky-dao/jobkit/issues)
- [PyPI Package](https://pypi.org/project/jobkit/)

---

## License

MIT License - free for personal and commercial use.

---

<p align="center">
  <strong>Built with AI, for job seekers</strong>
</p>
