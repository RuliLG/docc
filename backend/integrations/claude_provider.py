import subprocess
import os
import json
from backend.integrations.ai_provider import AIProvider


class ClaudeProvider(AIProvider):
    def __init__(self):
        self.claude_command = "claude"

    async def analyze_repository(
        self, repository_path: str, question: str, prompt: str
    ) -> str:
        if not self.is_available():
            raise RuntimeError("Claude Code CLI is not available")

        try:
            # Use Claude Code CLI with proper syntax
            # Run from within the repository directory for better context
            cmd = [
                self.claude_command,
                "-p", prompt,  # The prompt includes both system prompt and question
                "--no-stream"  # Don't stream output, get it all at once
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=repository_path  # Run from within the repo directory
            )
            
            # Claude CLI returns plain text by default
            # We need to extract any JSON from the response
            output = result.stdout.strip()
            
            # Try to find JSON in the output
            # Look for array brackets that indicate our expected format
            json_start = output.find('[')
            json_end = output.rfind(']')
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_str = output[json_start:json_end + 1]
                try:
                    # Validate it's proper JSON
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError:
                    # If JSON is malformed, return the whole output
                    return output
            
            # If no JSON array found, return the entire output
            # The script generator will handle the parsing error
            return output
                
        except subprocess.CalledProcessError as e:
            # Provide helpful error messages
            error_msg = f"Claude Code CLI failed with exit code {e.returncode}"
            if e.stderr:
                error_msg += f": {e.stderr}"
            raise RuntimeError(error_msg)
        except Exception as e:
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
