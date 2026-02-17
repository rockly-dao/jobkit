# JobKit

**Open source job hunting toolkit** - Search jobs, generate tailored resumes and cover letters with AI.

JobKit automates the tedious parts of job hunting so you can focus on what matters: landing interviews.

## Features

- **Job Search**: Scrape jobs from LinkedIn (more sources coming)
- **AI-Powered Generation**: Create tailored resumes and cover letters using local (Ollama) or cloud (Claude, GPT) LLMs
- **Web Interface**: Clean, simple UI for managing your job search
- **CLI**: Power user? Use the command line
- **100% Local**: Your data stays on your machine. No accounts, no tracking.

## Quick Start

### Install

```bash
# Clone the repo
git clone https://github.com/jobkit/jobkit.git
cd jobkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install
pip install -e .

# Install browser automation
playwright install chromium
```

### Run

```bash
# Start the web interface
jobkit web

# Or use the CLI
jobkit search "software engineer" --location "Remote"
jobkit list
jobkit generate JOB_ID
```

## Usage

### Web Interface

```bash
jobkit web
```

Open http://localhost:5000 in your browser.

1. **Set up your profile**: Add your name, email, and paste your resume
2. **Search for jobs**: Enter keywords and location, or scrape from LinkedIn
3. **Generate applications**: Click "Generate" on any job to create a tailored resume and cover letter

### Command Line

```bash
# Search for jobs
jobkit search "data scientist" --location "New York"

# List saved jobs
jobkit list
jobkit list --new  # Only show jobs without applications

# Fetch a specific job by LinkedIn URL
jobkit job https://www.linkedin.com/jobs/view/123456789

# Generate application materials
jobkit generate 123456789
```

## LLM Configuration

JobKit supports multiple LLM providers:

### Ollama (Free, Local)

1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull llama3`
3. Start Ollama: `ollama serve`
4. In JobKit settings, select "Ollama" and model "llama3"

### Anthropic Claude

1. Get an API key: https://console.anthropic.com
2. Set environment variable: `export ANTHROPIC_API_KEY=your-key`
3. In JobKit settings, select "Anthropic" and model "claude-sonnet-4-20250514"

### OpenAI GPT

1. Get an API key: https://platform.openai.com
2. Set environment variable: `export OPENAI_API_KEY=your-key`
3. In JobKit settings, select "OpenAI" and model "gpt-4"

## Docker

```bash
# Build and run
docker-compose up -d

# Or just JobKit (without Ollama)
docker build -t jobkit .
docker run -p 5000:5000 -v jobkit-data:/data jobkit
```

## Project Structure

```
src/jobkit/
├── cli.py           # Command-line interface
├── config.py        # Configuration management
├── scrapers/        # Job board scrapers
│   ├── base.py      # Base scraper class
│   └── linkedin.py  # LinkedIn implementation
├── generators/      # AI content generators
│   ├── llm.py       # Multi-provider LLM client
│   ├── resume.py    # Resume generator
│   └── cover_letter.py
└── web/             # Flask web interface
    ├── app.py
    └── templates/
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Priority Areas

- **New job board scrapers**: Indeed, Glassdoor, ZipRecruiter
- **PDF export**: Professional resume formatting
- **Test coverage**: We need more tests
- **UI improvements**: Make it even easier to use

## Disclaimer

This tool is for personal use to assist with job hunting. Be respectful of websites' terms of service. LinkedIn may block automated access - use responsibly.

## License

MIT License - see [LICENSE](LICENSE)

---

**Happy job hunting!**
