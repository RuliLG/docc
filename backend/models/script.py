from typing import List, Optional, Union
from pydantic import BaseModel, Field


class LineRange(BaseModel):
    from_line: Optional[int] = Field(None, alias='from')
    to_line: Optional[int] = Field(None, alias='to')
    line: Optional[int] = None
    
    model_config = {'populate_by_name': True}


class TextBlock(BaseModel):
    type: str = "text"
    markdown: str


class CodeBlock(BaseModel):
    type: str = "code"
    file: str
    relevant_lines: List[LineRange]
    markdown: str


class ScriptRequest(BaseModel):
    repository_path: str
    question: str


class ScriptResponse(BaseModel):
    script: List[Union[TextBlock, CodeBlock]]
    audio_files: Optional[List[str]] = None
