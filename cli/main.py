#!/usr/bin/env python3
import click
import json
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from backend.core.script_generator import ScriptGenerator
from backend.core.tts_manager import TTSManager


@click.command()
@click.argument(
    "repository_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.argument("question")
@click.option(
    "--output",
    "-o",
    help="Output directory path for the generated session (defaults to auto-generated)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--no-browser", is_flag=True, help="Do not open browser automatically")
def docc(
    repository_path: str, question: str, output: str, verbose: bool, no_browser: bool
):
    """Generate documentation script for a repository question.

    REPOSITORY_PATH: Path to the repository to analyze
    QUESTION: Question about the repository
    """
    if verbose:
        click.echo(f"Analyzing repository: {repository_path}")
        click.echo(f"Question: {question}")

    try:
        repository_path = os.path.abspath(repository_path)

        if not os.path.isdir(repository_path):
            click.echo(f"Error: {repository_path} is not a valid directory", err=True)
            sys.exit(1)

        # Generate session ID and create session folder
        if output:
            session_folder = Path(output)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            repo_name = Path(repository_path).name
            session_id = f"{repo_name}_{timestamp}"
            session_folder = Path.cwd() / "sessions" / session_id

        session_folder.mkdir(parents=True, exist_ok=True)

        if verbose:
            click.echo(f"Session folder: {session_folder.absolute()}")
            click.echo("Initializing script generator...")

        script_generator = ScriptGenerator()

        if verbose:
            click.echo("Generating script...")

        async def generate_script_with_audio():
            # Generate script
            script = await script_generator.generate(repository_path, question)

            # Generate audio for all text blocks in the session folder
            if verbose:
                click.echo("Generating audio files...")

            audio_folder = session_folder / "audio"
            tts_manager = TTSManager(cache_dir=str(audio_folder))

            script_blocks = []
            for i, block in enumerate(script):
                block_dict = block.dict()

                # Generate audio for text content
                if hasattr(block, "markdown") and block.markdown:
                    try:
                        audio_filename = f"block_{i}.mp3"
                        audio_bytes = await tts_manager.generate_or_get_cached_audio(
                            block.markdown
                        )

                        # Save audio with predictable filename
                        audio_path = audio_folder / audio_filename
                        with open(audio_path, "wb") as f:
                            f.write(audio_bytes)

                        block_dict["audio_file"] = audio_filename

                        if verbose:
                            click.echo(f"Generated audio for block {i}")

                    except Exception as e:
                        if verbose:
                            click.echo(
                                f"Warning: Could not generate audio for block {i}: {e}"
                            )
                        block_dict["audio_file"] = None

                script_blocks.append(block_dict)

            return script_blocks

        import asyncio

        script_blocks = asyncio.run(generate_script_with_audio())

        script_data = {
            "repository_path": repository_path,
            "question": question,
            "script": script_blocks,
        }

        # Save script.json in the session folder
        script_file = session_folder / "script.json"
        with open(script_file, "w", encoding="utf-8") as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)

        click.echo(f"Session generated successfully: {session_folder.absolute()}")

        if verbose:
            click.echo(f"Generated {len(script_blocks)} script blocks")

        # Open browser with the session
        if not no_browser:
            frontend_url = f"http://localhost:3000?session={session_folder.name}"
            if verbose:
                click.echo(f"Opening browser: {frontend_url}")
            webbrowser.open(frontend_url)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        if verbose:
            import traceback

            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


if __name__ == "__main__":
    docc()
