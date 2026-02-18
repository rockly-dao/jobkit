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
- Pay careful attention to spelling names correctly
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

FORMAT:
- Use **bold** for key skills, achievements, and important phrases you want to highlight
- Keep paragraphs clean and readable

CRITICAL:
- Output ONLY the cover letter itself. Do NOT include any preamble like "Here is a cover letter" or "I've written".
- Do NOT wrap in code blocks or use triple backticks.
- Start DIRECTLY with "Dear Hiring Team," or similar greeting.
- Spell the candidate's name EXACTLY as shown in the background.
"""


def clean_llm_output(text: str) -> str:
    """Remove common LLM artifacts from generated text."""
    import re

    # Remove markdown code blocks
    text = re.sub(r'^```(?:markdown)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)

    # Remove common preambles
    preambles = [
        r'^Here is (?:a |the )?(?:tailored |professional )?cover letter.*?:\s*\n*',
        r'^Here\'s (?:a |the )?(?:tailored |professional )?cover letter.*?:\s*\n*',
        r'^I\'ve (?:written|created|drafted).*?:\s*\n*',
        r'^Below is.*?:\s*\n*',
        r'^The following is.*?:\s*\n*',
    ]
    for pattern in preambles:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove lines that are just ## or ###
    text = re.sub(r'\n#+\s*\n', '\n\n', text)

    return text.strip()


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

        result = self.llm.generate(prompt, system_prompt=COVER_LETTER_SYSTEM_PROMPT)
        return clean_llm_output(result)

    def save(self, content: str, output_path: Path) -> Path:
        """Save cover letter to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(content)
        return output_path
