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
- Emphasize experience and skills that match the job requirements
- Highlight relevant achievements with metrics where possible
- Keep it concise and scannable
- Format as clean markdown

Output ONLY the resume content in markdown format, no additional commentary.
"""


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

        return self.llm.generate(prompt, system_prompt=RESUME_SYSTEM_PROMPT)

    def save(self, content: str, output_path: Path) -> Path:
        """Save resume to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(content)
        return output_path
