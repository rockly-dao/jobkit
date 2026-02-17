"""LLM client for text generation."""

import os
from typing import Optional
import json

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "llama3",
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:11434",
    ):
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url

        # Initialize provider client
        if self.provider == "anthropic":
            if not HAS_ANTHROPIC:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self.client = anthropic.Anthropic(api_key=self.api_key)
        elif self.provider == "openai":
            if not HAS_OPENAI:
                raise ImportError("openai package not installed. Run: pip install openai")
            self.client = openai.OpenAI(api_key=self.api_key)
        elif self.provider == "ollama":
            if not HAS_REQUESTS:
                raise ImportError("requests package not installed. Run: pip install requests")
            self.client = None  # Use requests directly
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 4096) -> str:
        """Generate text from prompt."""
        if self.provider == "anthropic":
            return self._generate_anthropic(prompt, system_prompt, max_tokens)
        elif self.provider == "openai":
            return self._generate_openai(prompt, system_prompt, max_tokens)
        elif self.provider == "ollama":
            return self._generate_ollama(prompt, system_prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _generate_anthropic(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        """Generate using Anthropic Claude."""
        messages = [{"role": "user", "content": prompt}]

        response = self.client.messages.create(
            model=self.model or "claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt or "You are a professional resume and cover letter writer.",
            messages=messages,
        )

        return response.content[0].text

    def _generate_openai(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        """Generate using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model or "gpt-4",
            max_tokens=max_tokens,
            messages=messages,
        )

        return response.choices[0].message.content

    def _generate_ollama(self, prompt: str, system_prompt: str) -> str:
        """Generate using local Ollama."""
        url = f"{self.base_url}/api/generate"

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = requests.post(
            url,
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
            },
            timeout=120,
        )

        if response.status_code != 200:
            raise Exception(f"Ollama error: {response.text}")

        return response.json()["response"]

    @classmethod
    def from_config(cls, config) -> "LLMClient":
        """Create client from config object."""
        return cls(
            provider=config.llm.provider,
            model=config.llm.model,
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
        )
