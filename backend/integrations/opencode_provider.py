import json
import logging
import subprocess
import time

from backend.integrations.ai_provider import AIProvider

logger = logging.getLogger(__name__)


class OpenCodeProvider(AIProvider):
    def __init__(self):
        self.opencode_command = "opencode"

    async def analyze_repository(
        self, repository_path: str, question: str, prompt: str
    ) -> str:
        if not self.is_available():
            raise RuntimeError("OpenCode CLI is not available")

        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # Use opencode run command with the prompt
                cmd = [
                    self.opencode_command,
                    "run",
                    prompt,  # The prompt includes both system prompt and question
                ]

                logger.info(
                    f"Attempt {attempt + 1}/{max_retries}: Running OpenCode CLI..."
                )

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=repository_path,  # Run from within the repo directory
                    timeout=120,  # 2 minute timeout
                )

                output = result.stdout.strip()

                # Check if we got empty output
                if not output:
                    logger.warning(
                        f"Attempt {attempt + 1}: OpenCode returned empty response"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise RuntimeError(
                            "OpenCode returned empty response after all retries"
                        )

                # Try to find JSON in the output
                # OpenCode might return plain text, so we look for JSON array
                json_start = output.find("[")
                json_end = output.rfind("]")

                if json_start != -1 and json_end != -1 and json_end > json_start:
                    json_str = output[json_start : json_end + 1]
                    try:
                        # Validate it's proper JSON
                        json.loads(json_str)
                        logger.info(
                            f"Successfully extracted JSON from OpenCode response"
                        )
                        return json_str
                    except json.JSONDecodeError:
                        logger.warning(
                            "Failed to parse extracted JSON, returning full output"
                        )
                        return output

                # If no JSON array found, return the entire output
                logger.info("No JSON array found in response, returning full output")
                return output

            except subprocess.CalledProcessError as e:
                error_msg = f"OpenCode CLI failed with exit code {e.returncode}"
                if e.stderr:
                    error_msg += f": {e.stderr}"
                logger.error(f"Attempt {attempt + 1}: {error_msg}")

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise RuntimeError(error_msg)

            except subprocess.TimeoutExpired:
                logger.error(f"Attempt {attempt + 1}: OpenCode CLI timed out")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise RuntimeError("OpenCode CLI timed out after all retries")

            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Unexpected error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise RuntimeError(f"Error running OpenCode CLI: {str(e)}")

    def is_available(self) -> bool:
        try:
            # Check if opencode command exists
            result = subprocess.run(
                [self.opencode_command, "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
