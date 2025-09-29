from typing import List, Optional, Union

from pydantic import BaseModel, Field


class LineRange(BaseModel):
    """Represents a range of lines in a code file."""

    from_line: Optional[int] = Field(
        None, alias="from", description="Starting line number (1-based)", ge=1
    )
    to_line: Optional[int] = Field(
        None, alias="to", description="Ending line number (1-based)", ge=1
    )
    line: Optional[int] = Field(
        None,
        description="Single line number (1-based) when highlighting just one line",
        ge=1,
    )

    model_config = {"populate_by_name": True}


class TextBlock(BaseModel):
    """A text block containing markdown content for narration."""

    type: str = Field(default="text", description="Block type identifier")
    markdown: str = Field(description="Markdown content to be narrated", min_length=1)


class CodeBlock(BaseModel):
    """A code block containing file content with highlighted lines."""

    type: str = Field(default="code", description="Block type identifier")
    file: str = Field(description="Absolute path to the source code file", min_length=1)
    relevant_lines: List[LineRange] = Field(
        description="List of line ranges to highlight in the code"
    )
    markdown: str = Field(
        description="Markdown explanation of the code block", min_length=1
    )


class ScriptRequest(BaseModel):
    """Request to generate a script for explaining repository code."""

    repository_path: str = Field(
        description="Absolute path to the repository to analyze", min_length=1
    )
    question: str = Field(
        description="Question about the repository to answer", min_length=1
    )
    ai_provider: Optional[str] = Field(
        None, description="AI provider to use for code analysis (claude_code, opencode)"
    )
    tts_provider: Optional[str] = Field(
        None,
        description="Text-to-speech provider for audio generation (elevenlabs, openai)",
    )


class ScriptResponse(BaseModel):
    """Response containing the generated script and audio files."""

    script: List[Union[TextBlock, CodeBlock]] = Field(
        description="Ordered list of text and code blocks forming the explanation"
    )
    audio_files: Optional[List[str]] = Field(
        None, description="URLs to generated audio files for each script block"
    )
