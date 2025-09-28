import json
import logging
import os
from typing import List, Optional, Union

from backend.integrations.ai_provider import AIProvider
from backend.integrations.claude_provider import ClaudeProvider
from backend.integrations.opencode_provider import OpenCodeProvider
from backend.models.script import CodeBlock, LineRange, TextBlock

logger = logging.getLogger(__name__)


class ScriptGenerator:
    def __init__(self):
        # Order providers by preference
        self.providers = [
            ClaudeProvider(),  # Primary: Claude Code CLI
            OpenCodeProvider(),  # Fallback: OpenCode CLI
        ]
        self.ai_provider = self._get_available_provider()
        self.system_prompt = self._load_system_prompt()

    async def generate(
        self, repository_path: str, question: str, ai_provider: Optional[str] = None
    ) -> List[Union[TextBlock, CodeBlock]]:
        prompt = self._build_prompt(repository_path, question)

        # Filter providers based on user preference
        providers_to_try = self._get_providers_to_try(ai_provider)

        # Try all available providers in order
        last_error = None
        for provider in providers_to_try:
            if not provider.is_available():
                continue

            provider_name = provider.__class__.__name__
            logger.info(f"Attempting to use {provider_name}...")

            try:
                ai_response = await provider.analyze_repository(
                    repository_path=repository_path, question=question, prompt=prompt
                )

                # If we got a response, try to parse it
                if ai_response:
                    logger.info(f"Successfully got response from {provider_name}")
                    return self._parse_ai_response(ai_response)
                else:
                    logger.warning(f"{provider_name} returned empty response")

            except Exception as e:
                logger.error(f"{provider_name} failed: {str(e)}")
                last_error = e
                # Continue to next provider

        # If we get here, all providers failed
        if last_error:
            raise RuntimeError(
                f"All AI providers failed. Last error: {str(last_error)}"
            )
        else:
            raise RuntimeError("No AI providers are available")

    def _load_system_prompt(self) -> str:
        """Load the system prompt from the prompts file."""
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "repository_analyzer.md"
        )
        try:
            with open(prompt_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to embedded prompt if file not found
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Fallback system prompt if file is not found."""
        return """You are an expert code analyst. Analyze the repository and answer questions about it.

        Respond with a valid JSON array following this structure:
        [
            {"type": "text", "markdown": "## TL;DR\\nBrief summary"},
            {"type": "code", "file": "/path/to/file", "relevant_lines": [{"from": 10, "to": 15}], "markdown": "Explanation"}
        ]
        """

    def _build_prompt(self, repository_path: str, question: str) -> str:
        return f"""{self.system_prompt}

## Current Task
Repository: {repository_path}
Question: {question}

Analyze this repository and provide a comprehensive answer to the question above."""

    def _parse_ai_response(self, response: str) -> List[Union[TextBlock, CodeBlock]]:
        try:
            parsed_response = json.loads(response)
            script_blocks = []

            for block in parsed_response:
                if block.get("type") == "text":
                    script_blocks.append(TextBlock(**block))
                elif block.get("type") == "code":
                    relevant_lines = []
                    for line_info in block.get("relevant_lines", []):
                        relevant_lines.append(LineRange(**line_info))

                    code_block = CodeBlock(
                        file=block["file"],
                        relevant_lines=relevant_lines,
                        markdown=block["markdown"],
                    )
                    script_blocks.append(code_block)

            return script_blocks
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse script blocks: {e}")

    def _get_available_provider(self) -> AIProvider:
        """Get the first available AI provider."""
        for provider in self.providers:
            if provider.is_available():
                provider_name = provider.__class__.__name__
                logger.info(f"✓ {provider_name} is available")
                return provider
            else:
                provider_name = provider.__class__.__name__
                logger.debug(f"✗ {provider_name} is not available")

        raise RuntimeError(
            "No local CLI agents are available. Please either:\n"
            "1. Install Claude Code CLI (recommended)\n"
            "2. Or install OpenCode CLI"
        )

    def _get_providers_to_try(
        self, preferred_provider: Optional[str]
    ) -> List[AIProvider]:
        """Get list of providers to try based on user preference."""
        if not preferred_provider:
            return self.providers

        # Map provider names to provider instances
        provider_map = {"claude_code": ClaudeProvider, "opencode": OpenCodeProvider}

        if preferred_provider not in provider_map:
            logger.warning(
                f"Unknown provider: {preferred_provider}, using all providers"
            )
            return self.providers

        # Find the specific provider
        for provider in self.providers:
            if isinstance(provider, provider_map[preferred_provider]):
                return [provider]

        # If preferred provider not found, fall back to all
        logger.warning(
            f"Preferred provider {preferred_provider} not available, trying all"
        )
        return self.providers
