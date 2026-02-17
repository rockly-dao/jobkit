"""Cover letter generator."""

from pathlib import Path
from typing import Optional

from .llm import LLMClient
from ..scrapers.base import Job


COVER_LETTER_SYSTEM_PROMPT = """You are an expert cover letter writer. You create compelling,
professional cover letters that connect a candidate's experience to specific job requirements.

Guidelines:
- Executive tone, confident but not arrogant
- Address specific requirements from the job description
- Connect background directly to the company's needs
- Show understanding of the company and role
- Keep to 3-4 paragraphs maximum
- Be specific, not generic
- End with a clear call to action
"""

COVER_LETTER_PROMPT_TEMPLATE = """Create a tailored cover letter for the following job:

## Target Role
**Title:** {job_title}
**Company:** {company}

## Job Description
{job_description}

## Candidate Background
{background}

## Instructions
Write a compelling cover letter that:
1. Opens with a strong hook connecting to the role or company
2. Highlights 2-3 key qualifications that match the job requirements
3. Shows understanding of the company and what they need
4. Closes with confidence and a call to action

Output ONLY the cover letter content in markdown format, no additional commentary.
Start with "Dear Hiring Team at {company}," or appropriate greeting.
"""


class CoverLetterGenerator:
    """Generate tailored cover letters using LLM."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate(
        self,
        job: Job,
        background: str,
        additional_instructions: str = None,
    ) -> str:
        """Generate a tailored cover letter for a job."""
        prompt = COVER_LETTER_PROMPT_TEMPLATE.format(
            job_title=job.title,
            company=job.company,
            job_description=job.description,
            background=background,
        )

        if additional_instructions:
            prompt += f"\n\n## Additional Instructions\n{additional_instructions}"

        return self.llm.generate(prompt, system_prompt=COVER_LETTER_SYSTEM_PROMPT)

    def save(self, content: str, output_path: Path) -> Path:
        """Save cover letter to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(content)
        return output_path
