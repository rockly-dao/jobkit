"""Tests for resume and cover letter generators."""

import pytest
from unittest.mock import Mock, patch

from jobkit.generators.llm import LLMClient
from jobkit.generators.resume import ResumeGenerator
from jobkit.generators.cover_letter import CoverLetterGenerator


@pytest.fixture
def mock_llm():
    """Create a mock LLM client."""
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "Generated content here"
    return llm


@pytest.fixture
def sample_profile():
    """Sample user profile."""
    return {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "555-123-4567",
        "background": """
        Senior Software Engineer with 8 years of experience.
        Skills: Python, JavaScript, AWS, Machine Learning
        Experience: TechCorp (2020-Present), StartupXYZ (2016-2020)
        """
    }


@pytest.fixture
def sample_job():
    """Sample job posting."""
    return {
        "id": "123",
        "title": "Staff Engineer",
        "company": "BigTech Inc",
        "location": "Remote",
        "description": """
        We're looking for a Staff Engineer to lead our platform team.
        Requirements:
        - 7+ years of software engineering experience
        - Experience with distributed systems
        - Strong Python skills
        """
    }


def test_resume_generator(mock_llm, sample_profile, sample_job):
    """Test resume generation."""
    generator = ResumeGenerator(mock_llm)
    result = generator.generate(sample_profile, sample_job)

    # Verify LLM was called
    mock_llm.generate.assert_called_once()

    # Verify prompt includes key info
    call_args = mock_llm.generate.call_args
    prompt = call_args[0][0]
    assert "Jane Doe" in prompt
    assert "Staff Engineer" in prompt
    assert "BigTech Inc" in prompt


def test_cover_letter_generator(mock_llm, sample_profile, sample_job):
    """Test cover letter generation."""
    generator = CoverLetterGenerator(mock_llm)
    result = generator.generate(sample_profile, sample_job)

    # Verify LLM was called
    mock_llm.generate.assert_called_once()

    # Verify prompt includes key info
    call_args = mock_llm.generate.call_args
    prompt = call_args[0][0]
    assert "Jane Doe" in prompt
    assert "Staff Engineer" in prompt
