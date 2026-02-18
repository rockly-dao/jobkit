"""
Configuration management for JobKit.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class SearchConfig:
    """Job search configuration."""
    keywords: str = "software engineer"
    location: str = "Remote"
    remote_options: list[str] = field(default_factory=lambda: ["remote", "hybrid"])
    experience_level: list[str] = field(default_factory=lambda: ["mid-senior", "director"])
    date_posted: str = "week"  # day, week, month, any
    max_jobs: int = 50


@dataclass
class LLMConfig:
    """LLM configuration for resume/cover letter generation."""
    provider: str = "ollama"  # ollama, anthropic, openai
    model: str = "llama3"  # Model name
    api_key: Optional[str] = None  # For cloud providers
    base_url: str = "http://localhost:11434"  # For Ollama


@dataclass
class Config:
    """Main configuration."""
    data_dir: Path = field(default_factory=lambda: Path.home() / ".jobkit")
    search: SearchConfig = field(default_factory=SearchConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)

    def __post_init__(self):
        self.data_dir = Path(self.data_dir)
        self.jobs_dir = self.data_dir / "jobs"
        self.resumes_dir = self.data_dir / "resumes"
        self.applications_dir = self.data_dir / "applications"
        self.profile_path = self.data_dir / "profile.json"

        # Create directories
        for dir_path in [self.data_dir, self.jobs_dir, self.resumes_dir, self.applications_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def save(self):
        """Save config to file."""
        config_path = self.data_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump({
                "search": {
                    "keywords": self.search.keywords,
                    "location": self.search.location,
                    "remote_options": self.search.remote_options,
                    "experience_level": self.search.experience_level,
                    "date_posted": self.search.date_posted,
                    "max_jobs": self.search.max_jobs,
                },
                "llm": {
                    "provider": self.llm.provider,
                    "model": self.llm.model,
                    "base_url": self.llm.base_url,
                    "api_key": self.llm.api_key,
                }
            }, f, indent=2)

    @classmethod
    def load(cls) -> "Config":
        """Load config from file or create default."""
        config = cls()
        config_path = config.data_dir / "config.json"

        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
                if "search" in data:
                    config.search = SearchConfig(**data["search"])
                if "llm" in data:
                    config.llm = LLMConfig(**data["llm"])

        return config


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global config."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config
