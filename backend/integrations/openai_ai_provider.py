import os
import json
from typing import Optional
import openai
from backend.integrations.ai_provider import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
        # Load the system prompt
        self.system_prompt = self._load_system_prompt()

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
            return """You are an expert code analyst. Analyze repositories and answer questions.
            Respond with a valid JSON array: [{"type": "text", "markdown": "content"}, {"type": "code", "file": "path", "relevant_lines": [...], "markdown": "explanation"}]"""

    async def analyze_repository(
        self, repository_path: str, question: str, prompt: str
    ) -> str:
        if not self.is_available():
            raise RuntimeError("OpenAI API key not available")

        try:
            # Read repository files to provide context
            # In a real implementation, we'd need a smarter way to select relevant files
            repo_context = self._get_repository_context(repository_path)
            
            # Prepare the messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"""Repository path: {repository_path}
Question: {question}

Repository structure and key files:
{repo_context}

Please analyze this repository and answer the question. Remember to respond with a valid JSON array as specified in the system prompt."""}
            ]

            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",  # or gpt-3.5-turbo for faster/cheaper
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent JSON output
                max_tokens=4000
            )

            # Extract the response
            content = response.choices[0].message.content
            
            # Try to extract JSON from the response
            json_start = content.find('[')
            json_end = content.rfind(']')
            
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end + 1]
                try:
                    # Validate it's proper JSON
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError:
                    pass
            
            # If no valid JSON found, return the whole content
            return content

        except Exception as e:
            raise RuntimeError(f"OpenAI API failed: {str(e)}")

    def _get_repository_context(self, repository_path: str, max_files: int = 20) -> str:
        """Get a summary of the repository structure and key files."""
        context_parts = []
        file_count = 0
        
        # Walk through the repository
        for root, dirs, files in os.walk(repository_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'dist', 'build']]
            
            rel_root = os.path.relpath(root, repository_path)
            if rel_root == '.':
                rel_root = ''
            
            for file in files:
                if file_count >= max_files:
                    break
                    
                # Skip hidden files and non-code files
                if file.startswith('.') or file.endswith(('.pyc', '.pyo', '.so', '.dylib', '.dll')):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.join(rel_root, file) if rel_root else file
                
                # For key files, include some content
                if file in ['README.md', 'setup.py', 'package.json', 'requirements.txt', 'Cargo.toml']:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read(500)  # First 500 chars
                            context_parts.append(f"\n--- {rel_path} ---\n{content}...")
                            file_count += 1
                    except:
                        pass
                else:
                    context_parts.append(f"- {rel_path}")
                    file_count += 1
        
        return "\n".join(context_parts)

    def is_available(self) -> bool:
        return self.api_key is not None