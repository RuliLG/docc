import subprocess
import os
import json
import time
import logging
from backend.integrations.ai_provider import AIProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(AIProvider):
    def __init__(self):
        self.claude_command = "claude"

    async def analyze_repository(
        self, repository_path: str, question: str, prompt: str
    ) -> str:
        if not self.is_available():
            raise RuntimeError("Claude Code CLI is not available")

        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # Use Claude Code CLI with proper syntax
                # Run from within the repository directory for better context
                cmd = [
                    self.claude_command,
                    "--print",  # Print response and exit
                    "--output-format", "text",  # Use text format
                    prompt  # The prompt includes both system prompt and question
                ]

                logger.info(f"Attempt {attempt + 1}/{max_retries}: Running Claude CLI...")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=repository_path,  # Run from within the repo directory
                    timeout=120  # 2 minute timeout
                )

                # Claude CLI returns plain text by default
                # We need to extract any JSON from the response
                output = result.stdout.strip()

                # Check if we got empty output
                if not output:
                    logger.warning(f"Attempt {attempt + 1}: Claude returned empty response")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise RuntimeError("Claude returned empty response after all retries")

                # Try to find JSON in the output
                # Look for array brackets that indicate our expected format
                json_start = output.find('[')
                json_end = output.rfind(']')

                if json_start != -1 and json_end != -1 and json_end > json_start:
                    json_str = output[json_start:json_end + 1]
                    try:
                        # Validate it's proper JSON
                        json.loads(json_str)
                        logger.info(f"Successfully extracted JSON from Claude response")
                        return json_str
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse extracted JSON, returning full output")
                        # If JSON is malformed, return the whole output
                        return output

                # If no JSON array found, return the entire output
                # The script generator will handle the parsing error
                logger.info("No JSON array found in response, returning full output")
                return output

            except subprocess.TimeoutExpired:
                logger.error(f"Attempt {attempt + 1}: Claude CLI timed out")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise RuntimeError("Claude CLI timed out after all retries")

            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Unexpected error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise RuntimeError(f"Error running Claude Code CLI: {str(e)}")

    def is_available(self) -> bool:
        try:
            # Check if claude command exists
            result = subprocess.run(
                [self.claude_command, "--version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
