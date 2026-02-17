"""Tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import json

from jobkit.config import Config, SearchConfig, LLMConfig, load_config, save_config


def test_default_config():
    """Test that default config has sensible values."""
    config = Config()

    assert config.search.keywords == ""
    assert config.search.location == "Remote"
    assert config.llm.provider == "ollama"
    assert config.llm.model == "llama3"


def test_config_save_load():
    """Test saving and loading config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        config = Config(
            data_dir=data_dir,
            search=SearchConfig(keywords="engineer", location="NYC"),
            llm=LLMConfig(provider="anthropic", model="claude-3-sonnet")
        )

        save_config(config)

        # Verify file was created
        config_file = data_dir / "config.json"
        assert config_file.exists()

        # Load and verify
        loaded = load_config(data_dir)
        assert loaded.search.keywords == "engineer"
        assert loaded.search.location == "NYC"
        assert loaded.llm.provider == "anthropic"
