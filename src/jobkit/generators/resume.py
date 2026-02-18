"""Resume generator."""

from pathlib import Path
from typing import Optional

from .llm import LLMClient
from ..scrapers.base import Job


RESUME_SYSTEM_PROMPT = """You are an expert executive resume writer. You create professional,
ATS-optimized resumes that highlight key achievements and match job requirements.

Guidelines:
- Professional, executive tone
- Quantify achievements where possible
- Highlight only key areas for readability
- Tailor skills and experience to match the specific role
- Keep to 1-2 pages maximum
- Use action verbs and results-oriented language
- Format in clean, professional markdown
"""

RESUME_PROMPT_TEMPLATE = """Create a tailored resume for the following job:

## Target Role
**Title:** {job_title}
**Company:** {company}

## Job Description
{job_description}

## Candidate Background
{background}

## Instructions
Create a professional resume tailored for this specific role.
- Start with the candidate's name as a top heading
- Include contact info (email, phone) directly below the name if available in background
- Use section headers for: Summary, Experience, Skills, Education
- Emphasize experience and skills that match the job requirements
- Highlight relevant achievements with metrics where possible
- Keep it concise and scannable
- Use bullet points for achievements and responsibilities

FORMAT:
- Use ## for section headers (Experience, Skills, Education, etc.)
- Use **bold** for company names, job titles, and key achievements
- Use bullet points (-) for listing accomplishments
- Start with # for the candidate's name as the main heading

CRITICAL:
- Output ONLY the resume itself. Do NOT include any preamble like "Here is a resume".
- Do NOT wrap in code blocks or use triple backticks.
- Start DIRECTLY with the candidate's name.
- Spell the candidate's name EXACTLY as shown in the background.
- Include email and phone from the background if available.
"""


def clean_llm_output(text: str) -> str:
    """Remove common LLM artifacts from generated text."""
    import re

    # Remove markdown code blocks
    text = re.sub(r'^```(?:markdown)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)

    # Remove common preambles
    preambles = [
        r'^Here is (?:a |the )?(?:tailored |professional )?resume.*?:\s*\n*',
        r'^Here\'s (?:a |the )?(?:tailored |professional )?resume.*?:\s*\n*',
        r'^I\'ve (?:written|created|drafted).*?:\s*\n*',
        r'^Below is.*?:\s*\n*',
        r'^The following is.*?:\s*\n*',
    ]
    for pattern in preambles:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove lines that are just ## or ###
    text = re.sub(r'\n#+\s*\n', '\n\n', text)

    return text.strip()


class ResumeGenerator:
    """Generate tailored resumes using LLM."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate(
        self,
        job: Job,
        background: str,
        additional_instructions: str = None,
    ) -> str:
        """Generate a tailored resume for a job."""
        prompt = RESUME_PROMPT_TEMPLATE.format(
            job_title=job.title,
            company=job.company,
            job_description=job.description,
            background=background,
        )

        if additional_instructions:
            prompt += f"\n\n## Additional Instructions\n{additional_instructions}"

        result = self.llm.generate(prompt, system_prompt=RESUME_SYSTEM_PROMPT)
        return clean_llm_output(result)

    def save(self, content: str, output_path: Path) -> Path:
        """Save resume to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(content)
        return output_path
