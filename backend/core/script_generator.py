import json
import os
from typing import List, Union
from backend.models.script import TextBlock, CodeBlock, LineRange
from backend.integrations.ai_provider import AIProvider
from backend.integrations.claude_provider import ClaudeProvider
from backend.integrations.opencode_provider import OpenCodeProvider
from backend.integrations.openai_ai_provider import OpenAIProvider


class ScriptGenerator:
    def __init__(self):
        # Order providers by preference
        self.providers = [
            ClaudeProvider(),      # Primary: Claude Code CLI
            OpenAIProvider(),      # Secondary: OpenAI API
            OpenCodeProvider()     # Fallback: OpenCode CLI
        ]
        self.ai_provider = self._get_available_provider()
        self.system_prompt = self._load_system_prompt()

    async def generate(
        self, repository_path: str, question: str
    ) -> List[Union[TextBlock, CodeBlock]]:
        prompt = self._build_prompt(repository_path, question)

        ai_response = await self.ai_provider.analyze_repository(
            repository_path=repository_path, question=question, prompt=prompt
        )

        return self._parse_ai_response(ai_response)

    def _load_system_prompt(self) -> str:
        """Load the system prompt from the prompts file."""
        prompt_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "prompts", 
            "repository_analyzer.md"
        )
        try:
            with open(prompt_path, 'r') as f:
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
        available_providers = []
        for provider in self.providers:
            if provider.is_available():
                provider_name = provider.__class__.__name__
                print(f"✓ {provider_name} is available")
                return provider
            else:
                provider_name = provider.__class__.__name__
                print(f"✗ {provider_name} is not available")

        raise RuntimeError(
            "No AI providers are available. Please either:\n"
            "1. Install Claude Code CLI (recommended)\n"
            "2. Set OPENAI_API_KEY environment variable\n"
            "3. Install OpenCode CLI"
        )
