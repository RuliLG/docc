import subprocess
from backend.integrations.ai_provider import AIProvider


class OpenCodeProvider(AIProvider):
    def __init__(self):
        self.opencode_command = "opencode"

    async def analyze_repository(
        self, repository_path: str, question: str, prompt: str
    ) -> str:
        if not self.is_available():
            raise RuntimeError("OpenCode CLI is not available")

        try:
            result = subprocess.run(
                [
                    self.opencode_command,
                    "analyze",
                    "--path",
                    repository_path,
                    "--question",
                    question,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"OpenCode CLI failed: {e.stderr}")

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                [self.opencode_command, "--version"], capture_output=True, text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
