import os
import fnmatch
from pathlib import Path
from typing import List, Dict


def analyze_repository_structure(repo_path: str, max_depth: int = 3) -> str:
    """Analyze repository structure and return a summary."""

    ignore_patterns = [
        "*.pyc",
        "__pycache__",
        ".git",
        "node_modules",
        "venv",
        "env",
        ".venv",
        "dist",
        "build",
        "*.egg-info",
    ]

    structure = []
    file_count = {"python": 0, "javascript": 0, "typescript": 0, "other": 0}

    def should_ignore(path: str) -> bool:
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
        return False

    def get_file_type(filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext in [".py"]:
            return "python"
        elif ext in [".js", ".jsx"]:
            return "javascript"
        elif ext in [".ts", ".tsx"]:
            return "typescript"
        else:
            return "other"

    def walk_directory(path: str, depth: int = 0, prefix: str = ""):
        if depth > max_depth:
            return

        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            return

        for item in items:
            item_path = os.path.join(path, item)

            if should_ignore(item_path):
                continue

            if os.path.isdir(item_path):
                structure.append(f"{prefix}📁 {item}/")
                walk_directory(item_path, depth + 1, prefix + "  ")
            else:
                file_type = get_file_type(item)
                file_count[file_type] += 1

                if file_type == "python":
                    structure.append(f"{prefix}🐍 {item}")
                elif file_type in ["javascript", "typescript"]:
                    structure.append(f"{prefix}⚡ {item}")
                else:
                    structure.append(f"{prefix}📄 {item}")

    walk_directory(repo_path)

    summary = f"""
Repository Structure Analysis:
Path: {repo_path}

File Summary:
- Python files: {file_count['python']}
- JavaScript/TypeScript files: {file_count['javascript'] + file_count['typescript']}
- Other files: {file_count['other']}

Directory Structure:
{''.join(structure[:50])}  # Truncated for brevity
{'... (truncated)' if len(structure) > 50 else ''}
"""

    return summary


def read_file_with_line_numbers(
    file_path: str, relevant_lines: List[Dict] = None
) -> str:
    """Read file content with line numbers, highlighting relevant lines."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        relevant_set = set()
        if relevant_lines:
            for line_info in relevant_lines:
                if "from" in line_info and "to" in line_info:
                    relevant_set.update(range(line_info["from"], line_info["to"] + 1))
                elif "line" in line_info:
                    relevant_set.add(line_info["line"])

        result = []
        for i, line in enumerate(lines, 1):
            marker = ">>> " if i in relevant_set else "    "
            result.append(f"{marker}{i:4d}: {line.rstrip()}")

        return "\n".join(result)
    except Exception as e:
        return f"Error reading file: {str(e)}"
